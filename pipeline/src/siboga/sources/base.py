from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import random

from siboga.models import SourceData

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

@dataclass(frozen = True)
class RateLimit:
    """How politely the fetcher treats a source; an adapter can set a stricter one.

    If the server sends a Retry-After, that always wins (up to max_backoff_seconds):
    Wikimedia explicitly asks for this instead of a fixed wait.
    """
    backoff_base_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    max_retries: int = 3
    min_interval_seconds: float = 0.2
    retry_after_seconds: float = 5.0
    retry_statuses: frozenset[int] = field(default_factory = lambda: frozenset({429, 500, 502, 503, 504}))

    def backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter, so retries don't happen in lockstep."""
        wait = self.backoff_base_seconds * (2 ** attempt)
        return min(wait, self.max_backoff_seconds) * random.uniform(0.8, 1.0)

    def retry_delay(
        self,
        status: int,
        retry_after: float | None,
        attempt: int
    ) -> float:
        """Wait before a retry after status; retry_after is the Retry-After in seconds."""
        if retry_after is not None:
            return min(retry_after, self.max_backoff_seconds)
        if status == 429:
            return min(self.retry_after_seconds, self.max_backoff_seconds)
        return self.backoff(attempt)

class SourceAdapter:
    """Base for one kind of source.

    fetch() runs only in the `fetch` step and may access the internet, through the fetcher.
    normalize() runs only in the `build` step and reads exclusively from the cache.
    rate_limit says how often and how long the fetcher retries for this adapter.
    """
    name: str = ""
    rate_limit: RateLimit = RateLimit()

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        raise NotImplementedError

    def matches(self, uri: str) -> bool:
        raise NotImplementedError

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        raise NotImplementedError

# For Wikidata and Commons: Wikimedia wants serial, unhurried requests that respect Retry-After.
WIKIMEDIA_RATE_LIMIT = RateLimit(
    max_retries = 5,
    min_interval_seconds = 1.0,
    retry_after_seconds = 10.0
)