"""Step `build`: merges content and cache into the frontend data. Runs without internet."""
from datetime import datetime, timezone
from pathlib import Path
import json
import mimetypes
import re
import shutil
import subprocess

from loguru import logger
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from siboga.cache import Cache
from siboga.config import Config
from siboga.content import (
    LinkIndex,
    body_images,
    build_link_index,
    chapter_coordinates,
    chapter_number,
    content_type,
    convert_body,
    description,
    page_title,
    plugin_title,
    read_content,
    read_messages,
    record_uri,
    show_in_explore
)
from siboga.fields import FieldCatalog, load_fields
from siboga.models import AudioInfo, ContentItem, Coordinates, ImageInfo, ItemKind, Report, SourceData
from siboga.sources import Registry, build_registry

# The source of a value that an editor wrote in the frontmatter, such as description_nl.
CONTENT_SOURCE = "content"
SCHEMA_VERSION = 3

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")

class OutputModel(BaseModel):
    """Base for the output: snake_case in Python, camelCase in the JSON."""
    model_config = ConfigDict(
        alias_generator = to_camel,
        populate_by_name = True
    )

class CoordinatesOut(OutputModel):
    lat: float
    lon: float

class ImageOut(OutputModel):
    src: str
    credit: str
    license: str
    license_url: str | None
    source_url: str | None
    source: str

class AudioOut(OutputModel):
    src: str
    mime_type: str | None
    credit: str
    license: str
    license_url: str | None
    source_url: str | None
    source: str

class FieldOut(OutputModel):
    key: str
    type: str
    values: list[str]
    source: str

class SourceOut(OutputModel):
    name: str
    uri: str

class PageOut(OutputModel):
    ref: str
    id: str
    title: str
    body: str | None
    links: list[str]
    backlinks: list[str]

class PluginOut(OutputModel):
    ref: str
    id: str
    title: str
    description: str | None
    show_in_explore: bool
    body: str | None
    links: list[str]
    backlinks: list[str]

class ChapterOut(OutputModel):
    ref: str
    id: str
    title: str
    number: int | None
    coordinates: CoordinatesOut | None
    body: str | None
    links: list[str]
    backlinks: list[str]

class RecordOut(OutputModel):
    ref: str
    id: str
    title: str
    content_type: str | None
    label: str | None
    label_source: str | None
    description: str | None
    description_source: str | None
    uri: str | None
    source: str | None
    sources: list[SourceOut]
    body: str | None
    image: ImageOut | None
    audio: AudioOut | None = None
    coordinates: CoordinatesOut | None
    coordinates_source: str | None
    fields: list[FieldOut]
    links: list[str]
    backlinks: list[str]

class Meta(OutputModel):
    schema_version: int
    generated_at: str
    content_commit: str | None
    warnings: int

class FrontendData(OutputModel):
    meta: Meta
    messages: dict[str, str]
    pages: dict[str, PageOut]
    plugins: dict[str, PluginOut] = {}
    chapters: list[ChapterOut]
    records: dict[str, RecordOut]

def check_output(output_path: Path) -> list[str]:
    """Checks the frontend data against the contract. Returns a list of problems."""
    json_path = output_path / "siboga.json"
    if not json_path.exists():
        return [f"{json_path} does not exist"]
    data = FrontendData.model_validate_json(json_path.read_text(encoding = "utf-8"))
    problems = []
    if data.meta.schema_version != SCHEMA_VERSION:
        problems.append(f"schemaVersion is {data.meta.schema_version}, expected {SCHEMA_VERSION}")
    items = {item.ref: item for item in [*data.pages.values(), *data.plugins.values(), *data.chapters, *data.records.values()]}
    for key, item in [*data.pages.items(), *data.plugins.items(), *data.records.items()]:
        if key != item.id:
            problems.append(f"{item.ref}: key {key} is not the id")
    for item in items.values():
        for ref in [*item.links, *item.backlinks]:
            if ref not in items:
                problems.append(f"{item.ref}: refers to unknown ref {ref}")
        for target in MARKDOWN_LINK.findall(item.body or ""):
            # A plugin link carries its argument in the query string.
            if target.startswith("/") and re.split(r"[?#]", target[1:], maxsplit = 1)[0] not in items:
                problems.append(f"{item.ref}: link in body to unknown page {target}")
            elif target.startswith("media/") and not (output_path / target).exists():
                problems.append(f"{item.ref}: media file {target} is missing")
        for kind in ("image", "audio"):
            media = getattr(item, kind, None)
            if media is not None and not (output_path / media.src).exists():
                problems.append(f"{item.ref}: {kind} {media.src} is missing")
    return problems

