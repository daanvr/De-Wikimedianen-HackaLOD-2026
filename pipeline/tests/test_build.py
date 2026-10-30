"""Integration test for the build step: small vault, fake source, real cache, no internet."""
from pathlib import Path
import json

import pytest

from siboga import build
from siboga.build import check_output, run_build
from siboga.cache import Cache
from siboga.config import Config
from siboga.models import CachedResponse, ImageInfo, Report, SourceData
from siboga.sources import Registry
from siboga.sources.base import SourceAdapter

IMAGE_URL = "https://example.org/files/anna.jpg"

class FakeAdapter(SourceAdapter):
    name = "fake"

    def fetch(
        self,
        uri: str,
        fetcher
    ) -> None:
        pass

    def matches(self, uri: str) -> bool:
        return uri.startswith("https://example.org/")

    def normalize(
        self,
        uri: str,
        cache
    ) -> SourceData | None:
        if uri.endswith("/missing"):
            return None
        if uri.endswith("/broken"):
            raise ValueError("kapotte bron")
        license = None if uri.endswith("/nolicense") else "CC0"
        return SourceData(
            description = "beschrijving uit de bron",
            fields = {
                "birth_date": ["1852-03-27"],
                "death_date": ["ergens in 1942"],
                "occupation": ["algoloog", "botanicus"],
                "scientific_name": ["hoort niet bij een persoon"]
            },
            image = ImageInfo(
                credit = "Fotograaf onbekend",
                download_url = IMAGE_URL,
                license = license,
                license_url = None,
                source_url = "https://example.org/page"
            ),
            label = "Anna Weber-van Bosse"
        )

def _write(
    path: Path,
    text: str
) -> None:
    path.parent.mkdir(parents = True, exist_ok = True)
    path.write_text(text, encoding = "utf-8")

@pytest.fixture
def config(tmp_path: Path) -> Config:
    vault = tmp_path / "content"
    _write(vault / "records" / "Anna Weber.md", "---\ntype: record\nuri: https://example.org/anna\ndescription_nl: Nederlandse algoloog\ncontenttype: person\n---\n")
    _write(vault / "records" / "Zonder bron.md", "---\ntype: record\nuri: https://example.org/missing\ncontenttype: item\n---\n")
    _write(vault / "records" / "Zonder licentie.md", "---\ntype: record\nuri: https://example.org/nolicense\ncontenttype: media\n---\n")
    _write(vault / "records" / "Kapotte bron.md", "---\ntype: record\nuri: https://example.org/broken\ncontenttype: item\n---\n")
    _write(vault / "records" / "Geen url.md", "---\ntype: record\nuri: wikidata\ncontenttype: location\n---\n")
    _write(vault / "records" / "Haven.md", "---\ntype: record\nuri: https://elders.example.com/haven\ncontenttype: location\n---\n")
    _write(
        vault / "chapters" / "Hoofdstuk 1 - Vertrek.md",
        "---\ntype: chapter\nchapter: \"1\"\nlocation: \"[[Haven]]\"\n---\n"
        "[[Anna Weber|Anna]] ging mee. Zie ook [[Bestaat niet]].\n\n![[kaart.png]]\n\n[[IIIF#https://example.org/iiif/1/full/max/0/default.jpg]]\n"
    )
    _write(vault / "pages" / "about.md", "---\ntype: page\ntitle: Over deze website\n---\nGemaakt door het team. Lees over [[Anna Weber]].\n")
    _write(vault / "plugins" / "IIIF.md", "---\ntype: plugin\nid: iiif\nshow_in_explore: false\n---\n")
    _write(vault / "plugins" / "Diep.md", "---\ntype: plugin\nid: deepdive\ndescription_nl: Specimens\nshow_in_explore: \"true\"\n---\n")
    _write(vault / "etc" / "i18n.md", "---\ntype: i18n\nabout_site: Over deze site\nfield_birth_date: Geboren\n---\n")
    (vault / "kaart.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    return Config(
        cache_path = tmp_path / "cache" / "siboga.sqlite",
        content_path = vault,
        image_width = 100,
        max_age_days = 30,
        media_path = tmp_path / "cache" / "media",
        output_path = tmp_path / "out" / "data",
        timeout_seconds = 1,
        user_agent = "test"
    )

@pytest.fixture(autouse = True)
def fake_registry(monkeypatch):
    monkeypatch.setattr(build, "build_registry", lambda config: Registry([FakeAdapter()]))

def _cache_image(config: Config) -> None:
    cache = Cache(config.cache_path, config.media_path)
    cache.media_path(IMAGE_URL).write_bytes(b"\xff\xd8\xff")
    cache.put(CachedResponse(
        adapter = "fake",
        body = None,
        content_type = "image/jpeg",
        fetched_at = "2026-10-30T12:00:00+00:00",
        status = 200,
        url = IMAGE_URL
    ))
    cache.close()

