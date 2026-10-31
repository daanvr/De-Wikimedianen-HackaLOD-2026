"""Adapter for GBIF: Catalogue of Life taxa (/taxon/…), GBIF species (/species/…) and specimens (/occurrence/…)."""
from __future__ import annotations

from typing import TYPE_CHECKING
import hashlib
import re

from loguru import logger

from siboga.models import Coordinates, ImageInfo, SourceData
from siboga.sources.base import SourceAdapter

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

# GBIF's taxon pages use the extended release of the Catalogue of Life (COL XR).
COL_CHECKLIST_KEY = "7ddf754f-d193-4cc9-b351-99906754a03b"
COL_INFO_URL = "https://api.checklistbank.org/dataset/3LXR/taxon/{id}/info"
DUTCH = ("nld", "nl")
GBIF_IMAGE_URL = "https://api.gbif.org/v1/image/cache/{width}x/occurrence/{key}/media/{md5}"
GBIF_INSTITUTION_URL = "https://api.gbif.org/v1/grscicoll/institution/{key}"
GBIF_LICENSE_CODES = {
    "CC0_1_0": "http://creativecommons.org/publicdomain/zero/1.0/",
    "CC_BY_4_0": "http://creativecommons.org/licenses/by/4.0/",
    "CC_BY_NC_4_0": "http://creativecommons.org/licenses/by-nc/4.0/"
}
GBIF_OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/{key}"
GBIF_SPECIES_URL = "https://api.gbif.org/v1/species/{id}"
GBIF_VERNACULAR_URL = "https://api.gbif.org/v1/species/{id}/vernacularNames?limit=1000"
LICENSE_URL = re.compile(r"https?://creativecommons\.org/(licenses|publicdomain)/([a-z-]+)/(\d\.\d)", re.IGNORECASE)
OCCURRENCE_PAGE_URL = "https://www.gbif.org/occurrence/{key}"
OCCURRENCE_SEARCH_URL = "https://api.gbif.org/v1/occurrence/search?{taxon}&mediaType=StillImage&limit=20"
OCCURRENCE_URL = re.compile(r"https?://(www\.)?gbif\.org/occurrence/(\d+)(?![\w])")
# From high to low; determines whether family and order belong in the description.
RANKS = (
    "kingdom",
    "phylum",
    "class",
    "order",
    "superfamily",
    "family",
    "subfamily",
    "tribe",
    "genus",
    "species",
    "subspecies",
    "variety",
    "form"
)
RANK_NAMES = {
    "class": "klasse",
    "family": "familie",
    "form": "vorm",
    "genus": "geslacht",
    "kingdom": "rijk",
    "order": "orde",
    "phylum": "stam",
    "species": "soort",
    "subfamily": "onderfamilie",
    "subspecies": "ondersoort",
    "superfamily": "superfamilie",
    "tribe": "tribus",
    "variety": "variëteit"
}
SPECIES_URL = re.compile(r"https?://(www\.)?gbif\.org/species/(\d+)(?![\w])")
TAXON_URL = re.compile(r"https?://(www\.)?gbif\.org/taxon/([A-Za-z0-9]+)(?![\w])")
# Placeholders for an unknown collector.
UNKNOWN_COLLECTORS = ("anonymous", "unknown")
# How some museums write a date in verbatimEventDate: day-month-year.
VERBATIM_DATE = re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})")

