from pathlib import Path
import json

import pytest

from siboga.content import (
    BodyImage,
    LinkIndex,
    body_images,
    build_link_index,
    chapter_markers,
    chapter_number,
    content_type,
    convert_body,
    description,
    is_term,
    page_title,
    plugin_title,
    read_content,
    read_messages,
    record_uri,
    resolve_link,
    show_in_explore,
    slugify
)
from siboga.models import ContentItem, Coordinates, ItemKind, Marker, Report

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "content"
REAL_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content"

@pytest.fixture
def items() -> list[ContentItem]:
    return read_content(FIXTURE_PATH, Report())

@pytest.fixture
def index(items: list[ContentItem]):
    return build_link_index(items, FIXTURE_PATH)

def _by_ref(items: list[ContentItem]) -> dict[str, ContentItem]:
    return {item.ref: item for item in items}

def _convert(body: str, index):
    report = Report()
    item = ContentItem(
        body = body,
        frontmatter = {},
        id = "test",
        kind = ItemKind.CHAPTER,
        path = Path("chapters/Test.md"),
        title = "Test"
    )
    return convert_body(item, index, report), report

def _item(frontmatter: dict) -> ContentItem:
    return ContentItem(
        body = "",
        frontmatter = frontmatter,
        id = "test",
        kind = ItemKind.RECORD,
        path = Path("records/Test.md"),
        title = "Test"
    )

def test_build_link_index(index):
    assert index.refs["anna weber"] == "records/anna-weber"
    assert index.refs["hr.ms. siboga"] == "records/hr-ms-siboga"
    assert index.attachments["foto van anna.png"] == (FIXTURE_PATH / "bijlagen" / "Foto van Anna.png").resolve()
    assert not any(name.endswith(".md") for name in index.attachments)

def _markers(
    tmp_path: Path,
    geojson: str,
    refs: dict[str, str] | None = None
) -> tuple[list[Marker], Report]:
    path = tmp_path / "kaart.geojson"
    path.write_text(geojson, encoding = "utf-8")
    index = LinkIndex(attachments = {"kaart.geojson": path}, refs = refs or {})
    report = Report()
    return chapter_markers(_item({"geojson": "[[kaart.geojson]]"}), index, report), report

def _point(
    lon: float,
    lat: float,
    properties: dict | None = None
) -> dict:
    return {
        "type": "Feature",
        "properties": properties or {},
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        }
    }

def test_chapter_markers(items, index):
    chapters = _by_ref(items)
    report = Report()
    markers = chapter_markers(chapters["chapters/hoofdstuk-1-vertrek-uit-amsterdam"], index, report)
    assert markers == [
        Marker(coordinates = Coordinates(lat = -6.12, lon = 106.81), label = "Batavia", ref = "records/haven-jakarta"),
        Marker(coordinates = Coordinates(lat = -8.0, lon = 115.5), label = None, ref = None)
    ]
    assert report.warnings == []
    # Without geojson the chapter has no markers, and that is fine.
    assert chapter_markers(chapters["chapters/hoofdstuk-2-zonder-plek"], index, report) == []
    assert report.warnings == []

def test_chapter_markers_properties(tmp_path: Path):
    features = [
        _point(128.18, -3.69, {"label": " Ambon "}),
        _point(4.47, 52.17, {"name": "Leiden", "link": "/records/leiden"}),
        _point(106.8, -6.1, {"link": "Bestaat niet"})
    ]
    geojson = json.dumps({"type": "FeatureCollection", "features": features})
    markers, report = _markers(tmp_path, geojson, {"leiden": "records/leiden"})
    assert [marker.label for marker in markers] == ["Ambon", "Leiden", None]
    assert [marker.ref for marker in markers] == [None, "records/leiden", None]
    assert len(report.warnings) == 1
    assert "Bestaat niet" in report.warnings[0]