def test_build_writes_frontend_data(config: Config):
    _cache_image(config)
    report = Report()
    json_path = run_build(config, report)
    data = json.loads(json_path.read_text(encoding = "utf-8"))
    assert data["meta"]["schemaVersion"] == 2
    assert data["meta"]["warnings"] == len(report.warnings)
    assert data["messages"] == {"about_site": "Over deze site", "field_birth_date": "Geboren"}
    about = data["pages"]["about"]
    assert about["ref"] == "pages/about"
    assert about["title"] == "Over deze website"
    assert about["body"] == "Gemaakt door het team. Lees over [Anna Weber](/records/anna-weber)."
    assert about["links"] == ["records/anna-weber"]
    chapter = data["chapters"][0]
    assert chapter["ref"] == "chapters/hoofdstuk-1-vertrek"
    assert chapter["number"] == 1
    assert chapter["location"] == "records/haven"
    assert "[Anna](/records/anna-weber)" in chapter["body"]
    assert "![](media/kaart.png)" in chapter["body"]
    assert chapter["links"] == ["records/anna-weber", "plugins/iiif"]
    assert "[IIIF](/plugins/iiif?argument=https%3A%2F%2Fexample.org%2Fiiif%2F1%2Ffull%2Fmax%2F0%2Fdefault.jpg)" in chapter["body"]
    assert data["plugins"]["iiif"] == {
        "ref": "plugins/iiif",
        "id": "iiif",
        "title": "IIIF",
        "description": None,
        "showInExplore": False,
        "body": None,
        "links": [],
        "backlinks": ["chapters/hoofdstuk-1-vertrek"]
    }
    assert data["plugins"]["deepdive"]["title"] == "Diep"
    assert data["plugins"]["deepdive"]["description"] == "Specimens"
    assert data["plugins"]["deepdive"]["showInExplore"] is True
    anna = data["records"]["anna-weber"]
    assert anna["contentType"] == "person"
    assert anna["description"] == "Nederlandse algoloog"
    assert anna["label"] == "Anna Weber-van Bosse"
    assert anna["source"] == "fake"
    assert anna["fields"] == [
        {"key": "birth_date", "type": "date", "values": ["1852-03-27"], "source": "fake"},
        {"key": "occupation", "type": "text", "values": ["algoloog", "botanicus"], "source": "fake"}
    ]
    assert anna["sources"] == [{"name": "fake", "uri": anna["uri"]}]
    assert anna["labelSource"] == "fake"
    assert anna["descriptionSource"] == "content"
    assert anna["image"]["source"] == "fake"
    assert anna["image"]["src"] == "media/anna-weber.jpg"
    assert anna["image"]["license"] == "CC0"
    assert anna["backlinks"] == ["pages/about", "chapters/hoofdstuk-1-vertrek"]
    messages = "\n".join(report.warnings)
    assert "invalid value for death_date" in messages
    assert "field_occupation" in messages
    assert "field_birth_date," not in messages
    assert (config.output_path / "media" / "anna-weber.jpg").read_bytes() == b"\xff\xd8\xff"
    assert (config.output_path / "media" / "kaart.png").exists()
    assert check_output(config.output_path) == []

def test_build_tolerates_bad_content_and_sources(config: Config):
    _cache_image(config)
    report = Report()
    data = json.loads(run_build(config, report).read_text(encoding = "utf-8"))
    records = data["records"]
    assert records["zonder-bron"]["label"] is None
    assert records["zonder-bron"]["sources"] == []
    assert records["zonder-bron"]["labelSource"] is None
    assert records["haven"]["sources"] == []
    assert records["zonder-licentie"]["image"] is None
    assert records["kapotte-bron"]["source"] == "fake"
    assert records["geen-url"]["uri"] is None
    assert records["haven"]["source"] is None
    messages = "\n".join(report.warnings)
    for fragment in ["Bestaat niet", "kapotte bron", "licentie", "no adapter", "run fetch first"]:
        assert fragment in messages

def test_build_without_cached_image_skips_image(config: Config):
    report = Report()
    data = json.loads(run_build(config, report).read_text(encoding = "utf-8"))
    assert data["records"]["anna-weber"]["image"] is None
    assert any("not in the cache" in warning for warning in report.warnings)

def test_build_replaces_previous_output(config: Config):
    stale = config.output_path / "media" / "oud.jpg"
    stale.parent.mkdir(parents = True)
    stale.write_bytes(b"oud")
    run_build(config, Report())
    assert not stale.exists()
    assert (config.output_path / "siboga.json").exists()

def test_check_output_finds_problems(config: Config):
    _cache_image(config)
    run_build(config, Report())
    (config.output_path / "media" / "anna-weber.jpg").unlink()
    problems = check_output(config.output_path)
    assert any("anna-weber.jpg" in problem for problem in problems)
