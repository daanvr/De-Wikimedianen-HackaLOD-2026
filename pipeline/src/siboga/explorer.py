"""Specimens and stations of the explore mode: records and images, for explorer.json and media/.

The explore mode shows the specimens of the gold dataset (frontend/public/datasets/siboga-goud.json)
that are linked to a station. `fetch` caches their GBIF occurrences and images; `build` copies the
images to media/ and writes what the dataset itself does not have: the image with its license,
every identification the record knows about, and the collectors as the record writes them.

The stations (frontend/public/datasets/route-stations.json) each have a Wikidata item; some of those
have an image (P18), mostly a photograph from the expedition. They go the same way.
"""
from pathlib import Path
from urllib.parse import quote, urlencode
import json
import shutil

from loguru import logger

from siboga.cache import Cache
from siboga.fetcher import Fetcher
from siboga.models import Report
from siboga.sources.commons import fetch_image, read_image
from siboga.sources.gbif import GBIF_OCCURRENCE_URL, _pick_image

ADAPTER = "gbif"
WIKIDATA_ADAPTER = "wikidata"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
# The most items the Wikidata API returns in one request
ENTITIES_PER_REQUEST = 50
IDENTIFICATION_EXTENSION = "http://rs.tdwg.org/dwc/terms/Identification"
DWC = "http://rs.tdwg.org/dwc/terms/"

def build_explorer(
    gold_path: Path,
    stations_path: Path,
    cache: Cache,
    output_dir: Path,
    media_dir: Path,
    image_width: int,
    report: Report
) -> int:
    """Writes explorer.json next to siboga.json; returns the number of images copied."""
    keys = specimen_keys(gold_path, report)
    specimens = {}
    images = 0
    for key in keys:
        occurrence = cache.get_json(GBIF_OCCURRENCE_URL.format(key = key))
        if not isinstance(occurrence, dict):
            report.warn(f"explorer: GBIF occurrence {key} is not in the cache, run fetch first")
            continue
        entry = {
            "identifications": identifications(occurrence),
            "recordedBy": recorded_by(occurrence)
        }
        image = _pick_image({"results": [occurrence]}, image_width)
        if image is not None and cache.has_media(image.download_url):
            cached_file = cache.media_path(image.download_url)
            name = f"specimen-{key}{cached_file.suffix.lower() or '.jpg'}"
            shutil.copyfile(cached_file, media_dir / name)
            entry["image"] = {
                "src": f"media/{name}",
                "credit": image.credit,
                "license": image.license,
                "licenseUrl": image.license_url,
                "sourceUrl": image.source_url
            }
            images += 1
        specimens[str(key)] = entry
    stations = build_station_images(stations_path, cache, media_dir, image_width, report)
    (output_dir / "explorer.json").write_text(
        json.dumps({"specimens": specimens, "stations": stations}, ensure_ascii = False, indent = 1) + "\n",
        encoding = "utf-8"
    )
    logger.info(f"explorer: {len(specimens)} specimens, {images} images; {len(stations)} station images")
    return images + len(stations)

def build_station_images(
    stations_path: Path,
    cache: Cache,
    media_dir: Path,
    image_width: int,
    report: Report
) -> dict[str, dict]:
    """Copies the cached Wikidata images of the stations to media/; returns them per station number."""
    stations = station_items(stations_path, report)
    images = {}
    entities = {}
    for url in entities_urls(sorted(set(stations.values()))):
        data = cache.get_json(url)
        if not isinstance(data, dict):
            report.warn("explorer: Wikidata items of the stations are not in the cache, run fetch first")
            continue
        entities.update(data.get("entities") or {})
    for number, qid in stations.items():
        filename = image_filename(entities.get(qid))
        if filename is None:
            continue
        image = read_image(filename, image_width, cache)
        if image is None or not cache.has_media(image.download_url):
            report.warn(f"explorer: image {filename} of station {number} is not in the cache, run fetch first")
            continue
        cached_file = cache.media_path(image.download_url)
        name = f"station-{_safe(number)}{cached_file.suffix.lower() or '.jpg'}"
        shutil.copyfile(cached_file, media_dir / name)
        images[number] = {
            "image": {
                "src": f"media/{name}",
                "caption": caption(filename),
                "credit": image.credit,
                "license": image.license,
                "licenseUrl": image.license_url,
                "sourceUrl": image.source_url
            }
        }
    return images

def caption(filename: str) -> str:
    """What the photo shows, from its file name: 'UvA-BC 300.056 - Siboga - Sebangkatan.jpg' becomes 'Sebangkatan'."""
    name = filename.rsplit(".", 1)[0]
    return name.rsplit(" - ", 1)[-1].strip()

def entities_urls(qids: list[str]) -> list[str]:
    """API URLs for the claims of Wikidata items, as many per request as the API allows."""
    urls = []
    for start in range(0, len(qids), ENTITIES_PER_REQUEST):
        params = [
            ("action", "wbgetentities"),
            ("format", "json"),
            ("props", "claims"),
            ("ids", "|".join(qids[start:start + ENTITIES_PER_REQUEST]))
        ]
        urls.append(f"{WIKIDATA_API_URL}?{urlencode(params, quote_via = quote)}")
    return urls