def test_chapter_markers_problems(tmp_path: Path):
    line = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "LineString",
            "coordinates": [[106.8, -6.1], [115.5, -8.0]]
        }
    }
    geojson = json.dumps({"type": "FeatureCollection", "features": [line, _point(200, 95), _point(115.5, -8.0)]})
    markers, report = _markers(tmp_path, geojson)
    assert len(markers) == 1
    assert any("outside the map" in warning for warning in report.warnings)
    assert any("LineString" in warning for warning in report.warnings)
    # A single geometry is a valid GeoJSON file too.
    markers, report = _markers(tmp_path, json.dumps({"type": "Point", "coordinates": [115.5, -8.0, 12]}))
    assert markers[0].coordinates == Coordinates(lat = -8.0, lon = 115.5)
    assert report.warnings == []
    markers, report = _markers(tmp_path, "{kapot")
    assert markers == []
    assert "can't be read" in report.warnings[0]
    report = Report()
    index = LinkIndex(attachments = {}, refs = {})
    assert chapter_markers(_item({"geojson": "[[weg.geojson]]"}), index, report) == []
    assert "does not exist" in report.warnings[0]

def test_chapter_markers_unquoted_wikilink(tmp_path: Path):
    path = tmp_path / "kaart.geojson"
    path.write_text(json.dumps(_point(115.5, -8.0)), encoding = "utf-8")
    index = LinkIndex(attachments = {"kaart.geojson": path}, refs = {})
    # Without quotes, YAML reads [[kaart.geojson]] as a list in a list.
    assert len(chapter_markers(_item({"geojson": [["kaart.geojson"]]}), index, Report())) == 1

def test_chapter_number(items):
    chapters = _by_ref(items)
    report = Report()
    assert chapter_number(chapters["chapters/hoofdstuk-1-vertrek-uit-amsterdam"], report) == 1
    assert chapter_number(_item({"chapter": 3}), report) == 3
    assert report.warnings == []
    assert chapter_number(chapters["chapters/hoofdstuk-2-zonder-plek"], report) is None
    assert chapter_number(_item({}), report) is None
    assert chapter_number(_item({"chapter": True}), report) is None
    assert len(report.warnings) == 3

def test_content_type(items):
    records = _by_ref(items)
    report = Report()
    assert content_type(records["records/anna-weber"], report) == "person"
    assert report.warnings == []
    assert content_type(records["records/hr-ms-siboga"], report) == "schip"
    assert content_type(_item({}), report) is None
    assert len(report.warnings) == 2

def test_convert_chapter_fixture(items, index):
    chapter = _by_ref(items)["chapters/hoofdstuk-1-vertrek-uit-amsterdam"]
    report = Report()
    converted = convert_body(chapter, index, report)
    assert converted.markdown == (
        "[Anna Weber](/records/anna-weber) was aan boord van de [Siboga](/records/hr-ms-siboga). \n"
        "Er is een [vlinder](/records/weberolegra-weberi) naar haar vernoemd.\n"
        "\n"
        "![|300](media/foto-van-anna.png)\n"
    )
    assert converted.links == ["records/anna-weber", "records/hr-ms-siboga", "records/weberolegra-weberi"]
    assert converted.attachments == {"foto-van-anna.png": (FIXTURE_PATH / "bijlagen" / "Foto van Anna.png").resolve()}
    assert report.warnings == []

def test_convert_code_untouched(index):
    body = "```\n[[Anna Weber]] %%x%%\n```\nen `[[Anna Weber]]` maar [[Anna Weber]]\n"
    converted, report = _convert(body, index)
    assert converted.markdown == "```\n[[Anna Weber]] %%x%%\n```\nen `[[Anna Weber]]` maar [Anna Weber](/records/anna-weber)\n"
    assert converted.links == ["records/anna-weber"]

def test_convert_comments(index):
    converted, report = _convert("voor %%kort%% midden %%over\nmeer regels [[Anna Weber]]%% na", index)
    assert converted.markdown == "voor  midden  na"
    assert converted.links == []
    assert report.warnings == []

