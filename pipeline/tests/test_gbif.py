from pathlib import Path
import copy
import hashlib
import json

from siboga.models import CachedResponse, ImageInfo
from siboga.sources.gbif import GbifAdapter, license_name

FIXTURES = Path(__file__).parent / "fixtures" / "sources"
COL_INFO_URL = "https://api.checklistbank.org/dataset/3LXR/taxon/94X5L/info"
COL_OCCURRENCES_URL = "https://api.gbif.org/v1/occurrence/search?checklistKey=7ddf754f-d193-4cc9-b351-99906754a03b&taxonKey=94X5L&mediaType=StillImage&limit=20"
SPECIES_OCCURRENCES_URL = "https://api.gbif.org/v1/occurrence/search?taxonKey=9013523&mediaType=StillImage&limit=20"
SPECIES_URL = "https://api.gbif.org/v1/species/9013523"
SPECIES_VERNACULAR_URL = "https://api.gbif.org/v1/species/9013523/vernacularNames?limit=1000"
TAXON_URI = "https://www.gbif.org/taxon/94X5L"
WEBEROLEGRA_FIELDS = {
    "family": ["Lasiocampidae"],
    "order": ["Lepidoptera"],
    "parent_taxon": ["Weberolegra"],
    "scientific_name": ["Weberolegra weberi (Tams, 1929)"],
    "taxon_rank": ["soort"]
}
WIDTH = 1600

class FakeCache:
    """In-memory cache: URL to JSON response."""
    def __init__(self, responses: dict[str, object]):
        self.responses = responses

    def get(self, url: str) -> CachedResponse | None:
        if url not in self.responses:
            return None
        return CachedResponse(
            adapter = "gbif",
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
        return Path("/media") / hashlib.sha1(url.encode()).hexdigest()

class FakeFetcher:
    """Fetcher that serves responses from a dict and records what was requested."""
    def __init__(self, responses: dict[str, object]):
        self.cache = FakeCache(responses)
        self.downloads: list[str] = []
        self.requests: list[str] = []

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
        self.requests.append(url)
        return self.cache.get(url)

    def get_json(
        self,
        url: str,
        adapter: str,
        headers: dict[str, str] | None = None
    ) -> dict | list | None:
        response = self.get(url, adapter, headers)
        return response.json() if response else None

def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())

def _col_responses() -> dict[str, object]:
    return {
        COL_INFO_URL: _fixture("gbif_col_94X5L_info.json"),
        COL_OCCURRENCES_URL: _fixture("gbif_col_94X5L_occurrences.json")
    }

def _nhm_image() -> ImageInfo:
    md5 = hashlib.md5(b"https://data.nhm.ac.uk/media/36d1592b-d6a7-4ffc-a00a-aed4e040e2ed").hexdigest()
    return ImageInfo(
        credit = "The Trustees of the Natural History Museum, London",
        download_url = f"https://api.gbif.org/v1/image/cache/1600x/occurrence/1826325281/media/{md5}",
        license = "CC BY 4.0",
        license_url = "https://creativecommons.org/licenses/by/4.0/",
        source_url = "https://www.gbif.org/occurrence/1826325281"
    )

def test_fetch_downloads_licensed_image():
    responses = _col_responses()
    responses[COL_OCCURRENCES_URL] = _fixture("gbif_occurrences_with_image.json")
    fetcher = FakeFetcher(responses)
    GbifAdapter(image_width = WIDTH).fetch(TAXON_URI, fetcher)
    assert fetcher.requests == [COL_INFO_URL, COL_OCCURRENCES_URL]
    assert fetcher.downloads == [_nhm_image().download_url]

def test_fetch_species_without_image():
    fetcher = FakeFetcher({})
    GbifAdapter(image_width = WIDTH).fetch("https://www.gbif.org/species/9013523", fetcher)
    assert fetcher.requests == [SPECIES_URL, SPECIES_VERNACULAR_URL, SPECIES_OCCURRENCES_URL]
    assert fetcher.downloads == []

