"""Source adapters and the registry that picks the right adapter for a URI."""
from siboga.config import Config
from siboga.sources.archief_amsterdam import ArchiefAmsterdamAdapter
from siboga.sources.base import SourceAdapter
from siboga.sources.commons import CommonsAdapter
from siboga.sources.gbif import GbifAdapter
from siboga.sources.wikidata import WikidataAdapter

class Registry:
    def __init__(self, adapters: list[SourceAdapter]):
        self.adapters = adapters

    def adapter_for(self, uri: str) -> SourceAdapter | None:
        for adapter in self.adapters:
            if adapter.matches(uri):
                return adapter
        return None

def build_registry(config: Config) -> Registry:
    return Registry([
        WikidataAdapter(image_width = config.image_width),
        CommonsAdapter(image_width = config.image_width),
        GbifAdapter(image_width = config.image_width),
        ArchiefAmsterdamAdapter(image_width = config.image_width)
    ])