def test_convert_embed_missing(index):
    converted, report = _convert("a ![[Bestaat niet.jpg]] b", index)
    assert converted.markdown == "a  b"
    assert converted.attachments == {}
    assert len(report.warnings) == 1

def test_convert_embed_of_note(index):
    converted, report = _convert("![[Anna Weber]]", index)
    assert converted.markdown == "[Anna Weber](/records/anna-weber)"
    assert converted.links == ["records/anna-weber"]

def test_convert_external_links_untouched(index):
    body = "[site](https://example.org/a_(b)) [mail](mailto:a@b.nl) [kop](#kop) [abs](/records/x)"
    converted, report = _convert(body, index)
    assert converted.markdown == body
    assert report.warnings == []

def test_convert_markdown_links_to_notes(index):
    body = "[Anna](records/Anna%20Weber.md) en [Siboga](<Hr.Ms. Siboga.md>) en [ook](Anna Weber.md#Leven) en [weg](Niets.md)"
    converted, report = _convert(body, index)
    assert converted.markdown == (
        "[Anna](/records/anna-weber) en [Siboga](/records/hr-ms-siboga) en [ook](/records/anna-weber) en weg"
    )
    assert converted.links == ["records/anna-weber", "records/hr-ms-siboga"]
    assert len(report.warnings) == 1

def test_convert_markdown_image(index):
    converted, report = _convert("![foto](bijlagen/Foto%20van%20Anna.png)", index)
    assert converted.markdown == "![foto](media/foto-van-anna.png)"
    assert list(converted.attachments) == ["foto-van-anna.png"]

def test_convert_unresolved_wikilink(index):
    converted, report = _convert("Zie [[Krantenartikel|het interview]] en [[Bestaat niet]].", index)
    assert converted.markdown == "Zie het interview en Bestaat niet."
    assert converted.links == []
    assert len(report.warnings) == 2
    assert all("chapters/Test.md" in warning for warning in report.warnings)

def test_convert_wikilink_variants(index):
    body = (
        "[[Anna Weber#Jeugd]] [[Anna Weber#Jeugd|jong]] [[records/Anna Weber]] "
        "| [[Hr.Ms. Siboga\\|schip]] | [[ anna weber ]] [[Weberolegra weberi|vlinder]]"
    )
    converted, report = _convert(body, index)
    assert converted.markdown == (
        "[Anna Weber](/records/anna-weber) [jong](/records/anna-weber) [Anna Weber](/records/anna-weber) "
        "| [schip](/records/hr-ms-siboga) | [anna weber](/records/anna-weber) [vlinder](/records/weberolegra-weberi)"
    )
    assert converted.links == ["records/anna-weber", "records/hr-ms-siboga", "records/weberolegra-weberi"]
    assert report.warnings == []

def test_description(items):
    records = _by_ref(items)
    assert description(records["records/anna-weber"]) == "Nederlandse algoloog (1852-1942)"
    assert description(records["records/haven-jakarta"]) is None
    assert description(_item({"description_nl": "  "})) is None

def test_embed_extension_lowercased(tmp_path: Path):
    (tmp_path / "Kaart Route.JPG").write_bytes(b"x")
    index = build_link_index([], tmp_path)
    converted, report = _convert("![[kaart route.jpg]]", index)
    assert converted.markdown == "![](media/kaart-route.jpg)"
    assert converted.attachments == {"kaart-route.jpg": (tmp_path / "Kaart Route.JPG").resolve()}

