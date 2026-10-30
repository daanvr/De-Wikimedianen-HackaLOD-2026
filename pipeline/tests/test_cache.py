from pathlib import Path

from siboga.cache import Cache
from siboga.models import CachedResponse
import pytest

URL = "https://www.wikidata.org/wiki/Special:EntityData/Q1940785.json"

@pytest.fixture
def cache(tmp_path: Path):
    cache = Cache(tmp_path / "db" / "cache.sqlite", tmp_path / "media")
    yield cache
    cache.close()

def _response(
    status: int = 200,
    body: bytes | None = b'{"a": 1}',
    url: str = URL
) -> CachedResponse:
    return CachedResponse(
        adapter = "wikidata",
        body = body,
        content_type = "application/json",
        fetched_at = "2026-10-30T12:00:00+00:00",
        status = status,
        url = url
    )

def test_creates_directories(tmp_path: Path):
    cache = Cache(tmp_path / "a" / "b" / "cache.sqlite", tmp_path / "c" / "media")
    assert (tmp_path / "a" / "b" / "cache.sqlite").is_file()
    assert (tmp_path / "c" / "media").is_dir()
    cache.close()

def test_get_missing_returns_none(cache: Cache):
    assert cache.get(URL) is None
    assert cache.get_json(URL) is None

def test_put_get_roundtrip(cache: Cache):
    cache.put(_response())
    assert cache.get(URL) == _response()
    assert cache.get_json(URL) == {"a": 1}

def test_put_replaces_ok_with_newer_ok(cache: Cache):
    cache.put(_response())
    cache.put(_response(body = b'{"a": 2}'))
    assert cache.get_json(URL) == {"a": 2}

def test_put_never_replaces_ok_with_failure(cache: Cache):
    cache.put(_response())
    cache.put(_response(status = 0, body = None))
    cache.put(_response(status = 503, body = b"down"))
    assert cache.get(URL) == _response()

def test_put_replaces_failure_with_failure_and_ok(cache: Cache):
    cache.put(_response(status = 0, body = None))
    cache.put(_response(status = 404, body = b"not found"))
    assert cache.get(URL).status == 404
    assert cache.get_json(URL) is None
    cache.put(_response())
    assert cache.get(URL).status == 200

def test_get_json_invalid_json(cache: Cache):
    cache.put(_response(body = b"<html>"))
    assert cache.get_json(URL) is None

def test_persists_after_reopen(tmp_path: Path):
    cache = Cache(tmp_path / "cache.sqlite", tmp_path / "media")
    cache.put(_response())
    cache.close()
    cache = Cache(tmp_path / "cache.sqlite", tmp_path / "media")
    assert cache.get(URL) == _response()
    cache.close()

def test_media_path_is_deterministic(cache: Cache):
    url = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.jpg"
    assert cache.media_path(url) == cache.media_path(url)
    assert cache.media_path(url).parent == cache.media_dir
    assert cache.media_path(url) != cache.media_path(url + "?x=1")

@pytest.mark.parametrize(
    ("url", "suffix"),
    [
        ("https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.JPG", ".jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Example.jpg/120px-Example.jpg", ".jpg"),
        ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Map.svg/800px-Map.svg.png", ".png"),
        ("https://example.org/scan.tiff?download=1", ".tiff"),
        ("https://example.org/sound.mp3", ".mp3"),
        ("https://example.org/Foto%20van%20Siboga.JPEG", ".jpeg"),
        ("https://www.wikidata.org/wiki/Q1940785", ""),
        ("https://example.org/", ""),
        ("https://example.org/api/v1.2", ""),
        ("https://example.org/file.verylongext", "")
    ]
)
def test_media_path_suffix(
    cache: Cache,
    url: str,
    suffix: str
):
    assert cache.media_path(url).suffix == suffix
    assert len(cache.media_path(url).stem) == 40

def test_has_media(cache: Cache):
    url = "https://example.org/a.png"
    assert not cache.has_media(url)
    cache.media_path(url).write_bytes(b"png")
    assert cache.has_media(url)
