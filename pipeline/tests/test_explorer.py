import json

from siboga.explorer import caption, entities_urls, identifications, image_filename, recorded_by, station_items
from siboga.models import Report

DWC = "http://rs.tdwg.org/dwc/terms/"

def test_current_identification_only():
    result = identifications({
        "scientificName": "Hydrolithon boergesenii (Foslie) Foslie",
        "identifiedBy": "Mikael Heggelund Foslie"
    })
    assert result == [{
        "name": "Hydrolithon boergesenii (Foslie) Foslie",
        "by": ["Mikael Heggelund Foslie"],
        "date": None,
        "remarks": None,
        "current": True
    }]

def test_history_from_extension_is_sorted_and_ends_with_current():
    occurrence = {
        "scientificName": "Parapenaeus fissurus (Bate, 1881)",
        "identifiedBy": "A. Cosnier",
        "dateIdentified": "1984-01-01T00:00:00",
        "extensions": {
            "http://rs.tdwg.org/dwc/terms/Identification": [
                {
                    f"{DWC}scientificName": "Parapenaeus fissurus (Bate, 1881)",
                    f"{DWC}identifiedBy": "A. Cosnier",
                    f"{DWC}dateIdentified": "1984"
                },
                {
                    f"{DWC}scientificName": "Penaeus fissurus",
                    f"{DWC}identifiedBy": "J.G. de Man",
                    f"{DWC}dateIdentified": "1911"
                }
            ]
        }
    }
    result = identifications(occurrence)
    assert [entry["name"] for entry in result] == ["Penaeus fissurus", "Parapenaeus fissurus (Bate, 1881)"]
    assert result[0]["by"] == ["J.G. de Man"]
    assert [entry["current"] for entry in result] == [False, True]

def test_previous_identifications_are_split_on_pipes():
    result = identifications({
        "scientificName": "Smittina Norman, 1903",
        "previousIdentifications": "Smittia sp. | Lepralia sp."
    })
    assert [entry["name"] for entry in result] == ["Smittia sp.", "Lepralia sp.", "Smittina Norman, 1903"]

def test_recorded_by_keeps_the_text_of_the_record():
    assert recorded_by({"recordedBy": "Anna Antoinette Weber-van Bosse scr."}) == ["Anna Antoinette Weber-van Bosse scr."]
    assert recorded_by({"recordedBy": "M. Weber | Siboga Expedition"}) == ["M. Weber", "Siboga Expedition"]
    assert recorded_by({}) == []

def test_caption_is_the_last_part_of_the_file_name():
    assert caption("UvA-BC 300.056 - Siboga - Sebangkatan.jpg") == "Sebangkatan"
    assert caption("COLLECTIE TROPENMUSEUM De vulkaan Goenoeng Api op Banda TMnr 10004159.jpg") == "COLLECTIE TROPENMUSEUM De vulkaan Goenoeng Api op Banda TMnr 10004159"

def test_entities_urls_ask_for_fifty_items_at_a_time():
    urls = entities_urls([f"Q{i}" for i in range(1, 121)])
    assert len(urls) == 3
    assert "ids=Q1%7CQ2%7C" in urls[0]
    assert "Q51" in urls[1] and "Q50%7C" not in urls[1]

def test_image_filename_prefers_preferred_and_skips_deprecated():
    def statement(value, rank):
        return {
            "rank": rank,
            "mainsnak": {
                "datavalue": {
                    "value": value
                }
            }
        }

    entity = {
        "claims": {
            "P18": [
                statement("Old.jpg", "deprecated"),
                statement("Normal.jpg", "normal"),
                statement("Best.jpg", "preferred")
            ]
        }
    }
    assert image_filename(entity) == "Best.jpg"
    assert image_filename({"claims": {"P18": [statement("Old.jpg", "deprecated")]}}) is None
    assert image_filename({"claims": {}}) is None
    assert image_filename(None) is None

def test_station_items_skip_stations_without_an_item(tmp_path):
    path = tmp_path / "route-stations.json"
    path.write_text(json.dumps({
        "stations": {
            "velden": ["nummer", "wikidata", "km"],
            "rijen": [["1", "Q141749010", 0], ["2", None, 10], ["225a", "Q141749044", 20]]
        }
    }))
    assert station_items(path, Report()) == {
        "1": "Q141749010",
        "225a": "Q141749044"
    }