def test_read_content(items):
    refs = [item.ref for item in items]
    # sjablonen/Record.md is left out: .obsidian/templates.json makes it the templates folder.
    assert refs == [
        "chapters/hoofdstuk-1-vertrek-uit-amsterdam",
        "chapters/hoofdstuk-2-zonder-plek",
        "records/anna-weber",
        "records/duplicaat",
        "records/duplicaat-2",
        "records/haven-jakarta",
        "records/hr-ms-siboga",
        "records/weberolegra-weberi"
    ]
    anna = _by_ref(items)["records/anna-weber"]
    assert anna.kind == ItemKind.RECORD
    assert anna.title == "Anna Weber"
    assert anna.path == Path("records/Anna Weber.md")
    assert anna.frontmatter["contenttype"] == "person"
    assert anna.body == "Anna was aan boord van de [[Hr.Ms. Siboga]].\n"
    chapter = _by_ref(items)["chapters/hoofdstuk-1-vertrek-uit-amsterdam"]
    assert chapter.kind == ItemKind.CHAPTER
    assert chapter.body.startswith("[[Anna Weber]] was aan boord")

def test_read_content_without_templates_setting(tmp_path: Path):
    record = tmp_path / "sjablonen" / "Record.md"
    record.parent.mkdir()
    record.write_text("---\ntype: record\n---\n", encoding = "utf-8")
    # Without Obsidian's setting the pipeline does not know it is a template.
    assert [item.ref for item in read_content(tmp_path, Report())] == ["records/record"]

def test_read_content_duplicates_sorted_by_path(items):
    duplicates = {item.id: item.path for item in items if item.id.startswith("duplicaat")}
    assert duplicates == {
        "duplicaat": Path("overig/Duplicaat.md"),
        "duplicaat-2": Path("records/Duplicaat.md")
    }

def test_read_content_warnings():
    report = Report()
    read_content(FIXTURE_PATH, report)
    assert len(report.warnings) == 3
    assert any("Kapotte YAML.md" in warning for warning in report.warnings)
    assert any("Onbekend type.md" in warning for warning in report.warnings)
    assert any("duplicaat-2" in warning for warning in report.warnings)
    # No frontmatter, no type, or in a hidden folder: silently skipped.
    assert not any("README" in warning or "Notitie" in warning or "Verborgen" in warning for warning in report.warnings)

def test_real_content_smoke():
    if not REAL_CONTENT_PATH.is_dir():
        pytest.skip("content/ ontbreekt")
    report = Report()
    items = read_content(REAL_CONTENT_PATH, report)
    index = build_link_index(items, REAL_CONTENT_PATH)
    for item in items:
        convert_body(item, index, report)
        if item.kind == ItemKind.CHAPTER:
            chapter_markers(item, index, report)
            chapter_number(item, report)
        else:
            content_type(item, report)
            description(item)
            record_uri(item, report)
    assert items

def test_record_uri(items):
    records = _by_ref(items)
    report = Report()
    assert record_uri(records["records/anna-weber"], report) == "https://www.wikidata.org/wiki/Q1940785"
    assert report.warnings == []
    assert record_uri(records["records/haven-jakarta"], report) is None
    assert record_uri(_item({}), report) is None
    assert record_uri(_item({"uri": ["https://a.org", "https://b.org"]}), report) is None
    assert record_uri(_item({"uri": "ftp://a.org/x"}), report) is None
    assert len(report.warnings) == 4

def test_record_uri_of_term():
    report = Report()
    # A term needs no uri; with one, it is a link to read more.
    assert record_uri(_item({"contenttype": "term"}), report) is None
    assert record_uri(_item({"contenttype": "term", "uri": "https://nl.wikipedia.org/wiki/Sloep"}), report) == "https://nl.wikipedia.org/wiki/Sloep"
    assert report.warnings == []
    assert is_term(_item({"contenttype": " term "}))
    assert not is_term(_item({"contenttype": "person"}))