def run_build(
    config: Config,
    report: Report
) -> Path:
    """Builds siboga.json and media/ in a temporary directory, then moves it into place."""
    items = read_content(config.content_path, report)
    messages = read_messages(config.content_path, report)
    catalog = load_fields()
    _check_field_messages(catalog, messages, report)
    index = build_link_index(items, config.content_path)
    registry = build_registry(config)
    cache = Cache(config.cache_path, config.media_path)
    staging = config.output_path.with_name(config.output_path.name + ".tmp")
    if staging.exists():
        shutil.rmtree(staging)
    media_dir = staging / "media"
    media_dir.mkdir(parents = True)
    try:
        pages, plugins, chapters, records = _build_items(items, index, registry, cache, catalog, media_dir, report)
    finally:
        cache.close()
    _add_backlinks([*pages.values(), *plugins.values(), *chapters, *records.values()])
    _check_image_licenses(items, [*pages.values(), *plugins.values(), *chapters, *records.values()], records, report)
    data = FrontendData(
        meta = Meta(
            schema_version = SCHEMA_VERSION,
            generated_at = datetime.now(timezone.utc).isoformat(timespec = "seconds"),
            content_commit = _content_commit(config.content_path),
            warnings = len(report.warnings)
        ),
        messages = dict(sorted(messages.items())),
        pages = dict(sorted(pages.items())),
        plugins = dict(sorted(plugins.items())),
        chapters = sorted(chapters, key = lambda chapter: (chapter.number is None, chapter.number or 0, chapter.id)),
        records = dict(sorted(records.items()))
    )
    json_path = staging / "siboga.json"
    json_path.write_text(
        json.dumps(data.model_dump(by_alias = True, mode = "json"), ensure_ascii = False, indent = 4) + "\n",
        encoding = "utf-8"
    )
    _replace_dir(staging, config.output_path)
    media_count = len(list((config.output_path / "media").iterdir()))
    logger.info(f"build done: {len(pages)} pages, {len(plugins)} plugins, {len(chapters)} chapters, {len(records)} records, {len(messages)} messages, {media_count} media files in {config.output_path}")
    return config.output_path / "siboga.json"

def _add_backlinks(items: list[PageOut | PluginOut | ChapterOut | RecordOut]) -> None:
    by_ref = {item.ref: item for item in items}
    for item in items:
        for ref in item.links:
            target = by_ref.get(ref)
            if target is not None and item.ref not in target.backlinks:
                target.backlinks.append(item.ref)

def _body_or_none(markdown: str) -> str | None:
    text = markdown.strip()
    return text or None

def _build_chapter(
    item: ContentItem,
    index: LinkIndex,
    media_dir: Path,
    report: Report
) -> ChapterOut:
    converted = convert_body(item, index, report)
    _copy_attachments(converted.attachments, media_dir, item, report)
    return ChapterOut(
        ref = item.ref,
        id = item.id,
        title = item.title,
        number = chapter_number(item, report),
        coordinates = _coordinates_out(chapter_coordinates(item, report)),
        body = _body_or_none(converted.markdown),
        links = converted.links,
        backlinks = []
    )

def _build_fields(
    source: SourceData,
    own_source: str | None,
    profile: list[str],
    catalog: FieldCatalog,
    item: ContentItem,
    report: Report
) -> list[FieldOut]:
    """Picks the fields that belong to the content type, in the order of fields.toml."""
    fields = []
    for key in profile:
        values = []
        for value in source.fields.get(key, []):
            if catalog.is_valid(key, value):
                values.append(value)
            else:
                report.warn(f"invalid value for {key}: {value!r}", item.path)
        if values:
            fields.append(FieldOut(
                key = key,
                type = catalog.types[key].value,
                values = values,
                source = source.source_of_field(key, own_source)
            ))
    return fields