class GbifAdapter(SourceAdapter):
    name = "gbif"

    def __init__(self, image_width: int):
        self.image_width = image_width

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        if OCCURRENCE_URL.match(uri):
            self._fetch_occurrence(uri, fetcher)
            return
        for url in self._source_urls(uri):
            fetcher.get(url, self.name)
        image = _pick_image(fetcher.get_json(self._occurrences_url(uri), self.name), self.image_width)
        if image is not None:
            fetcher.download(image.download_url, self.name)

    def matches(self, uri: str) -> bool:
        return any(pattern.match(uri) is not None for pattern in (OCCURRENCE_URL, SPECIES_URL, TAXON_URL))

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        if OCCURRENCE_URL.match(uri):
            return self._normalize_occurrence(uri, cache)
        urls = self._source_urls(uri)
        data = cache.get_json(urls[0])
        if not isinstance(data, dict):
            logger.warning(f"No GBIF data in the cache for {uri}")
            return None
        if TAXON_URL.match(uri):
            taxon = _col_taxon(data)
        else:
            taxon = _gbif_taxon(data, cache.get_json(urls[1]))
        if taxon is None:
            logger.warning(f"Unusable GBIF response for {uri}")
            return None
        return SourceData(
            description = _description(taxon),
            fields = _fields(taxon),
            image = _pick_image(cache.get_json(self._occurrences_url(uri)), self.image_width),
            label = taxon["label"]
        )

    def _fetch_occurrence(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        """The specimen itself, its institution, its taxon and its own image."""
        occurrence = fetcher.get_json(_occurrence_url(uri), self.name)
        if not isinstance(occurrence, dict):
            return
        for url in _occurrence_links(occurrence):
            fetcher.get(url, self.name)
        image = _pick_image({"results": [occurrence]}, self.image_width)
        if image is not None:
            fetcher.download(image.download_url, self.name)

    def _normalize_occurrence(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        occurrence = cache.get_json(_occurrence_url(uri))
        if not isinstance(occurrence, dict):
            logger.warning(f"No GBIF data in the cache for {uri}")
            return None
        taxon = _occurrence_taxon(occurrence, cache)
        if taxon is None:
            logger.warning(f"Unusable GBIF response for {uri}")
            return None
        key = occurrence.get("institutionKey")
        institution = cache.get_json(GBIF_INSTITUTION_URL.format(key = key)) if key else None
        return SourceData(
            coordinates = _coordinates(occurrence),
            description = _specimen_description(taxon, _type_status(occurrence)),
            fields = _fields(taxon) | _specimen_fields(occurrence, institution),
            # Only the specimen's own image: a photo of another specimen would be misleading here.
            image = _pick_image({"results": [occurrence]}, self.image_width),
            label = taxon["label"]
        )

    def _occurrences_url(self, uri: str) -> str:
        """Observations and specimens of this taxon that have an image."""
        match = TAXON_URL.match(uri)
        if match:
            taxon = f"checklistKey={COL_CHECKLIST_KEY}&taxonKey={match.group(2)}"
        else:
            taxon = f"taxonKey={_species_key(uri)}"
        return OCCURRENCE_SEARCH_URL.format(taxon = taxon)

    def _source_urls(self, uri: str) -> list[str]:
        """The API URLs with the data of the taxon itself; the first is the main source."""
        match = TAXON_URL.match(uri)
        if match:
            return [COL_INFO_URL.format(id = match.group(2))]
        return _species_urls(_species_key(uri))

def license_name(value: str | None) -> tuple[str, str] | None:
    """Short name and URL of a Creative Commons license, or None if it is not a CC license."""
    if not value:
        return None
    value = GBIF_LICENSE_CODES.get(value.strip(), value.strip())
    match = LICENSE_URL.match(value)
    if match is None:
        return None
    kind, code, version = match.group(1).lower(), match.group(2).lower(), match.group(3)
    url = f"https://creativecommons.org/{kind}/{code}/{version}/"
    if kind == "publicdomain":
        if code == "zero":
            return f"CC0 {version}", url
        if code == "mark":
            return "Publiek domein", url
        return None
    return f"CC {code.upper()} {version}", url

def _col_taxon(data: dict) -> dict | None:
    usage = data.get("usage") or {}
    name = usage.get("name") or {}
    label = usage.get("label") or _join(name.get("scientificName"), name.get("authorship"))
    if not label:
        return None
    classification = data.get("classification") or []
    ranks = {item.get("rank"): item.get("name") for item in classification}
    # The direct parent is the parentId of the taxon, otherwise the lowest rank in the classification.
    parents = [item for item in classification if item.get("id") == usage.get("parentId")] or classification[-1:]
    return {
        "family": ranks.get("family"),
        "label": label,
        "order": ranks.get("order"),
        "parent": parents[0].get("name") if parents else None,
        "rank": (name.get("rank") or "").lower(),
        "vernacular": _dutch_names(data.get("vernacularNames"), "name")
    }

def _capitalize(text: str) -> str:
    return f"{text[0].upper()}{text[1:]}"

def _collection_date(occurrence: dict) -> str | None:
    """The date the specimen was collected, as YYYY, YYYY-MM or YYYY-MM-DD."""
    year, month, day = (occurrence.get(key) for key in ("year", "month", "day"))
    if isinstance(year, int):
        if not isinstance(month, int):
            return f"{year:04d}"
        if not isinstance(day, int):
            return f"{year:04d}-{month:02d}"
        return f"{year:04d}-{month:02d}-{day:02d}"
    # GBIF leaves year empty when it can't parse the date; some museums use day-month-year.
    match = VERBATIM_DATE.fullmatch((occurrence.get("verbatimEventDate") or "").strip())
    if match is None:
        return None
    day, month, year = (int(part) for part in match.groups())
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"

def _collectors(value: str | None) -> list[str]:
    """The collectors of a specimen; recordedBy separates several with a pipe."""
    names = [name.strip() for name in (value or "").split("|")]
    return _values(*(name for name in names if name.lower() not in UNKNOWN_COLLECTORS))

def _coordinates(occurrence: dict) -> Coordinates | None:
    lat, lon = occurrence.get("decimalLatitude"), occurrence.get("decimalLongitude")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return Coordinates(lat = float(lat), lon = float(lon))

def _credit(media: dict, occurrence: dict) -> str | None:
    """Creator and rights holder of the image, otherwise the provenance of the record."""
    parts = []
    for value in (media.get("creator"), media.get("rightsHolder") or occurrence.get("rightsHolder")):
        if value and value not in parts:
            parts.append(value)
    if parts:
        return ", ".join(parts)
    return occurrence.get("datasetName") or occurrence.get("institutionCode")

def _depth(occurrence: dict) -> str | None:
    """The depth in metres at which the specimen was collected."""
    minimum, maximum = occurrence.get("minimumDepthInMeters"), occurrence.get("maximumDepthInMeters")
    if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)) and round(minimum) != round(maximum):
        return f"{round(minimum)}–{round(maximum)} m"
    depth = occurrence.get("depth")
    if isinstance(depth, (int, float)):
        return f"{round(depth)} m"
    return occurrence.get("verbatimDepth")

