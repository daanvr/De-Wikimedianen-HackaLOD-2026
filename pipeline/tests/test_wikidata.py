from pathlib import Path
import json

import pytest

from siboga.models import CachedResponse, Coordinates
from siboga.sources.commons import imageinfo_url
from siboga.sources.wikidata import WikidataAdapter, entity_url, labels_urls

ANNA_IMAGE = "Anna Antoinette Weber-van Bosse.jpg"
ANNA_URI = "https://www.wikidata.org/wiki/Q1940785"
BOOK_URI = "https://www.wikidata.org/wiki/Q124560811"
FIXTURES = Path(__file__).parent / "fixtures" / "sources"
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

def _entity(
    claims: dict[str, list[dict]] | None = None,
    descriptions: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
    qid: str = "Q1"
) -> dict:
    def texts(values: dict[str, str] | None) -> dict:
        return {language: {"language": language, "value": value} for language, value in (values or {}).items()}

    return {"entities": {qid: {
        "claims": claims or {},
        "descriptions": texts(descriptions),
        "id": qid,
        "labels": texts(labels)
    }}}

def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())

def _item(qid: str) -> dict:
    return {"entity-type": "item", "id": qid, "numeric-id": int(qid[1:])}

def _labels(labels: dict[str, dict[str, str] | None]) -> dict:
    """wbgetentities response; None stands for an item that does not exist."""
    entities = {}
    for qid, values in labels.items():
        if values is None:
            entities[qid] = {"id": qid, "missing": ""}
        else:
            entities[qid] = {
                "id": qid,
                "labels": {language: {"language": language, "value": value} for language, value in values.items()},
                "type": "item"
            }
    return {"entities": entities, "success": 1}

def _normalize(
    response: dict,
    uri: str = "https://www.wikidata.org/wiki/Q1",
    labels: dict[str, dict[str, str] | None] | None = None
):
    """Normalizes from a cache holding the entity and, under the URL for exactly these Q-numbers, the labels.

    If the adapter asks for labels of other items, it won't find them; so this also tests which items it requests.
    """
    responses = {entity_url("Q1"): response}
    if labels:
        for url in labels_urls(list(labels)):
            responses[url] = _labels(labels)
    return WikidataAdapter(image_width = WIDTH).normalize(uri, FakeCache(responses))

def _statement(
    value: object,
    rank: str = "normal",
    snaktype: str = "value"
) -> dict:
    mainsnak = {"snaktype": snaktype}
    if snaktype == "value":
        mainsnak["datavalue"] = {"value": value}
    return {"mainsnak": mainsnak, "rank": rank}

def _time(text: str, precision: int) -> dict:
    return {"time": text, "precision": precision}

def test_fetch_gets_entity_labels_and_image():
    entity = _fixture("wikidata_Q1940785.json")
    imageinfo = _fixture("commons_anna_weber.json")
    fetcher = FakeFetcher({
        entity_url("Q1940785"): entity,
        imageinfo_url(ANNA_IMAGE, WIDTH): imageinfo
    })
    WikidataAdapter(image_width = WIDTH).fetch(ANNA_URI, fetcher)
    labels_url = (
        "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels"
        "&languages=nl%7Cen%7Cmul&ids=Q727%7CQ765914%7CQ864503%7CQ2083925%7CQ2374149%7CQ2487799%7CQ12358881%7CQ98544732"
    )
    assert fetcher.requests == [
        ("https://www.wikidata.org/wiki/Special:EntityData/Q1940785.json", "wikidata"),
        (labels_url, "wikidata"),
        (imageinfo_url(ANNA_IMAGE, WIDTH), "wikidata")
    ]
    thumb = imageinfo["query"]["pages"][0]["imageinfo"][0]["thumburl"]
    assert fetcher.downloads == [(thumb, "wikidata")]

def test_fetch_without_image():
    fetcher = FakeFetcher({entity_url("Q1"): _entity(labels = {"nl": "Iets"})})
    WikidataAdapter(image_width = WIDTH).fetch("https://www.wikidata.org/entity/Q1", fetcher)
    assert len(fetcher.requests) == 1
    assert fetcher.downloads == []

def test_fetch_gets_labels_in_chunks():
    claims = {"P710": [_statement(_item(f"Q{number}")) for number in range(120, 0, -1)]}
    fetcher = FakeFetcher({entity_url("Q1"): _entity(claims = claims)})
    WikidataAdapter(image_width = WIDTH).fetch("https://www.wikidata.org/wiki/Q1", fetcher)
    assert [url for url, _ in fetcher.requests[1:]] == labels_urls([f"Q{number}" for number in range(1, 121)])
    assert len(fetcher.requests) == 4

