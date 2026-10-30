"""Data types shared between content, sources, cache and build."""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

from loguru import logger

class ContentType(Enum):
    ARTICLE = "article"
    EXPEDITION = "expedition"
    ITEM = "item"
    LOCATION = "location"
    MEDIA = "media"
    PERSON = "person"
    SPECIMEN = "specimen"

class FieldType(Enum):
    DATE = "date"
    TEXT = "text"

class ItemKind(Enum):
    CHAPTER = "chapters"
    PAGE = "pages"
    RECORD = "records"

@dataclass
class CachedResponse:
    """One raw response from a source, exactly as it came in."""
    adapter: str
    body: bytes | None
    content_type: str | None
    fetched_at: str
    status: int
    url: str

    def is_ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self) -> dict | list | None:
        if not self.is_ok() or not self.body:
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    def text(self) -> str | None:
        if not self.is_ok() or self.body is None:
            return None
        return self.body.decode("utf-8", errors = "replace")

@dataclass
class ContentItem:
    """One chapter or record from the content repo."""
    body: str
    frontmatter: dict
    id: str
    kind: ItemKind
    path: Path
    title: str

    @property
    def ref(self) -> str:
        return f"{self.kind.value}/{self.id}"

@dataclass
class Coordinates:
    lat: float
    lon: float

@dataclass
class ImageInfo:
    """An image from a source. The file itself is in the cache under download_url."""
    credit: str | None
    download_url: str
    license: str | None
    license_url: str | None
    source_url: str | None

@dataclass
class SourceRef:
    """A source a record got data from: the adapter name and the URI it was asked for."""
    name: str
    uri: str

@dataclass
class SourceData:
    """What an adapter extracts from a source for display.

    fields holds all fields the adapter can fill, with the names from pipeline/fields.toml.
    Which of them are shown depends on the content type of the record.
    Everything comes from the adapter's own source, unless filled_by says a linked source filled it.
    """
    coordinates: Coordinates | None = None
    description: str | None = None
    fields: dict[str, list[str]] = field(default_factory = dict)
    # Attribute ("label", "description", "coordinates", "image") to the name of the linked source that filled it.
    filled_by: dict[str, str] = field(default_factory = dict)
    # Field key to the name of the linked source that filled it.
    filled_fields_by: dict[str, str] = field(default_factory = dict)
    image: ImageInfo | None = None
    label: str | None = None
    linked_sources: list[SourceRef] = field(default_factory = list)

    def fill_from(
        self,
        other: "SourceData",
        source: SourceRef
    ) -> None:
        """Fills what is still empty from a linked source and records that it did; existing values always win."""
        if source not in self.linked_sources:
            self.linked_sources.append(source)
        for attribute in ("coordinates", "description", "image", "label"):
            if not getattr(self, attribute) and getattr(other, attribute):
                setattr(self, attribute, getattr(other, attribute))
                self.filled_by[attribute] = source.name
        for key, values in other.fields.items():
            if values and not self.fields.get(key):
                self.fields[key] = list(values)
                self.filled_fields_by[key] = source.name

    def source_of(
        self,
        attribute: str,
        own_source: str
    ) -> str:
        """The name of the source that filled attribute; own_source unless a linked source did."""
        return self.filled_by.get(attribute, own_source)

    def source_of_field(
        self,
        key: str,
        own_source: str
    ) -> str:
        return self.filled_fields_by.get(key, own_source)

class Report:
    """Collects warnings for the summary at the end."""
    def __init__(self):
        self.warnings: list[str] = []

    def warn(
        self,
        message: str,
        path: Path | str | None = None
    ) -> None:
        text = f"{path}: {message}" if path else message
        self.warnings.append(text)
        logger.warning(text)