def fetch_explorer(
    gold_path: Path,
    stations_path: Path,
    fetcher: Fetcher,
    image_width: int,
    report: Report
) -> None:
    """Caches the GBIF occurrence and the image of every specimen, and the images of the stations."""
    keys = specimen_keys(gold_path, report)
    logger.info(f"explorer: {len(keys)} specimens")
    for key in keys:
        try:
            occurrence = fetcher.get_json(GBIF_OCCURRENCE_URL.format(key = key), ADAPTER)
            if not isinstance(occurrence, dict):
                continue
            image = _pick_image({"results": [occurrence]}, image_width)
            if image is not None:
                fetcher.download(image.download_url, ADAPTER)
        except Exception as error:
            # One broken record must not stop the rest.
            report.warn(f"explorer: fetching GBIF occurrence {key} failed: {error!r}")
    fetch_station_images(stations_path, fetcher, image_width, report)

def fetch_station_images(
    stations_path: Path,
    fetcher: Fetcher,
    image_width: int,
    report: Report
) -> None:
    """Caches the Wikidata items of the stations and the image (P18) of those that have one."""
    stations = station_items(stations_path, report)
    filenames = set()
    for url in entities_urls(sorted(set(stations.values()))):
        data = fetcher.get_json(url, WIKIDATA_ADAPTER)
        if not isinstance(data, dict):
            report.warn("explorer: fetching Wikidata items of the stations failed")
            continue
        for entity in (data.get("entities") or {}).values():
            filename = image_filename(entity)
            if filename is not None:
                filenames.add(filename)
    logger.info(f"explorer: {len(stations)} stations, {len(filenames)} images on Wikidata")
    for filename in sorted(filenames):
        try:
            fetch_image(filename, image_width, fetcher, WIKIDATA_ADAPTER)
        except Exception as error:
            report.warn(f"explorer: fetching station image {filename} failed: {error!r}")

def identifications(occurrence: dict) -> list[dict]:
    """Every identification of a specimen, oldest first, the current one last.

    Comes from the Identification extension when the museum publishes its history,
    otherwise from previousIdentifications and the current identification.
    """
    history = []
    for row in (occurrence.get("extensions") or {}).get(IDENTIFICATION_EXTENSION) or []:
        entry = _identification(
            name = row.get(f"{DWC}scientificName") or row.get(f"{DWC}typifiedName"),
            by = row.get(f"{DWC}identifiedBy"),
            date = row.get(f"{DWC}dateIdentified"),
            remarks = row.get(f"{DWC}identificationRemarks")
        )
        if entry is not None:
            history.append(entry)
    if not history:
        for text in (occurrence.get("previousIdentifications") or "").split("|"):
            entry = _identification(name = text)
            if entry is not None:
                history.append(entry)
    history.sort(key = lambda entry: entry["date"] or "")
    current = _identification(
        name = occurrence.get("scientificName"),
        by = occurrence.get("identifiedBy"),
        date = occurrence.get("dateIdentified"),
        remarks = occurrence.get("identificationRemarks")
    )
    if current is not None:
        history = [entry for entry in history if not _same(entry, current)]
        current["current"] = True
        history.append(current)
    return history

def image_filename(entity: dict | None) -> str | None:
    """The Commons file name of the image (P18) of a Wikidata item; a preferred statement wins, a deprecated one never."""
    if not isinstance(entity, dict):
        return None
    statements = [
        statement for statement in (entity.get("claims") or {}).get("P18") or []
        if statement.get("rank") != "deprecated"
    ]
    statements.sort(key = lambda statement: statement.get("rank") != "preferred")
    for statement in statements:
        value = (statement.get("mainsnak") or {}).get("datavalue", {}).get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None

def recorded_by(occurrence: dict) -> list[str]:
    """The collectors exactly as the record writes them (Darwin Core recordedBy, split on pipes)."""
    return [person.strip() for person in (occurrence.get("recordedBy") or "").split("|") if person.strip()]

def specimen_keys(
    gold_path: Path,
    report: Report
) -> list[int]:
    """GBIF keys of the specimens in the gold dataset that have a station."""
    if not gold_path.is_file():
        report.warn(f"explorer: gold dataset not found at {gold_path}")
        return []
    gold = json.loads(gold_path.read_text(encoding = "utf-8"))
    fields = gold["specimens"]["velden"]
    key_index, station_index = fields.index("gbif"), fields.index("station")
    return [row[key_index] for row in gold["specimens"]["rijen"] if row[station_index] is not None]

def station_items(
    stations_path: Path,
    report: Report
) -> dict[str, str]:
    """Wikidata item per station number, for the stations that have one."""
    if not stations_path.is_file():
        report.warn(f"explorer: stations not found at {stations_path}")
        return {}
    data = json.loads(stations_path.read_text(encoding = "utf-8"))
    fields = data["stations"]["velden"]
    number_index, item_index = fields.index("nummer"), fields.index("wikidata")
    return {row[number_index]: row[item_index] for row in data["stations"]["rijen"] if row[item_index]}

def _identification(
    name: str | None = None,
    by: str | None = None,
    date: str | None = None,
    remarks: str | None = None
) -> dict | None:
    name = (name or "").strip()
    if not name:
        return None
    return {
        "name": name,
        "by": [person.strip() for person in (by or "").split("|") if person.strip()],
        "date": (date or "").strip()[:10] or None,
        "remarks": (remarks or "").strip() or None,
        "current": False
    }

def _safe(value: str) -> str:
    """A station number as part of a file name: 225a stays 225a, anything odd becomes a dash."""
    return "".join(character if character.isalnum() else "-" for character in value)

def _same(a: dict, b: dict) -> bool:
    """Same name, and dates that agree as far as both go: 1984 matches 1984-01-01."""
    if a["name"] != b["name"]:
        return False
    if not a["date"] or not b["date"]:
        return True
    return a["date"].startswith(b["date"]) or b["date"].startswith(a["date"])
