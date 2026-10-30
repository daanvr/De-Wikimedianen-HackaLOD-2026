from pathlib import Path
import json

import pytest

from siboga.models import CachedResponse, SourceData, SourceRef
from siboga.sources.nta import NtaAdapter, person_iri
from siboga.sources.wikidata import WikidataAdapter, entity_url

ANNA_IRI = "http://data.bibliotheken.nl/id/thes/p072591218"
FIXTURES = Path(__file__).parent / "fixtures" / "sources"
WIKIDATA_URI = "https://www.wikidata.org/wiki/Q1"

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
            content_type = "application/ld+json",
            fetched_at = "2026-10-30T12:00:00Z",
            status = 200,
            url = url
        )

    def get_json(self, url: str) -> dict | list | None:
        response = self.get(url)
        return response.json() if response else None

class FakeFetcher:
    """Fetcher that serves responses from a dict and records what was requested."""
    def __init__(self, responses: dict[str, object]):
        self.downloads: list[str] = []
        self.requests: list[tuple[str, str, dict | None]] = []
        self.responses = responses

    def download(
        self,
        url: str,
        adapter: str
    ) -> Path | None:
        self.downloads.append(url)
        return None

    def get_json(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> dict | list | None:
        self.requests.append((url, adapter, headers))
        return self.responses.get(url)

def _anna() -> list:
    return json.loads((FIXTURES / "nta_p072591218.json").read_text())

def _entity(claims: dict[str, list[dict]] | None = None, label: str | None = None) -> dict:
    labels = {"nl": {"language": "nl", "value": label}} if label else {}
    return {"entities": {"Q1": {"claims": claims or {}, "descriptions": {}, "id": "Q1", "labels": labels}}}

def _nta_statement(value: str, rank: str = "normal") -> dict:
    return {"mainsnak": {"datavalue": {"value": value}, "snaktype": "value"}, "rank": rank}

@pytest.mark.parametrize("uri", [
    "http://data.bibliotheken.nl/id/thes/p072591218",
    "https://data.bibliotheken.nl/id/thes/p072591218",
    "http://data.bibliotheken.nl/id/thes/p14329069x"
])
def test_matches_person_uris(uri: str):
    assert NtaAdapter().matches(uri)

@pytest.mark.parametrize("uri", [
    "http://data.bibliotheken.nl/id/nbt/p037447890",
    "http://data.bibliotheken.nl/id/thes/p0725912",
    "https://www.wikidata.org/wiki/Q1940785"
])
def test_does_not_match_other_uris(uri: str):
    assert not NtaAdapter().matches(uri)

def test_person_iri_is_canonical():
    assert person_iri("https://data.bibliotheken.nl/id/thes/p14329069x") == "http://data.bibliotheken.nl/id/thes/p14329069X"

def test_fetch_is_one_json_ld_request():
    fetcher = FakeFetcher({ANNA_IRI: _anna()})
    NtaAdapter().fetch(ANNA_IRI, fetcher)
    assert fetcher.requests == [(ANNA_IRI, "nta", {"Accept": "application/ld+json"})]
    assert fetcher.downloads == []

def test_normalize_anna_weber():
    source = NtaAdapter().normalize(ANNA_IRI, FakeCache({ANNA_IRI: _anna()}))
    assert source.label == "Anna Antoinette Weber-van Bosse"
    assert source.description.startswith("biologe (m.n. algen en wieren")
    assert source.image is None
    assert source.fields["birth_date"] == ["1852"]
    assert source.fields["death_date"] == ["1942"]
    assert source.fields["alternate_name"] == ["Bosse, Anna Antoinette van", "Bosse, Anna Weber van-"]
    works = source.fields["work"]
    assert "Een jaar aan boord H.M. Siboga" in works
    assert "Liste des algues du Siboga" in works
    assert len(works) == len(set(works))
    # Books about her or that she only contributed to are not her works.
    assert not any("Jubileumdeel" in work or "kolonie" in work for work in works)

def test_normalize_skips_invalid_dates():
    node = {
        "@id": ANNA_IRI,
        "http://schema.org/birthDate": [{"@value": "ca. 1850"}],
        "http://schema.org/name": [{"@value": "Iemand"}]
    }
    source = NtaAdapter().normalize(ANNA_IRI, FakeCache({ANNA_IRI: [node]}))
    assert source.label == "Iemand"
    assert source.fields == {}

def test_normalize_without_cache_returns_none():
    assert NtaAdapter().normalize(ANNA_IRI, FakeCache({})) is None

def test_fill_from_only_fills_gaps_and_records_the_source():
    nta = SourceRef(name = "nta", uri = ANNA_IRI)
    source = SourceData(label = "Wikidata", fields = {"birth_date": ["1852-03-27"], "occupation": []})
    source.fill_from(SourceData(
        description = "Uit de NTA",
        fields = {"birth_date": ["1852"], "occupation": ["biologe"], "work": ["Een boek"]},
        label = "NTA"
    ), nta)
    assert source.label == "Wikidata"
    assert source.description == "Uit de NTA"
    assert source.fields == {"birth_date": ["1852-03-27"], "occupation": ["biologe"], "work": ["Een boek"]}
    assert source.linked_sources == [nta]
    assert source.source_of("label", "wikidata") == "wikidata"
    assert source.source_of("description", "wikidata") == "nta"
    assert source.source_of_field("birth_date", "wikidata") == "wikidata"
    assert source.source_of_field("occupation", "wikidata") == "nta"
    assert source.source_of_field("work", "wikidata") == "nta"

def test_wikidata_fetches_linked_nta_one_hop():
    entity = _entity({"P1006": [_nta_statement("072591218")]})
    fetcher = FakeFetcher({entity_url("Q1"): entity, ANNA_IRI: _anna()})
    WikidataAdapter(image_width = 100, linked_adapters = [NtaAdapter()]).fetch(WIKIDATA_URI, fetcher)
    assert [(url, adapter) for url, adapter, _ in fetcher.requests] == [
        (entity_url("Q1"), "wikidata"),
        (ANNA_IRI, "nta")
    ]

def test_wikidata_without_linked_adapters_ignores_nta():
    entity = _entity({"P1006": [_nta_statement("072591218")]})
    fetcher = FakeFetcher({entity_url("Q1"): entity})
    WikidataAdapter(image_width = 100).fetch(WIKIDATA_URI, fetcher)
    assert [url for url, _, _ in fetcher.requests] == [entity_url("Q1")]

def test_wikidata_follows_only_best_nta_statement():
    entity = _entity({"P1006": [_nta_statement("111111111"), _nta_statement("072591218", rank = "preferred")]})
    fetcher = FakeFetcher({entity_url("Q1"): entity})
    WikidataAdapter(image_width = 100, linked_adapters = [NtaAdapter()]).fetch(WIKIDATA_URI, fetcher)
    assert [url for url, _, _ in fetcher.requests] == [entity_url("Q1"), ANNA_IRI]

def test_wikidata_normalize_fills_gaps_from_nta():
    entity = _entity({"P1006": [_nta_statement("072591218")]}, label = "Anna Weber-van Bosse")
    cache = FakeCache({entity_url("Q1"): entity, ANNA_IRI: _anna()})
    source = WikidataAdapter(image_width = 100, linked_adapters = [NtaAdapter()]).normalize(WIKIDATA_URI, cache)
    assert source.label == "Anna Weber-van Bosse"
    assert source.description.startswith("biologe")
    assert "Een jaar aan boord H.M. Siboga" in source.fields["work"]
    assert source.linked_sources == [SourceRef(name = "nta", uri = ANNA_IRI)]
    assert source.source_of("label", "wikidata") == "wikidata"
    assert source.source_of("description", "wikidata") == "nta"
    assert source.source_of_field("work", "wikidata") == "nta"

def test_wikidata_normalize_without_nta_in_cache():
    entity = _entity({"P1006": [_nta_statement("072591218")]}, label = "Anna")
    cache = FakeCache({entity_url("Q1"): entity})
    source = WikidataAdapter(image_width = 100, linked_adapters = [NtaAdapter()]).normalize(WIKIDATA_URI, cache)
    assert source.label == "Anna"
    assert "work" not in source.fields