"""Stap `build`: content en cache samenvoegen tot de frontend data. Draait zonder internet."""
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
    build_link_index,
    chapter_location,
    chapter_number,
    content_type,
    convert_body,
    description,
    page_title,
    read_content,
    read_messages,
    record_uri
)
from siboga.fields import FieldCatalog, load_fields
from siboga.models import ContentItem, ImageInfo, ItemKind, Report, SourceData
from siboga.sources import Registry, build_registry

SCHEMA_VERSION = 2

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")

class OutputModel(BaseModel):
    """Basis voor de uitvoer: snake_case in Python, camelCase in de JSON."""
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

class FieldOut(OutputModel):
    key: str
    type: str
    values: list[str]

class PageOut(OutputModel):
    ref: str
    id: str
    title: str
    body: str | None
    links: list[str]
    backlinks: list[str]

class ChapterOut(OutputModel):
    ref: str
    id: str
    title: str
    number: int | None
    location: str | None
    body: str | None
    links: list[str]
    backlinks: list[str]

class RecordOut(OutputModel):
    ref: str
    id: str
    title: str
    content_type: str | None
    label: str | None
    description: str | None
    uri: str | None
    source: str | None
    body: str | None
    image: ImageOut | None
    coordinates: CoordinatesOut | None
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
    chapters: list[ChapterOut]
    records: dict[str, RecordOut]

def check_output(output_path: Path) -> list[str]:
    """Controleert de frontend data tegen het contract. Geeft een lijst met problemen terug."""
    json_path = output_path / "siboga.json"
    if not json_path.exists():
        return [f"{json_path} bestaat niet"]
    data = FrontendData.model_validate_json(json_path.read_text(encoding = "utf-8"))
    problems = []
    if data.meta.schema_version != SCHEMA_VERSION:
        problems.append(f"schemaVersion is {data.meta.schema_version}, verwacht {SCHEMA_VERSION}")
    items = {item.ref: item for item in [*data.pages.values(), *data.chapters, *data.records.values()]}
    for key, item in [*data.pages.items(), *data.records.items()]:
        if key != item.id:
            problems.append(f"{item.ref}: sleutel {key} is niet het id")
    for item in items.values():
        refs = [*item.links, *item.backlinks]
        if isinstance(item, ChapterOut) and item.location:
            refs.append(item.location)
        for ref in refs:
            if ref not in items:
                problems.append(f"{item.ref}: verwijst naar onbekende ref {ref}")
        for target in MARKDOWN_LINK.findall(item.body or ""):
            if target.startswith("/") and target[1:] not in items:
                problems.append(f"{item.ref}: link in body naar onbekende pagina {target}")
            elif target.startswith("media/") and not (output_path / target).exists():
                problems.append(f"{item.ref}: mediabestand {target} ontbreekt")
        image = getattr(item, "image", None)
        if image is not None and not (output_path / image.src).exists():
            problems.append(f"{item.ref}: plaatje {image.src} ontbreekt")
    return problems

def run_build(
    config: Config,
    report: Report
) -> Path:
    """Bouwt siboga.json en media/ in een tijdelijke map en zet die daarna op zijn plek."""
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
        pages, chapters, records = _build_items(items, index, registry, cache, catalog, media_dir, report)
    finally:
        cache.close()
    _add_backlinks([*pages.values(), *chapters, *records.values()])
    data = FrontendData(
        meta = Meta(
            schema_version = SCHEMA_VERSION,
            generated_at = datetime.now(timezone.utc).isoformat(timespec = "seconds"),
            content_commit = _content_commit(config.content_path),
            warnings = len(report.warnings)
        ),
        messages = dict(sorted(messages.items())),
        pages = dict(sorted(pages.items())),
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
    logger.info(f"build klaar: {len(pages)} pages, {len(chapters)} chapters, {len(records)} records, {len(messages)} berichten, {media_count} mediabestanden in {config.output_path}")
    return config.output_path / "siboga.json"

def _add_backlinks(items: list[PageOut | ChapterOut | RecordOut]) -> None:
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
        location = chapter_location(item, index, report),
        body = _body_or_none(converted.markdown),
        links = converted.links,
        backlinks = []
    )