def test_labels_urls_are_sorted_chunked_and_stable():
    qids = [f"Q{number}" for number in range(1, 121)]
    urls = labels_urls(list(reversed(qids)) + ["Q5", "Q7"])
    assert urls == labels_urls(qids)
    assert len(urls) == 3
    assert urls[0].endswith("&ids=" + "%7C".join(qids[:50]))
    assert urls[1].endswith("&ids=" + "%7C".join(qids[50:100]))
    assert urls[2].endswith("&ids=" + "%7C".join(qids[100:]))
    assert labels_urls(["Q10", "Q9"])[0].endswith("&ids=Q9%7CQ10")
    assert labels_urls([]) == []

@pytest.mark.parametrize("uri, expected", [
    ("https://www.wikidata.org/wiki/Q1940785", True),
    ("http://www.wikidata.org/entity/Q4201627", True),
    ("https://wikidata.org/wiki/Q123196833", True),
    ("https://www.wikidata.org/wiki/Property:P18", False),
    ("https://www.wikidata.org/wiki/Q12abc", False),
    ("https://commons.wikimedia.org/wiki/File:Foo.jpg", False)
])
def test_matches(uri: str, expected: bool):
    assert WikidataAdapter(image_width = WIDTH).matches(uri) is expected

def test_normalize_full_text_url():
    english = _statement("https://example.org/book-en")
    english["qualifiers"] = {"P407": [{"datavalue": {"value": {"id": "Q1860"}}}]}
    dutch = _statement("https://www.delpher.nl/nl/boeken/view?identifier=1")
    dutch["qualifiers"] = {"P407": [{"datavalue": {"value": {"id": "Q7411"}}}]}
    # A Dutch text goes first, whatever the order on Wikidata.
    claims = {"P953": [english, dutch]}
    assert _normalize(_entity(claims = claims)).full_text_url == "https://www.delpher.nl/nl/boeken/view?identifier=1"
    # Without a language the first one counts; anything that is no web address is skipped.
    claims = {"P953": [_statement("not a url"), _statement("https://a.org"), _statement("https://b.org")]}
    assert _normalize(_entity(claims = claims)).full_text_url == "https://a.org"
    assert _normalize(_entity()).full_text_url is None

def test_normalize_coordinates():
    claims = {"P625": [_statement({"latitude": -4.52, "longitude": 129.9, "globe": "http://www.wikidata.org/entity/Q2"})]}
    assert _normalize(_entity(claims = claims)).coordinates == Coordinates(lat = -4.52, lon = 129.9)
    claims = {"P625": [_statement({"latitude": 1.0, "longitude": 2.0, "globe": "http://www.wikidata.org/entity/Q405"})]}
    assert _normalize(_entity(claims = claims)).coordinates is None

@pytest.mark.parametrize("value, expected", [
    (_time("+1899-03-07T00:00:00Z", 11), "1899-03-07"),
    (_time("+1899-03-00T00:00:00Z", 10), "1899-03"),
    (_time("+1899-00-00T00:00:00Z", 9), "1899"),
    (_time("+1850-00-00T00:00:00Z", 7), "1850"),
    (_time("-0500-00-00T00:00:00Z", 9), "-0500"),
    (_time("+1899-03-07T12:30:00Z", 13), "1899-03-07")
])
def test_normalize_date_precision(value: dict, expected: str):
    assert _normalize(_entity(claims = {"P585": [_statement(value)]})).fields == {"point_in_time": [expected]}

def test_normalize_item_labels():
    claims = {
        "P106": [_statement(_item("Q3")), _statement(_item("Q2")), _statement(_item("Q4")), _statement(_item("Q5"))],
        "P19": [_statement(_item("Q2"))],
        "P27": [_statement(_item("Q6"))]
    }
    labels = {
        "Q2": {"en": "Amsterdam", "nl": "Amsterdam (stad)"},
        "Q3": {"en": "biologist", "mul": "X"},
        "Q4": {"de": "Botaniker"},
        "Q5": None
    }
    data = _normalize(_entity(claims = claims), labels = labels)
    assert data.fields == {"birth_place": ["Amsterdam (stad)"], "occupation": ["biologist", "Amsterdam (stad)"]}

def test_normalize_item_label_falls_back_to_mul():
    data = _normalize(_entity(claims = {"P17": [_statement(_item("Q2"))]}), labels = {"Q2": {"mul": "Indonesia"}})
    assert data.fields == {"country": ["Indonesia"]}

def test_normalize_items_without_labels_in_cache():
    claims = {"P50": [_statement(_item("Q2"))], "P2093": [_statement("J.G. de Man")]}
    assert _normalize(_entity(claims = claims)).fields == {"author": ["J.G. de Man"]}

def test_normalize_authors_and_author_name_strings():
    claims = {
        "P2093": [_statement("J.G. de Man"), _statement(""), _statement("A. Weber")],
        "P50": [_statement(_item("Q2")), _statement(_item("Q3"), rank = "deprecated")]
    }
    labels = {"Q2": {"nl": "A. Weber"}}
    assert _normalize(_entity(claims = claims), labels = labels).fields == {"author": ["A. Weber", "J.G. de Man"]}

