"""Reads the content repo (chapters, records, pages, plugins and i18n) and converts Obsidian markdown to plain markdown."""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import json
import re
import unicodedata

from loguru import logger
import yaml

from siboga.models import ContentItem, ContentType, Coordinates, ItemKind, Marker, Report

_BLOCK_CLOSE = re.compile(r"^:::[ \t]*$")
# ::: gallery and :::details Summary; the frontend makes a gallery and a collapsible block of them.
_BLOCK_OPEN = re.compile(r"^:::[ \t]*(gallery[ \t]*$|details\b)")
# A line entirely in italics directly below an image is its caption (see frontend/src/services/markdown.js).
_CAPTION_LINE = re.compile(r"^\*(?!\*).+\*[ \t]*$")
_CONTENT_TYPES = {content_type.value for content_type in ContentType}
_EXTENSION = re.compile(r"\.[A-Za-z0-9]{1,5}$")
_FALSE_VALUES = {"false", "no", "0", ""}
_FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_FRONTMATTER = re.compile(
    r"\A﻿?---[ \t]*\n(.*?)^(?:---|\.\.\.)[ \t]*(?:\n|\Z)",
    re.DOTALL | re.MULTILINE
)
_I18N_TYPE = "i18n"
# ![[icon.svg|14]] or ![[map.png|300x200]]: the width (and height) in Obsidian, kept as ![|14](...) for the frontend.
_IMAGE_SIZE = re.compile(r"[0-9]+(?:x[0-9]+)?")
_IMAGE = re.compile(r"!\[[^\]\n]*\]\((?P<src>(?:[^()\s]|\([^()\s]*\))+)")
_IMAGE_LINE = re.compile(r"^!\[[^\]\n]*\]\((?:[^()\n]|\([^()\n]*\))*\)[ \t]*$")
_KINDS = {
    "chapter": ItemKind.CHAPTER,
    "page": ItemKind.PAGE,
    "plugin": ItemKind.PLUGIN,
    "record": ItemKind.RECORD
}
_LINK_TITLE = re.compile(r"\s+(?:\"[^\"]*\"|'[^']*')$")
# The map shows the whole world, so any place on Earth will do; a swapped pair usually falls outside it.
_MAP_BOUNDS = {
    "lat": (-90.0, 90.0),
    "lon": (-180.0, 180.0)
}
_RECORD_LINK = re.compile(r"\]\(/records/(?P<id>[^()\s/?#]+)\)")
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

@dataclass
class BodyImage:
    """An image in a converted body, and the id of the record its caption links to, if any."""
    record_id: str | None
    src: str

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
                size = f"|{alias}" if _IMAGE_SIZE.fullmatch(alias) else ""
                return f"![{size}]({self._attachment(attachment)})"
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

def body_images(markdown: str) -> list[BodyImage]:
    """All images in a converted body, outside code blocks.

    Only an image alone on its line, with a caption directly below it, can have a record:
    the frontend shows the credit and license of the first record that caption links to.
    """
    images = []
    lines = markdown.splitlines()
    fence = None
    for number, line in enumerate(lines):
        match = _FENCE_LINE.match(line)
        if match:
            mark = match.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        caption = lines[number + 1] if number + 1 < len(lines) else ""
        record = None
        if _IMAGE_LINE.match(line.strip()) and _CAPTION_LINE.match(caption.strip()):
            record = _RECORD_LINK.search(caption)
        for image in _IMAGE.finditer(line):
            images.append(BodyImage(record_id = record.group("id") if record else None, src = image.group("src")))
    return images

def build_link_index(items: list[ContentItem], content_path: Path) -> LinkIndex:
    attachments = {}
    for path in _walk_files(content_path):
        if path.suffix.lower() != ".md":
            attachments.setdefault(_key(path.name), path.resolve())
    refs = {}
    for item in items:
        refs.setdefault(_key(item.title), item.ref)
    return LinkIndex(attachments = attachments, refs = refs)