def _build_items(
    items: list[ContentItem],
    index: LinkIndex,
    registry: Registry,
    cache: Cache,
    catalog: FieldCatalog,
    media_dir: Path,
    report: Report
) -> tuple[dict[str, PageOut], dict[str, PluginOut], list[ChapterOut], dict[str, RecordOut]]:
    pages = {}
    plugins = {}
    chapters = []
    records = {}
    for item in items:
        if item.kind == ItemKind.PAGE:
            pages[item.id] = _build_page(item, index, media_dir, report)
        elif item.kind == ItemKind.PLUGIN:
            plugins[item.id] = _build_plugin(item, index, media_dir, report)
        elif item.kind == ItemKind.CHAPTER:
            chapters.append(_build_chapter(item, index, media_dir, report))
        else:
            records[item.id] = _build_record(item, index, registry, cache, catalog, media_dir, report)
    return pages, plugins, chapters, records

def _build_page(
    item: ContentItem,
    index: LinkIndex,
    media_dir: Path,
    report: Report
) -> PageOut:
    converted = convert_body(item, index, report)
    _copy_attachments(converted.attachments, media_dir, item, report)
    return PageOut(
        ref = item.ref,
        id = item.id,
        title = page_title(item, report),
        body = _body_or_none(converted.markdown),
        links = converted.links,
        backlinks = []
    )

def _build_plugin(
    item: ContentItem,
    index: LinkIndex,
    media_dir: Path,
    report: Report
) -> PluginOut:
    converted = convert_body(item, index, report)
    _copy_attachments(converted.attachments, media_dir, item, report)
    return PluginOut(
        ref = item.ref,
        id = item.id,
        title = plugin_title(item),
        description = description(item),
        show_in_explore = show_in_explore(item, report),
        body = _body_or_none(converted.markdown),
        links = converted.links,
        backlinks = []
    )

def _build_record(
    item: ContentItem,
    index: LinkIndex,
    registry: Registry,
    cache: Cache,
    catalog: FieldCatalog,
    media_dir: Path,
    report: Report
) -> RecordOut:
    converted = convert_body(item, index, report)
    _copy_attachments(converted.attachments, media_dir, item, report)
    uri = record_uri(item, report)
    adapter = registry.adapter_for(uri) if uri else None
    source = None
    if uri and adapter is None:
        report.warn(f"no adapter for {uri}", item.path)
    elif adapter is not None:
        source = _normalize(adapter, uri, cache, item, report)
    # Every value says where it came from: the record's own source, a linked one, or the content.
    own_source = None
    sources = []
    if source is not None:
        own_source = adapter.name
        sources = [SourceOut(name = adapter.name, uri = uri)]
        sources += [SourceOut(name = linked.name, uri = linked.uri) for linked in source.linked_sources]
    source = source or SourceData()
    record_type = content_type(item, report)
    own_description = description(item)
    image_source = _source_of(source, "image", own_source)
    return RecordOut(
        ref = item.ref,
        id = item.id,
        title = item.title,
        content_type = record_type,
        label = source.label,
        label_source = _source_of(source, "label", own_source),
        description = own_description or source.description,
        description_source = CONTENT_SOURCE if own_description else _source_of(source, "description", own_source),
        uri = uri,
        source = adapter.name if adapter else None,
        sources = sources,
        body = _body_or_none(converted.markdown),
        image = _copy_image(source.image, image_source, item, cache, media_dir, report),
        audio = _copy_audio(source.audio, own_source, item, cache, media_dir, report),
        coordinates = _coordinates_out(source.coordinates),
        coordinates_source = _source_of(source, "coordinates", own_source),
        fields = _build_fields(source, own_source, catalog.profiles.get(record_type or "", []), catalog, item, report),
        links = converted.links,
        backlinks = []
    )

def _check_field_messages(
    catalog: FieldCatalog,
    messages: dict[str, str],
    report: Report
) -> None:
    """The frontend shows field names via i18n; reports which field_<key> messages are still missing."""
    used = sorted({key for profile in catalog.profiles.values() for key in profile})
    missing = [f"field_{key}" for key in used if f"field_{key}" not in messages]
    if missing:
        report.warn(f"i18n is missing messages for field names: {', '.join(missing)}")

def _coordinates_out(coordinates: Coordinates | None) -> CoordinatesOut | None:
    if coordinates is None:
        return None
    return CoordinatesOut(lat = coordinates.lat, lon = coordinates.lon)

def _content_commit(content_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(content_path), "rev-parse", "--short", "HEAD"],
            capture_output = True,
            check = True,
            text = True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None

