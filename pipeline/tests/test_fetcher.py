from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
import time

from siboga.cache import Cache
from siboga.fetcher import Fetcher
from siboga.models import CachedResponse
import httpx
import pytest

IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.jpg"
URL = "https://www.wikidata.org/wiki/Special:EntityData/Q1940785.json"
USER_AGENT = "SibogaTest/0.1 (test)"

@pytest.fixture
def cache(tmp_path: Path):
    cache = Cache(tmp_path / "cache.sqlite", tmp_path / "media")
    yield cache
    cache.close()

@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Vangt time.sleep af, zodat herpogingen de tests niet vertragen."""
    calls: list[float] = []
    monkeypatch.setattr("siboga.fetcher.time.sleep", calls.append)
    return calls

def _fetcher(
    cache: Cache,
    handler: Callable[[httpx.Request], httpx.Response],
    delay_seconds: float = 0.0,
    refresh: bool = False
) -> Fetcher:
    return Fetcher(
        cache,
        USER_AGENT,
        delay_seconds = delay_seconds,
        refresh = refresh,
        client = httpx.Client(transport = httpx.MockTransport(handler))
    )

def _ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json = {"id": "Q1940785"})

def _put(
    cache: Cache,
    fetched_at: str,
    body: bytes = b'{"old": true}'
) -> None:
    cache.put(CachedResponse(
        adapter = "wikidata",
        body = body,
        content_type = "application/json",
        fetched_at = fetched_at,
        status = 200,
        url = URL
    ))

def _days_ago(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days = days)).isoformat(timespec = "seconds")

def test_get_fetches_and_caches(cache: Cache):
    fetcher = _fetcher(cache, _ok)
    response = fetcher.get(URL, "wikidata")
    assert response.status == 200
    assert response.json() == {"id": "Q1940785"}
    assert response.content_type == "application/json"
    assert cache.get_json(URL) == {"id": "Q1940785"}
    assert cache.get(URL).adapter == "wikidata"
    assert fetcher.stats["fetched"] == 1

def test_user_agent_and_extra_headers_sent(cache: Cache):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json = {})

    fetcher = _fetcher(cache, handler)
    fetcher.get(URL, "wikidata", headers = {"Accept": "application/json", "User-Agent": "other"})
    fetcher.download(IMAGE_URL, "commons")
    assert [request.headers["user-agent"] for request in seen] == [USER_AGENT, USER_AGENT]
    assert seen[0].headers["accept"] == "application/json"

def test_fresh_cache_hit_needs_no_network(cache: Cache):
    _put(cache, _days_ago(1))

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("geen netwerk verwacht")

    fetcher = _fetcher(cache, handler)
    assert fetcher.get_json(URL, "wikidata") == {"old": True}
    assert fetcher.stats["cached"] == 1

def test_stale_cache_is_refetched(cache: Cache):
    _put(cache, _days_ago(40))
    fetcher = _fetcher(cache, _ok)
    assert fetcher.get_json(URL, "wikidata") == {"id": "Q1940785"}
    assert cache.get_json(URL) == {"id": "Q1940785"}
    assert fetcher.stats["fetched"] == 1

def test_refresh_ignores_fresh_cache(cache: Cache):
    _put(cache, _days_ago(1))
    fetcher = _fetcher(cache, _ok, refresh = True)
    assert fetcher.get_json(URL, "wikidata") == {"id": "Q1940785"}

def test_failed_cache_row_is_refetched(cache: Cache):
    cache.put(CachedResponse("wikidata", None, None, _days_ago(0), 0, URL))
    fetcher = _fetcher(cache, _ok)
    assert fetcher.get_json(URL, "wikidata") == {"id": "Q1940785"}

def test_follows_redirects(cache: Cache):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/old":
            return httpx.Response(301, headers = {"Location": URL})
        return httpx.Response(200, json = {"ok": 1})

    fetcher = _fetcher(cache, handler)
    assert fetcher.get_json("https://www.wikidata.org/old", "wikidata") == {"ok": 1}

def test_retry_on_503_then_success(cache: Cache, sleeps: list[float]):
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, headers = {"Retry-After": "2"})
        return httpx.Response(200, json = {"ok": 1})

    fetcher = _fetcher(cache, handler)
    assert fetcher.get_json(URL, "wikidata") == {"ok": 1}
    assert len(calls) == 2
    assert 2.0 in sleeps

def test_retry_after_is_capped(cache: Cache, sleeps: list[float]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers = {"Retry-After": "3600"})

    fetcher = _fetcher(cache, handler)
    response = fetcher.get(URL, "wikidata")
    assert response.status == 429
    assert max(sleeps) <= 10.0
    assert fetcher.stats["failed"] == 1

def test_no_retry_on_404(cache: Cache, sleeps: list[float]):
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(404)

    fetcher = _fetcher(cache, handler)
    assert fetcher.get(URL, "wikidata").status == 404
    assert len(calls) == 1
    assert cache.get(URL).status == 404

def test_network_error_without_copy_returns_status_0(cache: Cache, sleeps: list[float]):
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ConnectError("down", request = request)

    fetcher = _fetcher(cache, handler)
    response = fetcher.get(URL, "wikidata")
    assert response.status == 0
    assert response.json() is None
    assert len(calls) == 3
    assert cache.get(URL).status == 0
    assert fetcher.get_json(URL, "wikidata") is None

def test_network_error_returns_previous_ok_copy(cache: Cache, sleeps: list[float]):
    _put(cache, _days_ago(40))

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request = request)

    fetcher = _fetcher(cache, handler)
    assert fetcher.get_json(URL, "wikidata") == {"old": True}
    assert cache.get(URL).status == 200
    assert cache.get_json(URL) == {"old": True}
    assert fetcher.stats["failed"] == 1

def test_download_success(cache: Cache):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content = b"jpegdata", headers = {"Content-Type": "image/jpeg"})

    fetcher = _fetcher(cache, handler)
    path = fetcher.download(IMAGE_URL, "commons")
    assert path == cache.media_path(IMAGE_URL)
    assert path.read_bytes() == b"jpegdata"
    assert path.suffix == ".jpg"
    assert cache.has_media(IMAGE_URL)
    row = cache.get(IMAGE_URL)
    assert (row.status, row.body, row.content_type) == (200, None, "image/jpeg")
    assert fetcher.stats["downloaded"] == 1
    assert list(cache.media_dir.iterdir()) == [path]

def test_download_existing_file_needs_no_network(cache: Cache):
    cache.media_path(IMAGE_URL).write_bytes(b"old")

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("geen netwerk verwacht")

    fetcher = _fetcher(cache, handler)
    assert fetcher.download(IMAGE_URL, "commons").read_bytes() == b"old"
    assert fetcher.stats["cached"] == 1

def test_download_failure_keeps_old_file(cache: Cache, sleeps: list[float]):
    cache.media_path(IMAGE_URL).write_bytes(b"old")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    fetcher = _fetcher(cache, handler, refresh = True)
    path = fetcher.download(IMAGE_URL, "commons")
    assert path.read_bytes() == b"old"
    assert fetcher.stats["failed"] == 1
    assert list(cache.media_dir.iterdir()) == [path]

def test_download_failure_without_file_returns_none(cache: Cache, sleeps: list[float]):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request = request)

    fetcher = _fetcher(cache, handler)
    assert fetcher.download(IMAGE_URL, "commons") is None
    assert not cache.has_media(IMAGE_URL)
    assert list(cache.media_dir.iterdir()) == []

def test_delay_between_requests_to_same_host(cache: Cache):
    times: dict[str, list[float]] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        times.setdefault(request.url.host, []).append(time.monotonic())
        return httpx.Response(200, json = {})

    fetcher = _fetcher(cache, handler, delay_seconds = 0.05)
    fetcher.get("https://a.example/1", "test")
    fetcher.get("https://b.example/1", "test")
    fetcher.get("https://a.example/2", "test")
    fetcher.get("https://a.example/3", "test")
    first, second, third = times["a.example"]
    assert second - first >= 0.05
    assert third - second >= 0.05
    assert times["b.example"][0] - first < 0.05
