from pathlib import Path
import json

import pytest

from siboga.models import CachedResponse
from siboga.sources.commons import (
    CommonsAdapter,
    filename_from_url,
    imageinfo_url,
    pageid_imageinfo_url,
    read_image,
    strip_html
)

DECAPODA_URI = "https://commons.wikimedia.org/entity/M42651403"
FIXTURES = Path(__file__).parent / "fixtures" / "sources"
KOR_URI = "https://commons.wikimedia.org/wiki/File:UvA-Artis_300.005_-_Siboga_-_bovenkomen_van_de_kor.jpg"
KOR_FILE = "UvA-Artis 300.005 - Siboga - bovenkomen van de kor.jpg"
WIDTH = 1600

class FakeCache:
    """In-memory cache: URL to JSON response."""
    def __init__(self, responses: dict[str, object]):
        self.responses = responses

    def get(self, url: str) -> CachedResponse | None:
        if url not in self.responses:
            return None
        return CachedResponse(
            adapter = "test",
            body = json.dumps(self.responses[url]).encode(),
            content_type = "application/json",
            fetched_at = "2026-10-30T12:00:00Z",
            status = 200,
            url = url
        )

    def get_json(self, url: str) -> dict | list | None:
        response = self.get(url)
        return response.json() if response else None

    def has_media(self, url: str) -> bool:
        return False

    def media_path(self, url: str) -> Path:
        return Path("/media") / str(abs(hash(url)))

