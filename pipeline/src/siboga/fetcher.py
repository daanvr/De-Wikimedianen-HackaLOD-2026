"""Haalt URL's op via de cache: beleefd, met herpogingen, en zonder ooit een goede kopie kwijt te raken."""
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
import os
import tempfile
import time

from loguru import logger
import httpx

from siboga.cache import Cache
from siboga.models import CachedResponse

# Wachttijd vóór de eerste en de tweede herpoging.
_BACKOFF_SECONDS = (1.0, 3.0)
_MAX_RETRY_AFTER_SECONDS = 10.0
_RETRY_STATUSES = {429, 500, 502, 503, 504}

class Fetcher:
    """Doet alle HTTP-verzoeken van de pipeline en schrijft elk antwoord in de cache."""
    def __init__(
        self,
        cache: Cache,
        user_agent: str,
        delay_seconds: float = 0.2,
        max_age_days: int = 30,
        refresh: bool = False,
        timeout_seconds: float = 30.0,
        client: httpx.Client | None = None
    ):
        self.cache = cache
        self.delay_seconds = delay_seconds
        self.max_age_days = max_age_days
        self.refresh = refresh
        self.stats: dict[str, int] = {
            "cached": 0,
            "downloaded": 0,
            "failed": 0,
            "fetched": 0
        }
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self._client = client or httpx.Client()
        self._last_request: dict[str, float] = {}
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def download(self, url: str, adapter: str) -> Path | None:
        """Downloadt url naar cache.media_path(url). Een bestaand bestand blijft staan als het misgaat."""
        path = self.cache.media_path(url)
        if path.is_file() and not self.refresh:
            self.stats["cached"] += 1
            return path
        response = self._request(url, adapter)
        if response.is_ok() and response.body:
            self._write_atomic(path, response.body)
            response.body = None
            self.cache.put(response)
            self.stats["downloaded"] += 1
            logger.debug(f"Gedownload: {url} -> {path.name}")
            return path
        response.body = None
        self.cache.put(response)
        self.stats["failed"] += 1
        if path.is_file():
            logger.warning(f"Download mislukt (status {response.status}), oude kopie blijft: {url}")
            return path
        logger.warning(f"Download mislukt (status {response.status}): {url}")
        return None

    def get(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> CachedResponse | None:
        """Geeft het antwoord voor url, uit de cache als dat kan. Gooit nooit een fout bij netwerkproblemen."""
        cached = self.cache.get(url)
        has_good_copy = cached is not None and cached.is_ok()
        if has_good_copy and not self.refresh and self._is_fresh(cached):
            self.stats["cached"] += 1
            return cached
        response = self._request(url, adapter, headers)
        self.cache.put(response)
        if response.is_ok():
            self.stats["fetched"] += 1
            logger.debug(f"Opgehaald: {url}")
            return response
        self.stats["failed"] += 1
        if has_good_copy:
            logger.warning(f"Ophalen mislukt (status {response.status}), oude kopie van {cached.fetched_at} gebruikt: {url}")
            return cached
        logger.warning(f"Ophalen mislukt (status {response.status}): {url}")
        return response

    def get_json(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> dict | list | None:
        response = self.get(url, adapter, headers)
        return response.json() if response else None

    def _is_fresh(self, response: CachedResponse) -> bool:
        try:
            fetched_at = datetime.fromisoformat(response.fetched_at)
        except ValueError:
            return False
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo = UTC)
        return datetime.now(UTC) - fetched_at < timedelta(days = self.max_age_days)

    def _request(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> CachedResponse:
        """Eén GET met maximaal twee herpogingen. Status 0 betekent een netwerkfout."""
        request_headers = {**(headers or {}), "User-Agent": self.user_agent}
        for attempt in range(len(_BACKOFF_SECONDS) + 1):
            is_last = attempt == len(_BACKOFF_SECONDS)
            self._wait(url)
            try:
                response = self._client.get(
                    url,
                    headers = request_headers,
                    follow_redirects = True,
                    timeout = self.timeout_seconds
                )
            except httpx.TransportError as error:
                logger.debug(f"Netwerkfout bij {url}: {error!r}")
                if is_last:
                    return _failure(url, adapter)
                time.sleep(_BACKOFF_SECONDS[attempt])
                continue
            except (httpx.HTTPError, httpx.InvalidURL) as error:
                logger.debug(f"Fout bij {url}: {error!r}")
                return _failure(url, adapter)
            if response.status_code in _RETRY_STATUSES and not is_last:
                logger.debug(f"Status {response.status_code} bij {url}, nieuwe poging")
                time.sleep(_retry_delay(response, _BACKOFF_SECONDS[attempt]))
                continue
            return CachedResponse(
                adapter = adapter,
                body = response.content,
                content_type = response.headers.get("content-type"),
                fetched_at = _now(),
                status = response.status_code,
                url = url
            )
        return _failure(url, adapter)

    def _wait(self, url: str) -> None:
        """Wacht tot er minstens delay_seconds voorbij is sinds het vorige verzoek aan dezelfde host."""
        host = urlsplit(url).netloc
        last = self._last_request.get(host)
        if last is not None:
            remaining = self.delay_seconds - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def _write_atomic(self, path: Path, data: bytes) -> None:
        """Schrijft eerst naar een tijdelijk bestand en zet het dan in één keer op zijn plek."""
        descriptor, temp_name = tempfile.mkstemp(dir = path.parent, prefix = ".download-")
        try:
            with os.fdopen(descriptor, "wb") as file:
                file.write(data)
            # mkstemp maakt het bestand alleen voor de eigenaar leesbaar.
            os.chmod(temp_name, 0o644)
            os.replace(temp_name, path)
        except BaseException:
            Path(temp_name).unlink(missing_ok = True)
            raise

def _failure(url: str, adapter: str) -> CachedResponse:
    return CachedResponse(
        adapter = adapter,
        body = None,
        content_type = None,
        fetched_at = _now(),
        status = 0,
        url = url
    )

def _now() -> str:
    return datetime.now(UTC).isoformat(timespec = "seconds")

def _retry_delay(response: httpx.Response, default: float) -> float:
    """Retry-After in seconden als de server die geeft, nooit langer dan het maximum."""
    try:
        seconds = float(response.headers.get("retry-after", default))
    except ValueError:
        seconds = default
    return max(0.0, min(seconds, _MAX_RETRY_AFTER_SECONDS))