def test_resolve_link(index):
    assert resolve_link("Anna Weber", index) == "records/anna-weber"
    assert resolve_link(" ANNA WEBER#Kop ", index) == "records/anna-weber"
    assert resolve_link("records/Anna Weber.md", index) == "records/anna-weber"
    assert resolve_link("Niemand", index) is None

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Anna Weber", "anna-weber"),
        ("Hr.Ms. Siboga", "hr-ms-siboga"),
        ("Zoöloog", "zooloog"),
        ("Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam", "hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam"),
        ("  --Café  Ål!--  ", "cafe-al"),
        ("???", "item"),
        ("", "item")
    ]
)
def test_slugify(text: str, expected: str):
    assert slugify(text) == expected

def _vault(
    tmp_path: Path,
    files: dict[str, str]
) -> Path:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents = True, exist_ok = True)
        path.write_text(text, encoding = "utf-8")
    return tmp_path

def test_pages(tmp_path: Path):
    vault = _vault(tmp_path, {
        "pages/about.md": "---\ntype: page\ntitle: Over deze website\n---\nTekst over [[Anna Weber]].\n",
        "pages/zonder titel.md": "---\ntype: page\n---\nTekst\n",
        "records/Anna Weber.md": "---\ntype: record\nuri: https://www.wikidata.org/wiki/Q1940785\ncontenttype: person\n---\n"
    })
    report = Report()
    items = {item.ref: item for item in read_content(vault, report)}
    assert set(items) == {"pages/about", "pages/zonder-titel", "records/anna-weber"}
    assert items["pages/about"].kind == ItemKind.PAGE
    assert page_title(items["pages/about"], report) == "Over deze website"
    assert page_title(items["pages/zonder-titel"], report) == "zonder titel"
    assert any("page without title" in warning for warning in report.warnings)
    converted = convert_body(items["pages/about"], build_link_index(list(items.values()), vault), report)
    assert converted.markdown.strip() == "Tekst over [Anna Weber](/records/anna-weber)."

def test_read_messages(tmp_path: Path):
    vault = _vault(tmp_path, {
        "etc/i18n.md": "---\ntype: i18n\nstart_bn: START EXPEDITIE\nabout_site: Over deze site\nleeg:\n---\n",
        "etc/meer.md": "---\ntype: i18n\nabout_site: Over de site\n---\n",
        "records/Gewoon.md": "---\ntype: record\nuri: https://example.org/x\n---\n"
    })
    report = Report()
    assert read_messages(vault, report) == {"about_site": "Over de site", "start_bn": "START EXPEDITIE"}
    warnings = "\n".join(report.warnings)
    assert "empty message: leeg" in warnings
    assert "about_site already exists" in warnings
    items_report = Report()
    assert [item.ref for item in read_content(vault, items_report)] == ["records/gewoon"]
    assert items_report.warnings == []

def test_plugins(tmp_path: Path):
    vault = _vault(tmp_path, {
        "plugins/IIIF.md": "---\ntype: plugin\nid: iiif\nshow_in_explore: false\n---\n",
        "plugins/Diep onder het schip.md": "---\ntype: plugin\nid: deepdive\ndescription_nl: Specimens\nshow_in_explore: \"true\"\n---\n",
        "plugins/Zonder id.md": "---\ntype: plugin\ntitle: Met titel\nshow_in_explore: misschien\n---\n"
    })
    report = Report()
    items = {item.ref: item for item in read_content(vault, report)}
    assert set(items) == {"plugins/deepdive", "plugins/iiif", "plugins/zonder-id"}
    assert items["plugins/iiif"].kind == ItemKind.PLUGIN
    assert any("plugin without id" in warning for warning in report.warnings)
    assert plugin_title(items["plugins/deepdive"]) == "Diep onder het schip"
    assert plugin_title(items["plugins/zonder-id"]) == "Met titel"
    assert description(items["plugins/deepdive"]) == "Specimens"
    report = Report()
    assert show_in_explore(items["plugins/deepdive"], report) is True
    assert show_in_explore(items["plugins/iiif"], report) is False
    assert report.warnings == []
    assert show_in_explore(items["plugins/zonder-id"], report) is False
    assert len(report.warnings) == 1

