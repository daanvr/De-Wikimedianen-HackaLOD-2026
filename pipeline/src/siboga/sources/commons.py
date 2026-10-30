"""Adapter for files on Wikimedia Commons, plus helpers for images from Commons."""
from __future__ import annotations

from datetime import date
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote, urlencode
import re

from loguru import logger

from siboga.models import ImageInfo, SourceData
from siboga.sources.base import SourceAdapter

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

API_URL = "https://commons.wikimedia.org/w/api.php"
BLOCK_TAGS = {"br", "div", "li", "p", "td", "tr"}
# A MediaInfo entity on Commons; the number after the M is the page id of the file.
ENTITY_URL = re.compile(r"https?://commons\.wikimedia\.org/(entity/|wiki/Special:EntityPage/)M(\d+)(?![\w/])")
FILE_PREFIXES = ("file:", "bestand:")
FILE_URL = re.compile(r"https?://commons\.wikimedia\.org/wiki/(File|Bestand):.+", re.IGNORECASE)
ISO_DATE = re.compile(r"\d{4}(-\d{2}(-\d{2})?)?")
USELESS_CREDIT = re.compile(r"^(eigen werk|own work)\b|geüpload|uploaded", re.IGNORECASE)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

class CommonsAdapter(SourceAdapter):
    name = "commons"

    def __init__(self, image_width: int):
        self.image_width = image_width

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        _fetch_download(self._url(uri), uri, fetcher, self.name)

    def matches(self, uri: str) -> bool:
        return FILE_URL.match(uri) is not None or ENTITY_URL.match(uri) is not None

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        data = cache.get_json(self._url(uri))
        info = _imageinfo(data)
        if info is None:
            logger.warning(f"Geen imageinfo van Commons in de cache voor {uri}")
            return None
        # For an M entity the file name is only in the response.
        filename = (_page_filename(data) or uri) if ENTITY_URL.match(uri) else filename_from_url(uri)
        metadata = info.get("extmetadata") or {}
        return SourceData(
            description = _metadata_text(metadata, "ImageDescription"),
            fields = _fields(metadata),
            image = _image(info, filename),
            label = _metadata_text(metadata, "ObjectName") or PurePosixPath(filename).stem
        )

    def _url(self, uri: str) -> str:
        """The imageinfo URL for a URI: by page id for an M entity, otherwise by file name."""
        match = ENTITY_URL.match(uri)
        if match:
            return pageid_imageinfo_url(int(match.group(2)), self.image_width)
        return imageinfo_url(filename_from_url(uri), self.image_width)

class _TextExtractor(HTMLParser):
    """Extracts the visible plain text from a piece of HTML; hidden elements are dropped."""
    def __init__(self):
        super().__init__(convert_charrefs = True)
        self.open_tags: list[tuple[str, bool]] = []
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if not any(hidden for _, hidden in self.open_tags):
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCK_TAGS:
            self.parts.append(" ")
        for index in range(len(self.open_tags) - 1, -1, -1):
            if self.open_tags[index][0] == tag:
                del self.open_tags[index:]
                break

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in BLOCK_TAGS:
            self.parts.append(" ")
        if tag in VOID_TAGS:
            return
        style = (dict(attrs).get("style") or "").replace(" ", "").lower()
        self.open_tags.append((tag, "display:none" in style))

def fetch_image(
    filename: str,
    width: int,
    fetcher: Fetcher,
    adapter: str
) -> None:
    """Fetches the imageinfo of a Commons file and downloads the image."""
    _fetch_download(imageinfo_url(filename, width), filename, fetcher, adapter)

def filename_from_url(url_or_name: str) -> str:
    """File name as Commons displays it, from a URL or a bare name."""
    name = unquote(url_or_name.strip())
    if "/wiki/" in name:
        name = name.split("/wiki/", 1)[1]
    name = name.split("?", 1)[0].split("#", 1)[0]
    for prefix in FILE_PREFIXES:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break
    return name.replace("_", " ").strip()

def imageinfo_url(filename: str, width: int) -> str:
    """API URL for the imageinfo of a file; always the same for the same input."""
    return _api_url(("titles", f"File:{filename}"), width)