def _description(taxon: dict) -> str | None:
    """Rank and position in the classification, with the Dutch name if the source has one."""
    text = _taxon_text(taxon)
    if taxon["vernacular"]:
        return f"{taxon['vernacular'][0]}, {text}."
    return f"{_capitalize(text)}."

def _dutch_names(
    names: list | None,
    field: str
) -> list[str]:
    """All Dutch names, the preferred name first."""
    dutch = [item for item in names or [] if item.get("language") in DUTCH and item.get(field)]
    dutch.sort(key = lambda item: not item.get("preferred"))
    return _values(*(item[field] for item in dutch))

def _fields(taxon: dict) -> dict[str, list[str]]:
    fields = {
        "family": _values(taxon["family"]),
        "order": _values(taxon["order"]),
        "parent_taxon": _values(taxon["parent"]),
        "scientific_name": _values(taxon["label"]),
        "taxon_rank": _values(RANK_NAMES.get(taxon["rank"])),
        "vernacular_name": taxon["vernacular"]
    }
    return {key: values for key, values in fields.items() if values}

def _gbif_taxon(
    data: dict,
    vernacular: dict | list | None
) -> dict | None:
    label = data.get("scientificName") or data.get("canonicalName")
    if not label:
        return None
    names = vernacular.get("results") if isinstance(vernacular, dict) else None
    return {
        "family": data.get("family"),
        "label": label,
        "order": data.get("order"),
        "parent": data.get("parent"),
        "rank": (data.get("rank") or "").lower(),
        "vernacular": _dutch_names(names, "vernacularName")
    }

def _institution_name(
    occurrence: dict,
    institution: dict | list | None
) -> str | None:
    """The full name from GRSciColl, otherwise the institution code of the record."""
    if isinstance(institution, dict) and institution.get("name"):
        return institution["name"]
    return occurrence.get("institutionCode")

def _join(*parts: str | None) -> str | None:
    text = " ".join(part for part in parts if part)
    return text or None

def _locality(occurrence: dict) -> str | None:
    """Where the specimen was found, from specific to general, without repeating parts."""
    parts = []
    candidates = (
        occurrence.get("locality") or occurrence.get("verbatimLocality"),
        occurrence.get("stateProvince"),
        occurrence.get("waterBody"),
        occurrence.get("country")
    )
    for value in candidates:
        value = (value or "").strip(" ;,")
        if value and not any(value.lower() in part.lower() for part in parts):
            parts.append(value)
    return ", ".join(parts) or None

def _occurrence_key(uri: str) -> str:
    match = OCCURRENCE_URL.match(uri)
    if match is None:
        raise ValueError(f"Not a GBIF occurrence URI: {uri}")
    return match.group(2)

