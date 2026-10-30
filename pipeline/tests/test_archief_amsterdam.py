from pathlib import Path
import copy
import hashlib
import json

from siboga.models import CachedResponse, ImageInfo
from siboga.sources.archief_amsterdam import ArchiefAmsterdamAdapter

FIXTURES = Path(__file__).parent / "fixtures" / "sources"
PERSON_IRI = "https://id.archief.amsterdam/99e87e40-953e-2bb2-e053-b784100a6a2e"
RECORD_IRI = "https://id.archief.amsterdam/37a9193c-31fa-4a34-a239-3f6928cb9094"
RECORD_URI = "https://beta.archief.amsterdam/detail/37a9193c-31fa-4a34-a239-3f6928cb9094"
RIGHTS_IRI = "https://id.archief.amsterdam/resources/records/37a9193c-31fa-4a34-a239-3f6928cb9094/accessibility_and_rights"
WIDTH = 1600

class FakeCache:
    """In-memory cache: URL to JSON response."""
    def __init__(self, responses: dict[str, object]):
        self.responses = responses

    def get(self, url: str) -> CachedResponse | None:
        if url not in self.responses:
            return None
        return CachedResponse(
            adapter = "archief_amsterdam",
            body = json.dumps(self.responses[url]).encode(),
            content_type = "application/ld+json",
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
        return Path("/media") / hashlib.sha1(url.encode()).hexdigest()

class FakeFetcher:
    """Fetcher that serves responses from a dict and records what was requested, with headers."""
    def __init__(self, responses: dict[str, object]):
        self.cache = FakeCache(responses)
        self.downloads: list[str] = []
        self.requests: list[tuple[str, dict | None]] = []

    def download(
        self,
        url: str,
        adapter: str
    ) -> Path | None:
        self.downloads.append(url)
        return self.cache.media_path(url)

    def get(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> CachedResponse | None:
        self.requests.append((url, headers))
        return self.cache.get(url)

    def get_json(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> dict | list | None:
        response = self.get(url, adapter, headers)
        return response.json() if response else None

def _licensed_responses() -> dict[str, object]:
    """The real record, plus a license such as an image record might have."""
    responses = _responses()
    record = copy.deepcopy(responses[RECORD_IRI])
    for node in record["@graph"]:
        if node["@id"] == RIGHTS_IRI:
            node["http://schema.org/license"] = {"@id": "http://creativecommons.org/publicdomain/zero/1.0/"}
    responses[RECORD_IRI] = record
    return responses

def _responses() -> dict[str, object]:
    return {
        PERSON_IRI: json.loads((FIXTURES / "archief_amsterdam_99e87e40.json").read_text()),
        RECORD_IRI: json.loads((FIXTURES / "archief_amsterdam_37a9193c.json").read_text())
    }

def test_fetch_record_and_persons():
    fetcher = FakeFetcher(_responses())
    ArchiefAmsterdamAdapter(image_width = WIDTH).fetch(RECORD_URI, fetcher)
    accept = {"Accept": "application/ld+json"}
    assert fetcher.requests == [(RECORD_IRI, accept), (PERSON_IRI, accept)]
    assert fetcher.downloads == []

def test_fetch_downloads_licensed_scan():
    fetcher = FakeFetcher(_licensed_responses())
    ArchiefAmsterdamAdapter(image_width = WIDTH).fetch(RECORD_URI, fetcher)
    assert fetcher.downloads == ["https://id.archief.amsterdam/resources/iiif/3/bc744236-a210-4c76-8edc-64c996d6b43d/full/1600,/0/default.jpg"]

def test_matches():
    adapter = ArchiefAmsterdamAdapter(image_width = WIDTH)
    assert adapter.matches(RECORD_URI)
    assert adapter.matches("https://beta.archief.amsterdam/zoeken/detail/37a9193c-31fa-4a34-a239-3f6928cb9094")
    assert adapter.matches("https://archief.amsterdam/detail/37a9193c-31fa-4a34-a239-3f6928cb9094")
    assert not adapter.matches("https://beta.archief.amsterdam/detail/niet-een-uuid")
    assert not adapter.matches("https://www.gbif.org/taxon/94X5L")

def test_normalize_record():
    data = ArchiefAmsterdamAdapter(image_width = WIDTH).normalize(RECORD_URI, FakeCache(_responses()))
    assert data.label == "Opname, 1882, Anna Weber"
    assert data.fields == {
        "archive": ["5268, Archief van de Gemeenteziekenhuizen"],
        "created": ["1882"],
        "point_in_time": ["1882"]
    }
    assert data.description.startswith("Opname (Patiëntenregisters). ")
    assert "Instelling: Binnengasthuis." in data.description
    assert "Afdeling: Vrouwen Zieken." in data.description
    assert "Geregistreerde: Anna Weber (geboren 22-08-1805)." in data.description
    assert data.description.endswith("Archief: 5268, Archief van de Gemeenteziekenhuizen.")
    assert data.image is None
    assert data.coordinates is None

def test_normalize_full_date():
    responses = _responses()
    record = copy.deepcopy(responses[RECORD_IRI])
    for node in record["@graph"]:
        if node["@id"] == RECORD_IRI:
            node["rico:normalizedDateValue"]["@value"] = "1882-03-14"
    responses[RECORD_IRI] = record
    data = ArchiefAmsterdamAdapter(image_width = WIDTH).normalize(RECORD_URI, FakeCache(responses))
    assert data.fields["created"] == ["1882-03-14"]
    assert data.fields["point_in_time"] == ["1882-03-14"]

def test_normalize_licensed_scan():
    data = ArchiefAmsterdamAdapter(image_width = WIDTH).normalize(RECORD_URI, FakeCache(_licensed_responses()))
    assert data.image == ImageInfo(
        credit = "Stadsarchief Amsterdam",
        download_url = "https://id.archief.amsterdam/resources/iiif/3/bc744236-a210-4c76-8edc-64c996d6b43d/full/1600,/0/default.jpg",
        license = "CC0 1.0",
        license_url = "https://creativecommons.org/publicdomain/zero/1.0/",
        source_url = RECORD_URI
    )

def test_normalize_missing_cache():
    assert ArchiefAmsterdamAdapter(image_width = WIDTH).normalize(RECORD_URI, FakeCache({})) is None

def test_normalize_without_date():
    responses = _responses()
    record = copy.deepcopy(responses[RECORD_IRI])
    for node in record["@graph"]:
        if node["@id"] == RECORD_IRI:
            del node["rico:normalizedDateValue"]
    responses[RECORD_IRI] = record
    data = ArchiefAmsterdamAdapter(image_width = WIDTH).normalize(RECORD_URI, FakeCache(responses))
    assert data.fields == {"archive": ["5268, Archief van de Gemeenteziekenhuizen"]}

def test_normalize_without_person_in_cache():
    responses = _responses()
    del responses[PERSON_IRI]
    data = ArchiefAmsterdamAdapter(image_width = WIDTH).normalize(RECORD_URI, FakeCache(responses))
    assert "Geregistreerde" not in data.description
    assert data.label == "Opname, 1882, Anna Weber"
