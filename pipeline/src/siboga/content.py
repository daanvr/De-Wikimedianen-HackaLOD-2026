"""Reads the content repo (chapters, records, pages, plugins and i18n) and converts Obsidian markdown to plain markdown."""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import re
import unicodedata

from loguru import logger
import yaml

from siboga.models import ContentItem, ContentType, ItemKind, Report

_CONTENT_TYPES = {content_type.value for content_type in ContentType}
_EXTENSION = re.compile(r"\.[A-Za-z0-9]{1,5}$")
_FALSE_VALUES = {"false", "no", "0", ""}
_FRONTMATTER = re.compile(
    r"\A﻿?---[ \t]*\n(.*?)^(?:---|\.\.\.)[ \t]*(?:\n|\Z)",
    re.DOTALL | re.MULTILINE
)
_I18N_TYPE = "i18n"
_KINDS = {
    "chapter": ItemKind.CHAPTER,
    "page": ItemKind.PAGE,
    "plugin": ItemKind.PLUGIN,
    "record": ItemKind.RECORD
}
_LINK_TITLE = re.compile(r"\s+(?:\"[^\"]*\"|'[^']*')$")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_TRUE_VALUES = {"true", "yes", "1"}
# A single scan over the text. Code blocks and inline code are matched first,
# so links and comments inside them stay untouched.
_TOKEN = re.compile(
    r"(?P<fence>^[ \t]*(?P<fence_mark>`{3,}|~{3,})[^`\n]*\n.*?(?:^[ \t]*(?P=fence_mark)[ \t]*$|\Z))"
    r"|(?P<code>(?<!`)(?P<ticks>`+)(?!`)[^\n]*?(?<!`)(?P=ticks)(?!`))"
    r"|(?P<comment>%%.*?%%)"
    r"|(?P<wikilink>(?P<embed>!?)\[\[(?P<inner>[^\[\]\n]+?)\]\])"
    r"|(?P<mdlink>(?P<image>!?)\[(?P<label>[^\[\]\n]*)\]\((?P<target>(?:[^()\n]|\([^()\n]*\))*)\))",
    re.DOTALL | re.MULTILINE
)
_WIKILINK = re.compile(r"\[\[([^\[\]\n]+?)\]\]")

@dataclass
class ConvertedBody:
    attachments: dict[str, Path]
    links: list[str]
    markdown: str

@dataclass
class LinkIndex:
    attachments: dict[str, Path]
    refs: dict[str, str]

@dataclass
class _BodyConverter:
    """Converts one body; collects attachments and links along the way."""
    index: LinkIndex
    item: ContentItem
    report: Report
    attachments: dict[str, Path] = field(default_factory = dict)
    links: list[str] = field(default_factory = list)

    def _attachment(self, path: Path) -> str:
        name = slugify(path.stem) + path.suffix.lower()
        existing = self.attachments.setdefault(name, path)
        if existing != path:
            self.report.warn(f"two attachments get the same name {name}: {existing.name} and {path.name}", self.item.path)
        return f"media/{name}"

    def _link(self, ref: str) -> None:
        if ref not in self.links:
            self.links.append(ref)

    def _markdown_link(self, match: re.Match) -> str:
        original = match.group(0)
        target = _strip_link_title(match.group("target"))
        if not target or _SCHEME.match(target) or target.startswith(("#", "/")):
            return original
        label = match.group("label")
        page = unquote(target.split("#", 1)[0])
        if page.lower().endswith(".md"):
            ref = resolve_link(page, self.index)
            if ref:
                self._link(ref)
                return f"[{label}](/{ref})"
            self.report.warn(f"link to unknown page ({target}), becomes plain text", self.item.path)
            return label
        attachment = self.index.attachments.get(_key(_last_part(page)))
        if attachment:
            return f"{match.group('image')}[{label}]({self._attachment(attachment)})"
        return original

    def _plugin_link(
        self,
        ref: str,
        target: str,
        alias: str
    ) -> str:
        """[[IIIF#argument]] becomes a link to the plugin, with everything after the # as its argument."""
        self._link(ref)
        argument = target.partition("#")[2].strip()
        href = f"/{ref}?argument={quote(argument, safe = '')}" if argument else f"/{ref}"
        return f"[{alias or _default_label(target.partition('#')[0])}]({href})"

    def _wikilink(self, match: re.Match) -> str:
        target, _, alias = match.group("inner").replace("\\|", "|").partition("|")
        target = target.strip()
        alias = alias.strip()
        page = target.split("#", 1)[0].strip()
        name = _last_part(page)
        ref = resolve_link(target, self.index)
        if ref and ref.startswith(f"{ItemKind.PLUGIN.value}/"):
            return self._plugin_link(ref, target, alias)
        attachment = None if ref else self.index.attachments.get(_key(name))
        if match.group("embed"):
            if attachment:
                return f"![]({self._attachment(attachment)})"
            if not ref and _EXTENSION.search(name):
                self.report.warn(f"attachment does not exist: ![[{target}]], left out", self.item.path)
                return ""
        label = alias or _default_label(target)
        if ref:
            self._link(ref)
            return f"[{label}](/{ref})"
        if attachment:
            return f"[{label}]({self._attachment(attachment)})"
        if page:
            self.report.warn(f"link to unknown page [[{target}]], becomes plain text", self.item.path)
        return label

    def replace(self, match: re.Match) -> str:
        if match.group("comment"):
            return ""
        if match.group("wikilink"):
            return self._wikilink(match)
        if match.group("mdlink"):
            return self._markdown_link(match)
        return match.group(0)