def _occurrence_links(occurrence: dict) -> list[str]:
    """The API URLs that an occurrence refers to: its institution and its taxon."""
    urls = []
    if occurrence.get("institutionKey"):
        urls.append(GBIF_INSTITUTION_URL.format(key = occurrence["institutionKey"]))
    if occurrence.get("taxonKey"):
        urls += _species_urls(occurrence["taxonKey"])
    return urls

def _occurrence_taxon(
    occurrence: dict,
    cache: Cache
) -> dict | None:
    """The taxon of a specimen from the GBIF species API, otherwise from the occurrence itself.

    The label is always the name on the specimen, which can be an older synonym.
    """
    label = occurrence.get("scientificName")
    if not label:
        return None
    taxon = None
    key = occurrence.get("taxonKey")
    if key:
        urls = _species_urls(key)
        species = cache.get_json(urls[0])
        if isinstance(species, dict):
            taxon = _gbif_taxon(species, cache.get_json(urls[1]))
    if taxon is None:
        taxon = {
            "family": occurrence.get("family"),
            "order": occurrence.get("order"),
            "parent": None,
            "rank": (occurrence.get("taxonRank") or "").lower(),
            "vernacular": []
        }
    taxon["label"] = label
    return taxon

def _occurrence_url(uri: str) -> str:
    return GBIF_OCCURRENCE_URL.format(key = _occurrence_key(uri))

def _pick_image(
    search: dict | list | None,
    width: int
) -> ImageInfo | None:
    """The first image with its own Creative Commons license and an attribution."""
    if not isinstance(search, dict):
        return None
    for occurrence in search.get("results") or []:
        key = occurrence.get("key")
        for media in occurrence.get("media") or []:
            identifier = media.get("identifier")
            license_info = license_name(media.get("license"))
            credit = _credit(media, occurrence)
            if media.get("type") != "StillImage" or not key or not identifier or license_info is None or not credit:
                continue
            md5 = hashlib.md5(identifier.encode("utf-8")).hexdigest()
            return ImageInfo(
                credit = credit,
                download_url = GBIF_IMAGE_URL.format(width = width, key = key, md5 = md5),
                license = license_info[0],
                license_url = license_info[1],
                source_url = OCCURRENCE_PAGE_URL.format(key = key)
            )
    return None

def _species_key(uri: str) -> str:
    match = SPECIES_URL.match(uri)
    if match is None:
        raise ValueError(f"Not a GBIF URI: {uri}")
    return match.group(2)

def _species_urls(key: int | str) -> list[str]:
    """The GBIF species and its vernacular names."""
    return [GBIF_SPECIES_URL.format(id = key), GBIF_VERNACULAR_URL.format(id = key)]

def _specimen_description(
    taxon: dict,
    type_status: str | None
) -> str:
    """For example: Holotype van een soort uit de familie Macrouridae (orde Gadiformes)."""
    return f"{_capitalize(type_status or 'exemplaar')} van een {_taxon_text(taxon)}."

def _specimen_fields(
    occurrence: dict,
    institution: dict | list | None
) -> dict[str, list[str]]:
    """What GBIF knows about the specimen itself, as opposed to its taxon."""
    fields = {
        "catalog_number": _values(occurrence.get("catalogNumber")),
        "collection": _values(_institution_name(occurrence, institution)),
        "collection_date": _values(_collection_date(occurrence)),
        "collector": _collectors(occurrence.get("recordedBy")),
        "depth": _values(_depth(occurrence)),
        "locality": _values(_locality(occurrence)),
        "type_status": _values(_type_status(occurrence))
    }
    return {key: values for key, values in fields.items() if values}

def _taxon_text(taxon: dict) -> str:
    """Rank and position in the classification, for example: soort uit de familie Macrouridae (orde Gadiformes)."""
    rank = taxon["rank"]
    depth = RANKS.index(rank) if rank in RANKS else len(RANKS)
    text = RANK_NAMES.get(rank, "taxon")
    family, order = taxon["family"], taxon["order"]
    if family and depth > RANKS.index("family"):
        text += f" uit de familie {family}"
        if order:
            text += f" (orde {order})"
    elif order and depth > RANKS.index("order"):
        text += f" uit de orde {order}"
    return text

def _type_status(occurrence: dict) -> str | None:
    """Holotype, syntype and so on, in lower case; the API gives a string or a list."""
    value = occurrence.get("typeStatus")
    if isinstance(value, list):
        value = value[0] if value else None
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().lower()

def _values(*values: str | None) -> list[str]:
    """Non-empty, deduplicated values in source order."""
    result = []
    for value in values:
        value = (value or "").strip()
        if value and value not in result:
            result.append(value)
    return result
