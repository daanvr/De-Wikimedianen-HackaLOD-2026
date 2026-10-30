"""Adapter voor taxa op GBIF: Catalogue of Life-taxa (/taxon/…) en GBIF-soorten (/species/…)."""
from __future__ import annotations

from typing import TYPE_CHECKING
import hashlib
import re

from loguru import logger

from siboga.models import ImageInfo, SourceData
from siboga.sources.base import SourceAdapter

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

# De taxonpagina's van GBIF gebruiken de uitgebreide release van de Catalogue of Life (COL XR).
COL_CHECKLIST_KEY = "7ddf754f-d193-4cc9-b351-99906754a03b"
COL_INFO_URL = "https://api.checklistbank.org/dataset/3LXR/taxon/{id}/info"
DUTCH = ("nld", "nl")
GBIF_IMAGE_URL = "https://api.gbif.org/v1/image/cache/{width}x/occurrence/{key}/media/{md5}"
GBIF_LICENSE_CODES = {
    "CC0_1_0": "http://creativecommons.org/publicdomain/zero/1.0/",
    "CC_BY_4_0": "http://creativecommons.org/licenses/by/4.0/",
    "CC_BY_NC_4_0": "http://creativecommons.org/licenses/by-nc/4.0/"
}
GBIF_SPECIES_URL = "https://api.gbif.org/v1/species/{id}"
GBIF_VERNACULAR_URL = "https://api.gbif.org/v1/species/{id}/vernacularNames?limit=1000"
LICENSE_URL = re.compile(r"https?://creativecommons\.org/(licenses|publicdomain)/([a-z-]+)/(\d\.\d)", re.IGNORECASE)
OCCURRENCE_PAGE_URL = "https://www.gbif.org/occurrence/{key}"
OCCURRENCE_SEARCH_URL = "https://api.gbif.org/v1/occurrence/search?{taxon}&mediaType=StillImage&limit=20"
# Van hoog naar laag; bepaalt of familie en orde in de beschrijving horen.
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

class GbifAdapter(SourceAdapter):
    name = "gbif"

    def __init__(self, image_width: int):
        self.image_width = image_width

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        for url in self._source_urls(uri):
            fetcher.get(url, self.name)
        image = _pick_image(fetcher.get_json(self._occurrences_url(uri), self.name), self.image_width)
        if image is not None:
            fetcher.download(image.download_url, self.name)

    def matches(self, uri: str) -> bool:
        return TAXON_URL.match(uri) is not None or SPECIES_URL.match(uri) is not None

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        urls = self._source_urls(uri)
        data = cache.get_json(urls[0])
        if not isinstance(data, dict):
            logger.warning(f"Geen GBIF-gegevens in de cache voor {uri}")
            return None
        if TAXON_URL.match(uri):
            taxon = _col_taxon(data)
        else:
            taxon = _gbif_taxon(data, cache.get_json(urls[1]))
        if taxon is None:
            logger.warning(f"Onbruikbaar GBIF-antwoord voor {uri}")
            return None
        return SourceData(
            description = _description(taxon),
            fields = _fields(taxon),
            image = _pick_image(cache.get_json(self._occurrences_url(uri)), self.image_width),
            label = taxon["label"]
        )

    def _occurrences_url(self, uri: str) -> str:
        """Waarnemingen en specimens van dit taxon met een plaatje."""
        match = TAXON_URL.match(uri)
        if match:
            taxon = f"checklistKey={COL_CHECKLIST_KEY}&taxonKey={match.group(2)}"
        else:
            taxon = f"taxonKey={_species_key(uri)}"
        return OCCURRENCE_SEARCH_URL.format(taxon = taxon)

    def _source_urls(self, uri: str) -> list[str]:
        """De API-URL's met de gegevens van het taxon zelf; de eerste is de hoofdbron."""
        match = TAXON_URL.match(uri)
        if match:
            return [COL_INFO_URL.format(id = match.group(2))]
        key = _species_key(uri)
        return [GBIF_SPECIES_URL.format(id = key), GBIF_VERNACULAR_URL.format(id = key)]

def license_name(value: str | None) -> tuple[str, str] | None:
    """Korte naam en URL van een Creative Commons-licentie, of None als het geen CC-licentie is."""
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
    # De directe ouder is de parentId van het taxon, anders de laagste rang in de classificatie.
    parents = [item for item in classification if item.get("id") == usage.get("parentId")] or classification[-1:]
    return {
        "family": ranks.get("family"),
        "label": label,
        "order": ranks.get("order"),
        "parent": parents[0].get("name") if parents else None,
        "rank": (name.get("rank") or "").lower(),
        "vernacular": _dutch_names(data.get("vernacularNames"), "name")
    }

def _credit(media: dict, occurrence: dict) -> str | None:
    """Maker en rechthebbende van het plaatje, anders de herkomst van het record."""
    parts = []
    for value in (media.get("creator"), media.get("rightsHolder") or occurrence.get("rightsHolder")):
        if value and value not in parts:
            parts.append(value)
    if parts:
        return ", ".join(parts)
    return occurrence.get("datasetName") or occurrence.get("institutionCode")

def _description(taxon: dict) -> str | None:
    """Rang en plaats in de classificatie, met de Nederlandse naam als de bron die heeft."""
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
    if taxon["vernacular"]:
        return f"{taxon['vernacular'][0]}, {text}."
    return f"{text[0].upper()}{text[1:]}."

def _dutch_names(
    names: list | None,
    field: str
) -> list[str]:
    """Alle Nederlandse namen, de voorkeursnaam eerst."""
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

def _join(*parts: str | None) -> str | None:
    text = " ".join(part for part in parts if part)
    return text or None

def _pick_image(
    search: dict | list | None,
    width: int
) -> ImageInfo | None:
    """Het eerste plaatje met een eigen Creative Commons-licentie en een bronvermelding."""
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
        raise ValueError(f"Geen GBIF-URI: {uri}")
    return match.group(2)

def _values(*values: str | None) -> list[str]:
    """Niet-lege, ontdubbelde waarden in bronvolgorde."""
    result = []
    for value in values:
        value = (value or "").strip()
        if value and value not in result:
            result.append(value)
    return result
