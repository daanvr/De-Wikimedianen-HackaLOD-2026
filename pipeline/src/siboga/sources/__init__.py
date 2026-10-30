"""Source adapters and the registry that picks the right adapter for a URI."""
from siboga.config import Config
from siboga.sources.archief_amsterdam import ArchiefAmsterdamAdapter
from siboga.sources.base import RateLimit, SourceAdapter
from siboga.sources.commons import CommonsAdapter
from siboga.sources.gbif import GbifAdapter
from siboga.sources.nta import NtaAdapter
from siboga.sources.wikidata import WikidataAdapter

class Registry:
    def __init__(self, adapters: list[SourceAdapter]):
        self.adapters = adapters

    def adapter_for(self, uri: str) -> SourceAdapter | None:
        for adapter in self.adapters:
            if adapter.matches(uri):
                return adapter
        return None

    def rate_limits(self) -> dict[str, RateLimit]:
        return {adapter.name: adapter.rate_limit for adapter in self.adapters}

def build_registry(config: Config) -> Registry:
    nta = NtaAdapter()
    return Registry([
        # Wikidata follows its linked sources one hop; those adapters never follow links themselves.
        WikidataAdapter(image_width = config.image_width, linked_adapters = [nta]),
        CommonsAdapter(image_width = config.image_width),
        GbifAdapter(image_width = config.image_width),
        ArchiefAmsterdamAdapter(image_width = config.image_width),
        nta
    ])