class FakeFetcher:
    """Fetcher that serves responses from a dict and records what was requested."""
    def __init__(self, responses: dict[str, object]):
        self.downloads: list[tuple[str, str]] = []
        self.requests: list[tuple[str, str]] = []
        self.responses = responses

    def download(
        self,
        url: str,
        adapter: str
    ) -> Path | None:
        self.downloads.append((url, adapter))
        return Path("/media/file")

    def get(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> CachedResponse | None:
        raise AssertionError("de adapter hoort get_json te gebruiken")

    def get_json(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> dict | list | None:
        self.requests.append((url, adapter))
        return self.responses.get(url)

def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())

def _imageinfo(metadata: dict[str, str], thumb: bool = True) -> dict:
    info = {
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Test.jpg",
        "extmetadata": {key: {"value": value} for key, value in metadata.items()},
        "url": "https://upload.wikimedia.org/test.jpg"
    }
    if thumb:
        info["thumburl"] = "https://upload.wikimedia.org/thumb/test.jpg"
    return {"query": {"pages": [{"title": "File:Test.jpg", "imageinfo": [info]}]}}

def test_fetch_downloads_original_without_thumb():
    fetcher = FakeFetcher({imageinfo_url("Test.jpg", WIDTH): _imageinfo({}, thumb = False)})
    CommonsAdapter(image_width = WIDTH).fetch("https://commons.wikimedia.org/wiki/File:Test.jpg", fetcher)
    assert fetcher.downloads == [("https://upload.wikimedia.org/test.jpg", "commons")]

def test_fetch_gets_imageinfo_and_downloads_thumb():
    response = _fixture("commons_bovenkomen_van_de_kor.json")
    fetcher = FakeFetcher({imageinfo_url(KOR_FILE, WIDTH): response})
    CommonsAdapter(image_width = WIDTH).fetch(KOR_URI, fetcher)
    assert fetcher.requests == [(imageinfo_url(KOR_FILE, WIDTH), "commons")]
    thumb = response["query"]["pages"][0]["imageinfo"][0]["thumburl"]
    assert fetcher.downloads == [(thumb, "commons")]

def test_fetch_media_entity_by_page_id():
    response = _fixture("commons_M42651403.json")
    fetcher = FakeFetcher({pageid_imageinfo_url(42651403, WIDTH): response})
    CommonsAdapter(image_width = WIDTH).fetch(DECAPODA_URI, fetcher)
    assert fetcher.requests == [(pageid_imageinfo_url(42651403, WIDTH), "commons")]
    thumb = response["query"]["pages"][0]["imageinfo"][0]["thumburl"]
    assert fetcher.downloads == [(thumb, "commons")]

def test_fetch_without_imageinfo_downloads_nothing():
    fetcher = FakeFetcher({})
    CommonsAdapter(image_width = WIDTH).fetch(KOR_URI, fetcher)
    assert fetcher.downloads == []

@pytest.mark.parametrize("value", [
    "https://commons.wikimedia.org/wiki/File:Siboga%2C_gunboat_%281898%29.jpg",
    "https://commons.wikimedia.org/wiki/Bestand:Siboga,_gunboat_(1898).jpg",
    "File:Siboga, gunboat (1898).jpg",
    "Siboga,_gunboat_(1898).jpg"
])
def test_filename_from_url(value: str):
    assert filename_from_url(value) == "Siboga, gunboat (1898).jpg"

def test_imageinfo_url_is_encoded_and_stable():
    url = imageinfo_url("Siboga, gunboat (1898).jpg", WIDTH)
    assert url == imageinfo_url(filename_from_url("File:Siboga,_gunboat_(1898).jpg"), WIDTH)
    assert url.startswith("https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2")
    assert "iiprop=url%7Cextmetadata%7Cmime%7Csize" in url
    assert "iiurlwidth=1600" in url
    assert "iiextmetadatalanguage=nl" in url
    assert url.endswith("titles=File%3ASiboga%2C%20gunboat%20%281898%29.jpg")

def test_pageid_imageinfo_url():
    assert pageid_imageinfo_url(42651403, WIDTH) == (
        "https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&prop=imageinfo"
        "&iiprop=url%7Cextmetadata%7Cmime%7Csize&iiurlwidth=1600&iiextmetadatalanguage=nl&pageids=42651403"
    )

@pytest.mark.parametrize("uri, expected", [
    (KOR_URI, True),
    ("http://commons.wikimedia.org/wiki/Bestand:Foo.jpg", True),
    (DECAPODA_URI, True),
    ("https://commons.wikimedia.org/wiki/Special:EntityPage/M42651403", True),
    ("https://commons.wikimedia.org/entity/M42651403/foo", False),
    ("https://commons.wikimedia.org/entity/M12abc", False),
    ("https://commons.wikimedia.org/entity/Q42", False),
    ("https://commons.wikimedia.org/wiki/Category:Siboga_Expedition", False),
    ("https://nl.wikipedia.org/wiki/File:Foo.jpg", False),
    ("https://www.wikidata.org/wiki/Q1940785", False)
])
def test_matches(uri: str, expected: bool):
    assert CommonsAdapter(image_width = WIDTH).matches(uri) is expected

@pytest.mark.parametrize("value, expected", [
    ("1899", {"created": ["1899"]}),
    ("1899-03", {"created": ["1899-03"]}),
    ("1899-03-07", {"created": ["1899-03-07"]}),
    ("<time datetime=\"1899\">1899</time>", {"created": ["1899"]}),
    ("ca. 1898<div style=\"display: none;\">date QS:P,+1898-00-00T00:00:00Z/9</div>", {"date_description": ["ca. 1898"]}),
    ("1899-13", {"date_description": ["1899-13"]}),
    ("1899-02-30", {"date_description": ["1899-02-30"]}),
    ("1899-03-07 12:00:00", {"date_description": ["1899-03-07 12:00:00"]}),
    ("<span style=\"display: none;\">1899</span>", {})
])
def test_normalize_dates(value: str, expected: dict):
    cache = FakeCache({imageinfo_url("Test.jpg", WIDTH): _imageinfo({"DateTimeOriginal": value})})
    data = CommonsAdapter(image_width = WIDTH).normalize("https://commons.wikimedia.org/wiki/File:Test.jpg", cache)
    assert data.fields == expected

def test_normalize_creator_is_visible_artist_text():
    artist = "<a href=\"x\">Jan</a><span style=\"display: none;\">Unknown author</span>"
    cache = FakeCache({imageinfo_url("Test.jpg", WIDTH): _imageinfo({"Artist": artist, "DateTimeOriginal": "1899"})})
    data = CommonsAdapter(image_width = WIDTH).normalize("https://commons.wikimedia.org/wiki/File:Test.jpg", cache)
    assert data.fields == {"created": ["1899"], "creator": ["Jan"]}

def test_normalize_label_falls_back_to_file_stem():
    cache = FakeCache({imageinfo_url("Test foto.jpg", WIDTH): _imageinfo({})})
    data = CommonsAdapter(image_width = WIDTH).normalize("https://commons.wikimedia.org/wiki/File:Test_foto.jpg", cache)
    assert data.label == "Test foto"
    assert data.description is None
    assert data.fields == {}
    assert data.image.license is None
    assert data.image.credit is None

def test_normalize_real_record():
    cache = FakeCache({imageinfo_url(KOR_FILE, WIDTH): _fixture("commons_bovenkomen_van_de_kor.json")})
    data = CommonsAdapter(image_width = WIDTH).normalize(KOR_URI, cache)
    assert data.label == "UvA-Artis 300.005 - Siboga - bovenkomen van de kor"
    assert data.description.startswith("1899-1900, Siboga-expeditie naar Nederlands Oost-Indië")
    assert "<" not in data.description
    assert data.fields == {
        "creator": ["Hugo Frederik Nierstrasz"],
        "date_description": ["tussen maart 1899 en februari 1900"]
    }
    assert data.coordinates is None
    assert data.image.credit == "Hugo Frederik Nierstrasz, Bijzondere Collecties van de Universiteit van Amsterdam"
    assert data.image.license == "Public domain"
    assert data.image.license_url is None
    assert data.image.source_url == KOR_URI
    assert data.image.download_url.startswith("https://thumb.wikimedia.org/")

def test_normalize_real_media_entity():
    cache = FakeCache({pageid_imageinfo_url(42651403, WIDTH): _fixture("commons_M42651403.json")})
    data = CommonsAdapter(image_width = WIDTH).normalize(DECAPODA_URI, cache)
    assert data.label == "The Decapoda of the Siboga Expedition (1911) (20223133003)"
    assert data.description.startswith("Title: The Decapoda of the Siboga Expedition")
    assert data.fields == {
        "created": ["1911"],
        "creator": ["Man, J. G. de, (Johannes Govertus. 1850-1930; Holthuis, L. B"]
    }
    assert data.image.license == "No restrictions"
    assert data.image.license_url == "https://www.flickr.com/commons/usage/"
    assert data.image.source_url == "https://commons.wikimedia.org/wiki/File:The_Decapoda_of_the_Siboga_Expedition_(1911)_(20223133003).jpg"
    assert data.image.download_url.startswith("https://thumb.wikimedia.org/")

def test_normalize_media_entity_label_falls_back_to_page_title():
    response = _imageinfo({})
    response["query"]["pages"][0]["title"] = "File:Een_tekening.jpg"
    cache = FakeCache({pageid_imageinfo_url(7, WIDTH): response})
    data = CommonsAdapter(image_width = WIDTH).normalize("https://commons.wikimedia.org/wiki/Special:EntityPage/M7", cache)
    assert data.label == "Een tekening"

def test_normalize_without_cache_returns_none():
    assert CommonsAdapter(image_width = WIDTH).normalize(KOR_URI, FakeCache({})) is None
    assert CommonsAdapter(image_width = WIDTH).normalize(DECAPODA_URI, FakeCache({})) is None

def test_read_image_drops_hidden_text_and_keeps_license_url():
    filename = filename_from_url(_fixture("commons_zeilvis.json")["query"]["pages"][0]["title"])
    cache = FakeCache({imageinfo_url(filename, WIDTH): _fixture("commons_zeilvis.json")})
    image = read_image(filename, WIDTH, cache)
    assert image.credit == "Onbekend, Wereldmuseum Amsterdam"
    assert image.license == "CC BY-SA 3.0"
    assert image.license_url == "https://creativecommons.org/licenses/by-sa/3.0"

def test_read_image_skips_upload_credit():
    filename = "Anna Antoinette Weber-van Bosse.jpg"
    cache = FakeCache({imageinfo_url(filename, WIDTH): _fixture("commons_anna_weber.json")})
    image = read_image(filename, WIDTH, cache)
    assert image.credit == "University of Amsterdam, Artis Library"
    assert image.license == "Public domain"

@pytest.mark.parametrize("artist, credit, expected", [
    ("Jan", "Eigen werk", "Jan"),
    ("Jan", "Jan", "Jan"),
    (None, "Rijksmuseum", "Rijksmuseum"),
    ("Jan", "Rijksmuseum", "Jan, Rijksmuseum")
])
def test_read_image_credit(
    artist: str | None,
    credit: str,
    expected: str
):
    metadata = {"Credit": credit, "LicenseShortName": "CC0"}
    if artist:
        metadata["Artist"] = artist
    cache = FakeCache({imageinfo_url("Test.jpg", WIDTH): _imageinfo(metadata)})
    assert read_image("Test.jpg", WIDTH, cache).credit == expected

def test_strip_html():
    value = "Onbekend<span style=\"display: none;\">Unknown <b>author</b></span> &amp; <a href=\"x\">Jan</a><br>Piet"
    assert strip_html(value) == "Onbekend & Jan Piet"
    assert strip_html("<p> </p>") is None
    assert strip_html(None) is None

def _audio_imageinfo() -> dict:
    return {"query": {"pages": [{"title": "File:Kat.ogg", "imageinfo": [{
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Kat.ogg",
        "extmetadata": {
            "Artist": {"value": "Tobias Puderer"},
            "LicenseShortName": {"value": "CC BY-SA 3.0"}
        },
        "mime": "application/ogg",
        "thumburl": "https://commons.wikimedia.org/w/resources/assets/file-type-icons/fileicon-ogg.png",
        "url": "https://upload.wikimedia.org/wikipedia/commons/5/53/Kat.ogg",
        "width": 0
    }]}]}}

def test_fetch_audio_downloads_the_file_not_the_icon():
    fetcher = FakeFetcher({imageinfo_url("Kat.ogg", WIDTH): _audio_imageinfo()})
    CommonsAdapter(image_width = WIDTH).fetch("https://commons.wikimedia.org/wiki/File:Kat.ogg", fetcher)
    assert fetcher.downloads == [("https://upload.wikimedia.org/wikipedia/commons/5/53/Kat.ogg", "commons")]

def test_normalize_audio():
    cache = FakeCache({imageinfo_url("Kat.ogg", WIDTH): _audio_imageinfo()})
    source = CommonsAdapter(image_width = WIDTH).normalize("https://commons.wikimedia.org/wiki/File:Kat.ogg", cache)
    assert source.image is None
    assert source.audio.download_url == "https://upload.wikimedia.org/wikipedia/commons/5/53/Kat.ogg"
    assert source.audio.mime_type == "application/ogg"
    assert source.audio.credit == "Tobias Puderer"
    assert source.audio.license == "CC BY-SA 3.0"