def build_link_index(items: list[ContentItem], content_path: Path) -> LinkIndex:
    attachments = {}
    for path in _walk_files(content_path):
        if path.suffix.lower() != ".md":
            attachments.setdefault(_key(path.name), path.resolve())
    refs = {}
    for item in items:
        refs.setdefault(_key(item.title), item.ref)
    return LinkIndex(attachments = attachments, refs = refs)

def chapter_location(
    item: ContentItem,
    index: LinkIndex,
    report: Report
) -> str | None:
    target = _location_target(item.frontmatter.get("location"))
    if not target:
        report.warn("chapter without location (required)", item.path)
        return None
    ref = resolve_link(target, index)
    if ref is None:
        report.warn(f"location refers to unknown page: {target}", item.path)
        return None
    if not ref.startswith(f"{ItemKind.RECORD.value}/"):
        report.warn(f"location does not refer to a record: {target}", item.path)
        return None
    return ref

def chapter_number(item: ContentItem, report: Report) -> int | None:
    value = item.frontmatter.get("chapter")
    if value is None or value == "":
        report.warn("chapter without number", item.path)
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value.strip()):
        return int(value.strip())
    report.warn(f"invalid number: {value!r}", item.path)
    return None

def content_type(item: ContentItem, report: Report) -> str | None:
    value = item.frontmatter.get("contenttype")
    text = "" if value is None else str(value).strip()
    if not text:
        report.warn("no content type", item.path)
        return None
    if text not in _CONTENT_TYPES:
        report.warn(f"unknown content type: {text}", item.path)
    return text

def convert_body(
    item: ContentItem,
    index: LinkIndex,
    report: Report
) -> ConvertedBody:
    converter = _BodyConverter(index = index, item = item, report = report)
    markdown = _TOKEN.sub(converter.replace, item.body)
    return ConvertedBody(
        attachments = converter.attachments,
        links = converter.links,
        markdown = markdown
    )

def description(item: ContentItem) -> str | None:
    value = item.frontmatter.get("description_nl")
    if value is None:
        return None
    return str(value).strip() or None

def page_title(item: ContentItem, report: Report) -> str:
    """A page's title comes from `title`; without a title, the file name is used."""
    value = item.frontmatter.get("title")
    if value is None or not str(value).strip():
        report.warn("page without title, the filename becomes the title", item.path)
        return item.title
    return str(value).strip()

def plugin_title(item: ContentItem) -> str:
    """A plugin's title comes from `title`; without a title, the file name is used."""
    value = item.frontmatter.get("title")
    if value is None or not str(value).strip():
        return item.title
    return str(value).strip()

def read_content(content_path: Path, report: Report) -> list[ContentItem]:
    items = []
    for path in _walk_files(content_path):
        if path.suffix.lower() == ".md":
            item = _read_item(path, content_path, report)
            if item:
                items.append(item)
    _deduplicate_ids(items, report)
    return sorted(items, key = lambda item: (item.kind.value, item.id))

def read_messages(content_path: Path, report: Report) -> dict[str, str]:
    """All messages from files with `type: i18n`: every key in the frontmatter except `type`."""
    messages = {}
    for path in _walk_files(content_path):
        if path.suffix.lower() != ".md":
            continue
        parsed = _parse(path, content_path)
        if parsed is None or str(parsed[0].get("type", "")).strip().lower() != _I18N_TYPE:
            continue
        frontmatter, _, relative = parsed
        for key, value in frontmatter.items():
            if key == "type":
                continue
            if value is None or not str(value).strip():
                report.warn(f"empty message: {key}", relative)
                continue
            if key in messages:
                report.warn(f"message {key} already exists, will be overwritten", relative)
            messages[str(key)] = str(value).strip()
    return messages

def record_uri(item: ContentItem, report: Report) -> str | None:
    value = item.frontmatter.get("uri")
    if value is None or value == "":
        report.warn("record without uri", item.path)
        return None
    if not isinstance(value, str) or not _is_http_url(value.strip()):
        report.warn(f"uri is not an http(s) URL: {value!r}", item.path)
        return None
    return value.strip()

