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
class SourceData:
    """What an adapter extracts from a source for display.

    fields holds all fields the adapter can fill, with the names from pipeline/fields.toml.
    Which of them are shown depends on the content type of the record.
    """
    coordinates: Coordinates | None = None
    description: str | None = None
    fields: dict[str, list[str]] = field(default_factory = dict)
    image: ImageInfo | None = None
    label: str | None = None

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