def test_convert_plugin_wikilink(tmp_path: Path):
    vault = _vault(tmp_path, {
        "plugins/IIIF.md": "---\ntype: plugin\nid: iiif\n---\n"
    })
    index = build_link_index(read_content(vault, Report()), vault)
    body = "[[IIIF#https://iiif.example.org/iiif/3/1/full/max/0/default.jpg]]\n\n[[IIIF]] [[iiif#a b|Bekijk]]"
    converted, report = _convert(body, index)
    assert converted.markdown == (
        "[IIIF](/plugins/iiif?argument=https%3A%2F%2Fiiif.example.org%2Fiiif%2F3%2F1%2Ffull%2Fmax%2F0%2Fdefault.jpg)\n\n"
        "[IIIF](/plugins/iiif) [Bekijk](/plugins/iiif?argument=a%20b)"
    )
    assert converted.links == ["plugins/iiif"]
    assert report.warnings == []

def test_convert_image_size(index):
    converted, report = _convert("![[Foto van Anna.png|14]] ![[Foto van Anna.png|300x200]] ![[Foto van Anna.png|Anna]]", index)
    assert converted.markdown == "![|14](media/foto-van-anna.png) ![|300x200](media/foto-van-anna.png) ![](media/foto-van-anna.png)"
    assert report.warnings == []

def test_convert_gallery(index):
    body = "::: gallery\n![[Foto van Anna.png]]\n*Anna, 1899. [Bron](https://example.org)*\n:::\n"
    converted, report = _convert(body, index)
    assert converted.markdown == "::: gallery\n![](media/foto-van-anna.png)\n*Anna, 1899. [Bron](https://example.org)*\n:::\n"
    assert report.warnings == []

def test_convert_gallery_unclosed(index):
    converted, report = _convert("::: gallery\n![[Foto van Anna.png]]\n", index)
    assert len(report.warnings) == 1
    assert "without a closing" in report.warnings[0]
    converted, report = _convert("```\n::: gallery\n```\n", index)
    assert report.warnings == []

def test_convert_details(index):
    body = ":::details Bekijk alle bronnen\n- [[Foto van Anna.png]]\n\n::: gallery\n![[Foto van Anna.png]]\n:::\n:::\n"
    converted, report = _convert(body, index)
    assert converted.markdown.startswith(":::details Bekijk alle bronnen\n- ")
    assert converted.markdown.endswith(":::\n:::\n")
    assert report.warnings == []

def test_convert_details_unclosed(index):
    converted, report = _convert(":::details Bronnen\n- Acda (2019)\n", index)
    assert len(report.warnings) == 1
    assert "details without a closing" in report.warnings[0]
    converted, report = _convert(":::details Bronnen\n::: gallery\n![[Foto van Anna.png]]\n:::\n", index)
    assert len(report.warnings) == 1
    assert "details without a closing" in report.warnings[0]

def test_body_images():
    markdown = (
        "![Siboga](https://commons.wikimedia.org/wiki/Special:FilePath/Siboga_(1898).jpg?width=1200)\n"
        "*[De Siboga](/records/foto-van-de-siboga), 1898*\n\n"
        "![](media/kaart.png)\n"
        "*Een kaart zonder record*\n\n"
        "Tekst met ![los](media/los.png) erin.\n\n"
        "```\n![code](media/code.png)\n```\n"
    )
    assert body_images(markdown) == [
        BodyImage(record_id = "foto-van-de-siboga", src = "https://commons.wikimedia.org/wiki/Special:FilePath/Siboga_(1898).jpg?width=1200"),
        BodyImage(record_id = None, src = "media/kaart.png"),
        BodyImage(record_id = None, src = "media/los.png")
    ]

def test_body_images_caption_must_follow_directly():
    assert body_images("![](media/a.png)\n\n*[A](/records/a)*\n") == [BodyImage(record_id = None, src = "media/a.png")]