def _check_image_licenses(
    items: list[ContentItem],
    outputs: list[PageOut | PluginOut | ChapterOut | RecordOut],
    records: dict[str, RecordOut],
    report: Report
) -> None:
    """Warns about every image in a body that gets no credit and license on the site.

    Those come from the record that the caption below the image links to, so that record must have an image.
    """
    paths = {item.ref: item.path for item in items}
    for output in outputs:
        for image in body_images(output.body or ""):
            record = records.get(image.record_id) if image.record_id else None
            if record is None:
                report.warn(f"image without license: {image.src}; give it a caption that links to a record of the image", paths.get(output.ref))
            elif record.image is None:
                report.warn(f"image without license: {image.src}; its caption links to records/{record.id}, which has no image with a license", paths.get(output.ref))

def _copy_attachments(
    attachments: dict[str, Path],
    media_dir: Path,
    item: ContentItem,
    report: Report
) -> None:
    for name, source in attachments.items():
        target = media_dir / name
        if target.exists():
            continue
        try:
            shutil.copyfile(source, target)
        except OSError as error:
            report.warn(f"attachment {source.name} not copied: {error}", item.path)

def _copy_audio(
    audio: AudioInfo | None,
    audio_source: str | None,
    item: ContentItem,
    cache: Cache,
    media_dir: Path,
    report: Report
) -> AudioOut | None:
    """Copies a sound recording from the cache to media/; like an image, only with license and credit."""
    if audio is None or audio_source is None:
        return None
    if not audio.license or not audio.credit:
        report.warn(f"audio skipped: license or credit is missing ({audio.source_url or audio.download_url})", item.path)
        return None
    src = _copy_cached_file(audio.download_url, item, cache, media_dir, report)
    if src is None:
        return None
    return AudioOut(
        src = src,
        mime_type = audio.mime_type,
        credit = audio.credit,
        license = audio.license,
        license_url = audio.license_url,
        source_url = audio.source_url,
        source = audio_source
    )

def _copy_cached_file(
    download_url: str,
    item: ContentItem,
    cache: Cache,
    media_dir: Path,
    report: Report
) -> str | None:
    """Copies a downloaded file from the cache to media/<item id>.<extension>; returns its src."""
    if not cache.has_media(download_url):
        report.warn(f"media file is not in the cache, run fetch first ({download_url})", item.path)
        return None
    cached_file = cache.media_path(download_url)
    name = f"{item.id}{_media_suffix(cached_file, download_url, cache)}"
    if (media_dir / name).exists():
        report.warn(f"media file {name} already exists and will be overwritten", item.path)
    shutil.copyfile(cached_file, media_dir / name)
    return f"media/{name}"

def _copy_image(
    image: ImageInfo | None,
    image_source: str | None,
    item: ContentItem,
    cache: Cache,
    media_dir: Path,
    report: Report
) -> ImageOut | None:
    """Copies the image from the cache to media/. No file, license or credit means no image."""
    if image is None or image_source is None:
        return None
    if not image.license or not image.credit:
        report.warn(f"image skipped: license or credit is missing ({image.source_url or image.download_url})", item.path)
        return None
    src = _copy_cached_file(image.download_url, item, cache, media_dir, report)
    if src is None:
        return None
    return ImageOut(
        src = src,
        credit = image.credit,
        license = image.license,
        license_url = image.license_url,
        source_url = image.source_url,
        source = image_source
    )

def _media_suffix(
    cached_file: Path,
    url: str,
    cache: Cache
) -> str:
    if cached_file.suffix:
        return cached_file.suffix.lower()
    response = cache.get(url)
    content_type = response.content_type.split(";")[0].strip() if response and response.content_type else ""
    return mimetypes.guess_extension(content_type) or ""

def _normalize(
    adapter,
    uri: str,
    cache: Cache,
    item: ContentItem,
    report: Report
) -> SourceData | None:
    try:
        source = adapter.normalize(uri, cache)
    except Exception as error:
        # One broken source must not stop the rest of the build.
        report.warn(f"normalizing failed ({adapter.name}): {error!r}", item.path)
        return None
    if source is None:
        report.warn(f"no data from {adapter.name} in the cache, run fetch first ({uri})", item.path)
    return source

def _replace_dir(
    staging: Path,
    target: Path
) -> None:
    target.parent.mkdir(parents = True, exist_ok = True)
    if target.exists():
        shutil.rmtree(target)
    staging.rename(target)

def _source_of(
    source: SourceData,
    attribute: str,
    own_source: str | None
) -> str | None:
    """The name of the source of an attribute, or None if it has no value."""
    if not getattr(source, attribute) or own_source is None:
        return None
    return source.source_of(attribute, own_source)