def test_license_name():
    assert license_name("http://creativecommons.org/licenses/by-nc/4.0/legalcode") == ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/")
    assert license_name("http://creativecommons.org/publicdomain/zero/1.0/legalcode") == ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")
    assert license_name("CC_BY_4_0") == ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")
    assert license_name("© alle rechten voorbehouden") is None
    assert license_name(None) is None

def test_matches():
    adapter = GbifAdapter(image_width = WIDTH)
    assert adapter.matches(TAXON_URI)
    assert adapter.matches("http://gbif.org/taxon/94X5L")
    assert adapter.matches("https://www.gbif.org/species/9013523")
    assert not adapter.matches("https://www.gbif.org/occurrence/1826325281")
    assert not adapter.matches("https://www.wikidata.org/wiki/Q1940785")

def test_normalize_col_taxon():
    data = GbifAdapter(image_width = WIDTH).normalize(TAXON_URI, FakeCache(_col_responses()))
    assert data.label == "Weberolegra weberi (Tams, 1929)"
    assert data.description == "Soort uit de familie Lasiocampidae (orde Lepidoptera)."
    assert data.image is None
    assert data.coordinates is None
    assert data.fields == WEBEROLEGRA_FIELDS

def test_normalize_missing_cache():
    assert GbifAdapter(image_width = WIDTH).normalize(TAXON_URI, FakeCache({})) is None

def test_normalize_picks_first_image_with_own_license():
    search = _fixture("gbif_occurrences_with_image.json")
    # Without a license on the image itself it doesn't count, even if the record has one.
    search["results"].reverse()
    responses = _col_responses()
    responses[COL_OCCURRENCES_URL] = search
    data = GbifAdapter(image_width = WIDTH).normalize(TAXON_URI, FakeCache(responses))
    assert data.image == _nhm_image()

def test_normalize_skips_image_without_license():
    search = _fixture("gbif_occurrences_with_image.json")
    search["results"] = search["results"][1:]
    responses = _col_responses()
    responses[COL_OCCURRENCES_URL] = search
    assert GbifAdapter(image_width = WIDTH).normalize(TAXON_URI, FakeCache(responses)).image is None

def test_normalize_col_parent_without_parent_id():
    responses = _col_responses()
    info = copy.deepcopy(responses[COL_INFO_URL])
    del info["usage"]["parentId"]
    info["classification"] = info["classification"][:-2]
    responses[COL_INFO_URL] = info
    data = GbifAdapter(image_width = WIDTH).normalize(TAXON_URI, FakeCache(responses))
    assert data.fields["parent_taxon"] == ["Lasiocampidae"]

def test_normalize_dutch_vernacular_name():
    responses = _col_responses()
    info = copy.deepcopy(responses[COL_INFO_URL])
    info["vernacularNames"] = [
        {"name": "Testmot", "language": "eng"},
        {"name": "testvlinder", "language": "nld"},
        {"name": "voorkeursvlinder", "language": "nl", "preferred": True},
        {"name": "testvlinder", "language": "nld"}
    ]
    responses[COL_INFO_URL] = info
    data = GbifAdapter(image_width = WIDTH).normalize(TAXON_URI, FakeCache(responses))
    assert data.description == "voorkeursvlinder, soort uit de familie Lasiocampidae (orde Lepidoptera)."
    assert data.fields["vernacular_name"] == ["voorkeursvlinder", "testvlinder"]

def test_normalize_gbif_species():
    responses = {
        SPECIES_URL: _fixture("gbif_species_9013523.json"),
        SPECIES_VERNACULAR_URL: _fixture("gbif_species_9013523_vernacular.json"),
        SPECIES_OCCURRENCES_URL: _fixture("gbif_species_9013523_occurrences.json")
    }
    data = GbifAdapter(image_width = WIDTH).normalize("https://www.gbif.org/species/9013523", FakeCache(responses))
    assert data.label == "Weberolegra weberi (Tams, 1929)"
    assert data.description == "Soort uit de familie Lasiocampidae (orde Lepidoptera)."
    assert data.image is None
    assert data.fields == WEBEROLEGRA_FIELDS
