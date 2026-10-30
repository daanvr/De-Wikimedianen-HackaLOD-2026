from __future__ import annotations

from typing import TYPE_CHECKING

from siboga.models import SourceData

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

class SourceAdapter:
    """Base for one kind of source.

    fetch() runs only in the `fetch` step and may access the internet, through the fetcher.
    normalize() runs only in the `build` step and reads exclusively from the cache.
    """
    name: str = ""

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
