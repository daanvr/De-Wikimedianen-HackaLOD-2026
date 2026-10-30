from __future__ import annotations

from typing import TYPE_CHECKING

from siboga.models import SourceData

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

class SourceAdapter:
    """Basis voor één soort bron.

    fetch() draait alleen in de stap `fetch` en mag het internet op, via de fetcher.
    normalize() draait alleen in de stap `build` en leest uitsluitend uit de cache.
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