def _build_fields(
    source: SourceData,
    profile: list[str],
    catalog: FieldCatalog,
    item: ContentItem,
    report: Report
) -> list[FieldOut]:
    """Kiest de velden die bij het contenttype horen, in de volgorde van fields.toml."""
    fields = []
    for key in profile:
        values = []
        for value in source.fields.get(key, []):
            if catalog.is_valid(key, value):
                values.append(value)
            else:
                report.warn(f"ongeldige waarde voor {key}: {value!r}", item.path)
        if values:
            fields.append(FieldOut(key = key, type = catalog.types[key].value, values = values))
    return fields

def _build_items(
    items: list[ContentItem],
    index: LinkIndex,
    registry: Registry,
    cache: Cache,
    catalog: FieldCatalog,
    media_dir: Path,
    report: Report
) -> tuple[dict[str, PageOut], list[ChapterOut], dict[str, RecordOut]]:
    pages = {}
    chapters = []
    records = {}
    for item in items:
        if item.kind == ItemKind.PAGE:
            pages[item.id] = _build_page(item, index, media_dir, report)
        elif item.kind == ItemKind.CHAPTER:
            chapters.append(_build_chapter(item, index, media_dir, report))
        else:
            records[item.id] = _build_record(item, index, registry, cache, catalog, media_dir, report)
    return pages, chapters, records

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
        report.warn(f"geen adapter voor {uri}", item.path)
    elif adapter is not None:
        source = _normalize(adapter, uri, cache, item, report)
    source = source or SourceData()
    record_type = content_type(item, report)
    return RecordOut(
        ref = item.ref,
        id = item.id,
        title = item.title,
        content_type = record_type,
        label = source.label,
        description = description(item) or source.description,
        uri = uri,
        source = adapter.name if adapter else None,
        body = _body_or_none(converted.markdown),
        image = _copy_image(source.image, item, cache, media_dir, report),
        coordinates = CoordinatesOut(lat = source.coordinates.lat, lon = source.coordinates.lon) if source.coordinates else None,
        fields = _build_fields(source, catalog.profiles.get(record_type or "", []), catalog, item, report),
        links = converted.links,
        backlinks = []
    )

def _check_field_messages(
    catalog: FieldCatalog,
    messages: dict[str, str],
    report: Report
) -> None:
    """De frontend toont veldnamen via i18n; meld welke berichten field_<veld> nog ontbreken."""
    used = sorted({key for profile in catalog.profiles.values() for key in profile})
    missing = [f"field_{key}" for key in used if f"field_{key}" not in messages]
    if missing:
        report.warn(f"i18n mist berichten voor veldnamen: {', '.join(missing)}")

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
            report.warn(f"bijlage {source.name} niet gekopieerd: {error}", item.path)

def _copy_image(
    image: ImageInfo | None,
    item: ContentItem,
    cache: Cache,
    media_dir: Path,
    report: Report
) -> ImageOut | None:
    """Kopieert het plaatje uit de cache naar media/. Zonder bestand, licentie of bronvermelding geen plaatje."""
    if image is None:
        return None
    if not image.license or not image.credit:
        report.warn(f"plaatje overgeslagen: licentie of bronvermelding ontbreekt ({image.source_url or image.download_url})", item.path)
        return None
    if not cache.has_media(image.download_url):
        report.warn(f"plaatje staat niet in de cache, draai eerst fetch ({image.download_url})", item.path)
        return None
    cached_file = cache.media_path(image.download_url)
    name = f"{item.id}{_media_suffix(cached_file, image.download_url, cache)}"
    if (media_dir / name).exists():
        report.warn(f"mediabestand {name} bestaat al en wordt overschreven", item.path)
    shutil.copyfile(cached_file, media_dir / name)
    return ImageOut(
        src = f"media/{name}",
        credit = image.credit,
        license = image.license,
        license_url = image.license_url,
        source_url = image.source_url
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
        # Eén kapotte bron mag de rest van de build niet tegenhouden.
        report.warn(f"normaliseren mislukt ({adapter.name}): {error!r}", item.path)
        return None
    if source is None:
        report.warn(f"geen gegevens van {adapter.name} in de cache, draai eerst fetch ({uri})", item.path)
    return source

def _replace_dir(
    staging: Path,
    target: Path
) -> None:
    target.parent.mkdir(parents = True, exist_ok = True)
    if target.exists():
        shutil.rmtree(target)
    staging.rename(target)