def pageid_imageinfo_url(page_id: int, width: int) -> str:
    """Like imageinfo_url, but by page id, for a MediaInfo entity (M + page id)."""
    return _api_url(("pageids", str(page_id)), width)

def read_image(
    filename: str,
    width: int,
    cache: Cache
) -> ImageInfo | None:
    """Image with attribution and license, from the imageinfo in the cache."""
    info = _imageinfo(cache.get_json(imageinfo_url(filename, width)))
    if info is None:
        logger.warning(f"Geen imageinfo van Commons in de cache voor {filename}")
        return None
    return _image(info, filename)

def strip_html(value: str | None) -> str | None:
    """Plain text without tags, with whitespace collapsed; None if nothing remains."""
    if not value:
        return None
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    text = " ".join("".join(parser.parts).split())
    return text or None

def _api_url(target: tuple[str, str], width: int) -> str:
    """API URL for the imageinfo of one page (titles or pageids); always the same for the same input."""
    params = [
        ("action", "query"),
        ("format", "json"),
        ("formatversion", "2"),
        ("prop", "imageinfo"),
        ("iiprop", "url|extmetadata|mime|size"),
        ("iiurlwidth", str(width)),
        ("iiextmetadatalanguage", "nl"),
        target
    ]
    return f"{API_URL}?{urlencode(params, quote_via = quote)}"

def _credit(metadata: dict) -> str | None:
    artist = _metadata_text(metadata, "Artist")
    credit = _metadata_text(metadata, "Credit")
    if credit and USELESS_CREDIT.search(credit):
        credit = None
    if not artist:
        return credit
    if not credit or credit.lower() in artist.lower():
        return artist
    return f"{artist}, {credit}"

def _fetch_download(
    url: str,
    name: str,
    fetcher: Fetcher,
    adapter: str
) -> None:
    """Fetches the imageinfo at url and downloads the image; name is only for the log messages."""
    info = _imageinfo(fetcher.get_json(url, adapter))
    if info is None:
        logger.warning(f"Geen imageinfo van Commons voor {name}")
        return
    download_url = info.get("thumburl") or info.get("url")
    if not download_url:
        logger.warning(f"Geen download-URL op Commons voor {name}")
        return
    fetcher.download(download_url, adapter)

def _fields(metadata: dict) -> dict[str, list[str]]:
    """The fields from the extmetadata; a date that is not ISO becomes date_description."""
    fields = {}
    creator = _metadata_text(metadata, "Artist")
    if creator:
        fields["creator"] = [creator]
    date_text = _metadata_text(metadata, "DateTimeOriginal")
    created = _iso_date(date_text)
    if created:
        fields["created"] = [created]
    elif date_text:
        fields["date_description"] = [date_text]
    return fields

def _image(info: dict, name: str) -> ImageInfo | None:
    """Image with attribution and license from one imageinfo; name is only for the log message."""
    download_url = info.get("thumburl") or info.get("url")
    if not download_url:
        logger.warning(f"Geen download-URL op Commons voor {name}")
        return None
    metadata = info.get("extmetadata") or {}
    return ImageInfo(
        credit = _credit(metadata),
        download_url = download_url,
        license = _metadata_text(metadata, "LicenseShortName"),
        license_url = _metadata_text(metadata, "LicenseUrl"),
        source_url = info.get("descriptionurl")
    )

def _imageinfo(data: dict | list | None) -> dict | None:
    if not isinstance(data, dict):
        return None
    for page in data.get("query", {}).get("pages", []):
        infos = page.get("imageinfo") or []
        if infos:
            return infos[0]
    return None

def _iso_date(value: str | None) -> str | None:
    if not value or not ISO_DATE.fullmatch(value):
        return None
    parts = [int(part) for part in value.split("-")] + [1, 1]
    try:
        date(parts[0], parts[1], parts[2])
    except ValueError:
        return None
    return value

def _metadata_text(metadata: dict, key: str) -> str | None:
    entry = metadata.get(key)
    if not isinstance(entry, dict):
        return None
    return strip_html(str(entry.get("value", "")))

def _page_filename(data: dict | list | None) -> str | None:
    """The file name from the title of the first page in the response."""
    if not isinstance(data, dict):
        return None
    for page in data.get("query", {}).get("pages", []):
        title = page.get("title")
        if title:
            return filename_from_url(title)
    return None