def chapter_markers(
    item: ContentItem,
    index: LinkIndex,
    report: Report
) -> list[Marker]:
    """The points in the GeoJSON file of `geojson`. `name` or `label` is the text, `link` the page a click opens."""
    value = item.frontmatter.get("geojson")
    if value is None or value == "":
        return []
    name = _frontmatter_link(value)
    path = index.attachments.get(_key(_last_part(name)))
    if path is None:
        report.warn(f"geojson file does not exist: {name!r}", item.path)
        return []
    try:
        data = json.loads(path.read_text(encoding = "utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        report.warn(f"geojson file can't be read ({error})", item.path)
        return []
    markers = []
    ignored = set()
    for feature in _geojson_features(data):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            ignored.add(str(geometry.get("type")))
            continue
        marker = _marker(feature, index, item, report)
        if marker is not None:
            markers.append(marker)
    if ignored:
        report.warn(f"geojson: only points become markers, ignored {', '.join(sorted(ignored))}", item.path)
    if not markers:
        report.warn(f"geojson file {name!r} has no points", item.path)
    return markers

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
    _check_blocks(markdown, item, report)
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

def is_term(item: ContentItem) -> bool:
    return str(item.frontmatter.get("contenttype") or "").strip() == ContentType.TERM.value

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
    """For a term the uri is optional: a link to read more, which the pipeline does not fetch."""
    value = item.frontmatter.get("uri")
    if value is None or value == "":
        if not is_term(item):
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

def _check_blocks(
    markdown: str,
    item: ContentItem,
    report: Report
) -> None:
    """Warns about a `::: gallery` or `:::details` without its closing `:::`; the frontend then shows it as plain text.

    A details block can hold a gallery, but a gallery can hold no other block.
    """
    fence = None
    open_blocks = []
    for line in markdown.splitlines():
        match = _FENCE_LINE.match(line)
        if match:
            mark = match.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        block = _BLOCK_OPEN.match(line)
        if block:
            name = "gallery" if block.group(1).startswith("gallery") else "details"
            if "gallery" in open_blocks:
                report.warn(f"::: {name} inside a gallery that was not closed with :::", item.path)
            open_blocks.append(name)
        elif _BLOCK_CLOSE.match(line) and open_blocks:
            open_blocks.pop()
    for name in open_blocks:
        report.warn(f"::: {name} without a closing :::, shown as plain text", item.path)

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

def _frontmatter_link(value: object) -> str:
    """The file name in "[[name|alias]]"; unquoted in YAML that is a nested list."""
    while isinstance(value, list) and value:
        value = value[0]
    text = str(value).strip()
    if text.startswith("[[") and text.endswith("]]"):
        text = text[2:-2]
    return text.split("|", 1)[0].split("#", 1)[0].strip()

def _geojson_features(data: object) -> list[dict]:
    """The features of a FeatureCollection, a single Feature or a bare geometry."""
    if not isinstance(data, dict):
        return []
    if data.get("type") == "FeatureCollection":
        return [feature for feature in data.get("features") or [] if isinstance(feature, dict)]
    if data.get("type") == "Feature":
        return [data]
    return [{"geometry": data, "properties": {}}]

def _is_http_url(text: str) -> bool:
    if not text or any(char.isspace() for char in text):
        return False
    parsed = urlparse(text)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def _key(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip()).lower()

def _last_part(path: str) -> str:
    return path.rsplit("/", 1)[-1].strip()

def _marker(
    feature: dict,
    index: LinkIndex,
    item: ContentItem,
    report: Report
) -> Marker | None:
    coordinates = feature["geometry"].get("coordinates")
    try:
        # GeoJSON has longitude first; a third number is the altitude.
        lon, lat = (float(number) for number in coordinates[:2])
    except (TypeError, ValueError):
        report.warn(f"geojson: point without valid coordinates: {coordinates!r}", item.path)
        return None
    if not _on_map(lat, lon):
        report.warn(f"geojson: point {coordinates!r} is outside the map", item.path)
        return None
    properties = feature.get("properties") or {}
    label = str(properties.get("name") or properties.get("label") or "").strip() or None
    return Marker(
        coordinates = Coordinates(lat = lat, lon = lon),
        label = label,
        ref = _marker_ref(properties.get("link"), index, item, report)
    )

def _marker_ref(
    link: object,
    index: LinkIndex,
    item: ContentItem,
    report: Report
) -> str | None:
    """`link` as "[[Ambon]]", "Ambon" or "/records/ambon"."""
    if link is None or str(link).strip() == "":
        return None
    text = str(link).strip()
    if text.startswith("/"):
        ref = text[1:].split("?", 1)[0].split("#", 1)[0]
        ref = ref if ref in index.refs.values() else None
    else:
        ref = resolve_link(_frontmatter_link(text), index)
    if ref is None:
        report.warn(f"geojson: marker links to unknown page {text!r}, is not clickable", item.path)
    return ref

def _on_map(lat: float, lon: float) -> bool:
    return _MAP_BOUNDS["lat"][0] <= lat <= _MAP_BOUNDS["lat"][1] and _MAP_BOUNDS["lon"][0] <= lon <= _MAP_BOUNDS["lon"][1]

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