def resolve_link(target: str, index: LinkIndex) -> str | None:
    name = _last_part(target.split("#", 1)[0])
    if name.lower().endswith(".md"):
        name = name[:-3]
    return index.refs.get(_key(name))

def show_in_explore(item: ContentItem, report: Report) -> bool:
    """`show_in_explore` as a boolean; YAML gives a bool, but editors also write "true" in quotes."""
    value = item.frontmatter.get("show_in_explore")
    if isinstance(value, bool):
        return value
    text = "" if value is None else str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text not in _FALSE_VALUES:
        report.warn(f"invalid show_in_explore: {value!r}, becomes false", item.path)
    return False

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "item"

def _deduplicate_ids(items: list[ContentItem], report: Report) -> None:
    """Gives duplicate ids within one kind a suffix -2, -3, ... (in path order)."""
    taken = {(item.kind, item.id) for item in items}
    seen = set()
    for item in sorted(items, key = lambda item: item.path.as_posix()):
        if (item.kind, item.id) in seen:
            number = 2
            while (item.kind, f"{item.id}-{number}") in taken:
                number += 1
            new_id = f"{item.id}-{number}"
            report.warn(f"id {item.id} already exists for {item.kind.value}, becomes {new_id}", item.path)
            item.id = new_id
            taken.add((item.kind, new_id))
        seen.add((item.kind, item.id))

def _default_label(target: str) -> str:
    page, _, heading = target.partition("#")
    name = _last_part(page)
    if name.lower().endswith(".md"):
        name = name[:-3]
    return name or heading.lstrip("^").strip()

def _is_http_url(text: str) -> bool:
    if not text or any(char.isspace() for char in text):
        return False
    parsed = urlparse(text)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def _key(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip()).lower()

def _last_part(path: str) -> str:
    return path.rsplit("/", 1)[-1].strip()

def _location_target(value: object) -> str | None:
    # Without quotes, YAML turns [[X]] into a nested list.
    while isinstance(value, list):
        value = value[0] if value else None
    if not isinstance(value, str):
        return None
    match = _WIKILINK.search(value)
    text = match.group(1) if match else value
    return text.replace("\\|", "|").partition("|")[0].strip() or None

def _parse(
    path: Path,
    content_path: Path,
    report: Report | None = None
) -> tuple[dict, str, Path] | None:
    """Frontmatter, body and relative path of a markdown file. Without a report, no warnings."""
    relative = path.relative_to(content_path)
    try:
        text = path.read_text(encoding = "utf-8")
    except (OSError, UnicodeDecodeError) as error:
        if report:
            report.warn(f"file can't be read, skipped ({error})", relative)
        return None
    match = _FRONTMATTER.match(text)
    if not match:
        logger.debug(f"{relative}: no frontmatter, skipped")
        return None
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        if report:
            report.warn(f"invalid YAML in frontmatter, skipped ({' '.join(str(error).split())})", relative)
        return None
    if not isinstance(frontmatter, dict):
        return None
    return frontmatter, text[match.end():], relative

def _read_item(
    path: Path,
    content_path: Path,
    report: Report
) -> ContentItem | None:
    parsed = _parse(path, content_path, report)
    if parsed is None:
        return None
    frontmatter, body, relative = parsed
    if frontmatter.get("type") in (None, ""):
        logger.debug(f"{relative}: no type, skipped")
        return None
    type_name = str(frontmatter["type"]).strip().lower()
    if type_name == _I18N_TYPE:
        return None
    kind = _KINDS.get(type_name)
    if kind is None:
        report.warn(f"unknown type: {frontmatter['type']!r}, skipped", relative)
        return None
    title = unicodedata.normalize("NFC", path.stem)
    item_id = slugify(title)
    if kind == ItemKind.PLUGIN:
        # The id names the plugin in the frontend, so it comes from the frontmatter.
        if frontmatter.get("id") in (None, ""):
            report.warn(f"plugin without id, becomes {item_id}", relative)
        else:
            item_id = slugify(str(frontmatter["id"]))
    return ContentItem(
        body = body,
        frontmatter = frontmatter,
        id = item_id,
        kind = kind,
        path = relative,
        title = title
    )

def _strip_link_title(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and ">" in target:
        return target[1:target.index(">")].strip()
    return _LINK_TITLE.sub("", target)

def _walk_files(content_path: Path) -> list[Path]:
    """All files under content_path, excluding hidden directories and files, sorted."""
    files = []
    for directory, directories, filenames in content_path.walk():
        directories[:] = [name for name in directories if not name.startswith(".")]
        files.extend(directory / name for name in filenames if not name.startswith("."))
    return sorted(files)