def test_normalize_scientific_and_vernacular_names():
    claims = {
        "P1843": [
            _statement({"language": "en", "text": "sea fan"}),
            _statement({"language": "nl", "text": "zeewaaier"}),
            _statement({"language": "nl", "text": "hoornkoraal"})
        ],
        "P225": [_statement("Gorgonia")]
    }
    data = _normalize(_entity(claims = claims))
    assert data.fields == {"scientific_name": ["Gorgonia"], "vernacular_name": ["zeewaaier", "hoornkoraal"]}

def test_normalize_label_and_description_fallbacks():
    data = _normalize(_entity(descriptions = {"de": "Schiff", "en": "ship"}, labels = {"en": "Siboga", "mul": "X"}))
    assert data.label == "Siboga"
    assert data.description == "ship"
    data = _normalize(_entity(labels = {"mul": "Siboga", "fr": "Le Siboga"}))
    assert data.label == "Siboga"
    assert data.description is None

def test_normalize_prefers_preferred_rank_and_skips_deprecated():
    claims = {
        "P569": [
            _statement(_time("+1850-01-01T00:00:00Z", 11), rank = "deprecated"),
            _statement(_time("+1851-01-01T00:00:00Z", 11)),
            _statement(_time("+1852-03-27T00:00:00Z", 11), rank = "preferred")
        ],
        "P570": [
            _statement(None, snaktype = "somevalue"),
            _statement(_time("+1942-10-29T00:00:00Z", 11), rank = "deprecated")
        ],
        "P571": [
            _statement(_time("+1898-00-00T00:00:00Z", 9), rank = "deprecated"),
            _statement(_time("+1899-00-00T00:00:00Z", 9))
        ]
    }
    assert _normalize(_entity(claims = claims)).fields == {
        "birth_date": ["1852-03-27"],
        "created": ["1899"],
        "inception": ["1899"]
    }

def test_normalize_real_entity():
    entity = _fixture("wikidata_Q1940785.json")
    cache = FakeCache({
        entity_url("Q1940785"): entity,
        imageinfo_url(ANNA_IMAGE, WIDTH): _fixture("commons_anna_weber.json"),
        labels_urls(list(_fixture("wikidata_labels_Q1940785.json")["entities"]))[0]: _fixture("wikidata_labels_Q1940785.json")
    })
    data = WikidataAdapter(image_width = WIDTH).normalize(ANNA_URI, cache)
    assert data.label == "Anna Weber-van Bosse"
    assert data.description == "Nederlandse algoloog (1852-1942)"
    assert data.fields == {
        "birth_date": ["1852-03-27"],
        "birth_place": ["Amsterdam"],
        "death_date": ["1942-10-29"],
        "death_place": ["Eerbeek"],
        "occupation": [
            "bioloog",
            "botanicus",
            "algenkundige",
            "plantenverzamelaar",
            "wetenschappelijk verzamelaar",
            "mycoloog"
        ]
    }
    assert data.coordinates is None
    assert data.image.credit == "University of Amsterdam, Artis Library"
    assert data.image.license == "Public domain"
    assert data.image.source_url == "https://commons.wikimedia.org/wiki/File:Anna_Antoinette_Weber-van_Bosse.jpg"

def test_normalize_real_book():
    cache = FakeCache({
        entity_url("Q124560811"): _fixture("wikidata_Q124560811.json"),
        labels_urls(["Q1940785", "Q917031"])[0]: _fixture("wikidata_labels_Q124560811.json")
    })
    data = WikidataAdapter(image_width = WIDTH).normalize(BOOK_URI, cache)
    assert data.label == "Een jaar aan boord H.M. Siboga"
    assert data.fields == {
        "author": ["Anna Weber-van Bosse"],
        "publication_date": ["1904"],
        "publisher": ["Koninklijke Brill NV"]
    }
    assert data.image is None

def test_normalize_real_entity_without_image_in_cache():
    cache = FakeCache({entity_url("Q1940785"): _fixture("wikidata_Q1940785.json")})
    data = WikidataAdapter(image_width = WIDTH).normalize(ANNA_URI, cache)
    assert data.label == "Anna Weber-van Bosse"
    assert data.image is None
    assert data.fields == {"birth_date": ["1852-03-27"], "death_date": ["1942-10-29"]}

def test_normalize_redirected_entity():
    data = _normalize(_entity(labels = {"nl": "Doel"}, qid = "Q2"))
    assert data.label == "Doel"

def test_normalize_without_cache_returns_none():
    assert WikidataAdapter(image_width = WIDTH).normalize(ANNA_URI, FakeCache({})) is None
