"""Adapter for items on Wikidata, through the full entity JSON."""
from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode
import re

from loguru import logger

from siboga.models import Coordinates, SourceData, SourceRef
from siboga.sources.base import WIKIMEDIA_RATE_LIMIT, SourceAdapter
from siboga.sources.commons import fetch_image, read_image

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

API_URL = "https://www.wikidata.org/w/api.php"
# Field to property; for a date only the first statement counts.
DATE_FIELDS = {
    "birth_date": "P569",
    "created": "P571",
    "death_date": "P570",
    "end_date": "P582",
    "inception": "P571",
    "point_in_time": "P585",
    "publication_date": "P577",
    "start_date": "P580"
}
DESCRIPTION_LANGUAGES = ("nl", "en")
DUTCH = "Q7411"
EARTH = "http://www.wikidata.org/entity/Q2"
ENTITY_URL = re.compile(r"https?://(www\.)?wikidata\.org/(wiki|entity)/(Q\d+)(?!\w)")
# Field to properties that refer to an item; the label of that item is shown.
ITEM_FIELDS = {
    "author": ("P50",),
    "birth_place": ("P19",),
    "collection": ("P195",),
    "country": ("P17",),
    "creator": ("P170",),
    "death_place": ("P20",),
    "employer": ("P108",),
    "location": ("P276",),
    "occupation": ("P106",),
    "parent_taxon": ("P171",),
    "participant": ("P710",),
    "published_in": ("P1433",),
    "publisher": ("P123",),
    "taxon_rank": ("P105",)
}
LABEL_CHUNK_SIZE = 50
# Property to URI template: external identifiers that are followed exactly one hop, to the linked adapters.
LINKED_SOURCES = {
    "P1006": "http://data.bibliotheken.nl/id/thes/p{}"
}
LABEL_LANGUAGES = ("nl", "en", "mul")
QID = re.compile(r"Q\d+")
# Field to properties with plain text as value.
STRING_FIELDS = {
    "author": ("P2093",),
    "scientific_name": ("P225",)
}
TIME_VALUE = re.compile(r"([+-])(\d+)-(\d{2})-(\d{2})T")
VERNACULAR_LANGUAGE = "nl"

class WikidataAdapter(SourceAdapter):
    name = "wikidata"
    rate_limit = WIKIMEDIA_RATE_LIMIT

    def __init__(
        self,
        image_width: int,
        linked_adapters: list[SourceAdapter] | None = None
    ):
        self.image_width = image_width
        self.linked_adapters = linked_adapters or []

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        qid = _qid(uri)
        entity = _entity(fetcher.get_json(entity_url(qid), self.name), qid)
        if entity is None:
            logger.warning(f"No entity from Wikidata for {qid}")
            return
        for url in labels_urls(_referenced_ids(entity)):
            fetcher.get_json(url, self.name)
        image = _first_value(entity, "P18")
        if isinstance(image, str):
            fetch_image(image, self.image_width, fetcher, self.name)
        for adapter, linked_uri in self._linked(entity):
            try:
                adapter.fetch(linked_uri, fetcher)
            except Exception as error:
                # A broken linked source must not stop the Wikidata item itself.
                logger.warning(f"Fetching linked {adapter.name} source failed for {qid}: {error!r}")

    def matches(self, uri: str) -> bool:
        return ENTITY_URL.match(uri) is not None

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        qid = _qid(uri)
        entity = _entity(cache.get_json(entity_url(qid)), qid)
        if entity is None:
            logger.warning(f"No entity from Wikidata in the cache for {qid}")
            return None
        labels = _read_labels(_referenced_ids(entity), cache)
        image = _first_value(entity, "P18")
        source = SourceData(
            coordinates = _coordinates(_first_value(entity, "P625")),
            description = _text(entity.get("descriptions"), DESCRIPTION_LANGUAGES),
            fields = _fields(entity, labels),
            full_text_url = _full_text_url(entity),
            image = read_image(image, self.image_width, cache) if isinstance(image, str) else None,
            label = _text(entity.get("labels"), LABEL_LANGUAGES)
        )
        for adapter, linked_uri in self._linked(entity):
            try:
                linked = adapter.normalize(linked_uri, cache)
            except Exception as error:
                logger.warning(f"Normalizing linked {adapter.name} source failed for {qid}: {error!r}")
                continue
            if linked is not None:
                source.fill_from(linked, SourceRef(name = adapter.name, uri = linked_uri))
        return source

    def _linked(self, entity: dict) -> list[tuple[SourceAdapter, str]]:
        """The linked sources of this entity that have an adapter, in the order of LINKED_SOURCES."""
        linked = []
        for prop, template in LINKED_SOURCES.items():
            for value in _values(entity, prop):
                if not isinstance(value, str) or not value.strip():
                    continue
                uri = template.format(value.strip())
                adapter = next((adapter for adapter in self.linked_adapters if adapter.matches(uri)), None)
                if adapter is not None:
                    linked.append((adapter, uri))
        return linked

def entity_url(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

def labels_urls(qids: list[str]) -> list[str]:
    """API URLs for the labels of items, sorted and in batches of 50; always the same for the same input."""
    ordered = sorted(set(qids), key = lambda qid: int(qid[1:]))
    urls = []
    for start in range(0, len(ordered), LABEL_CHUNK_SIZE):
        params = [
            ("action", "wbgetentities"),
            ("format", "json"),
            ("props", "labels"),
            ("languages", "|".join(LABEL_LANGUAGES)),
            ("ids", "|".join(ordered[start:start + LABEL_CHUNK_SIZE]))
        ]
        urls.append(f"{API_URL}?{urlencode(params, quote_via = quote)}")
    return urls

def _add(values: list[str], value: str | None) -> None:
    """Adds a value if it is not empty and not already present."""
    if value and value.strip() and value.strip() not in values:
        values.append(value.strip())

def _best_statements(entity: dict, prop: str) -> list[dict]:
    """Statements with a value: only the preferred ones if there are any, never deprecated."""
    statements = [
        statement for statement in entity.get("claims", {}).get(prop, [])
        if statement.get("rank") != "deprecated"
        and statement.get("mainsnak", {}).get("snaktype") == "value"
    ]
    preferred = [statement for statement in statements if statement.get("rank") == "preferred"]
    return preferred or statements

def _coordinates(value: dict | None) -> Coordinates | None:
    if not isinstance(value, dict) or value.get("globe", EARTH) != EARTH:
        return None
    try:
        return Coordinates(lat = float(value["latitude"]), lon = float(value["longitude"]))
    except (KeyError, TypeError, ValueError):
        return None

def _entity(data: dict | list | None, qid: str) -> dict | None:
    """The entity from the response; after a redirect it is under a different Q number."""
    if not isinstance(data, dict):
        return None
    entities = data.get("entities") or {}
    if qid in entities:
        return entities[qid]
    if len(entities) == 1:
        return next(iter(entities.values()))
    return None

def _fields(entity: dict, labels: dict[str, str]) -> dict[str, list[str]]:
    """All fields this entity can fill, with the names from fields.toml."""
    fields: dict[str, list[str]] = {}
    for key, prop in DATE_FIELDS.items():
        _add(fields.setdefault(key, []), _time(_first_value(entity, prop)))
    for key, props in ITEM_FIELDS.items():
        for prop in props:
            for qid in _item_ids(entity, prop):
                _add(fields.setdefault(key, []), labels.get(qid))
    for key, props in STRING_FIELDS.items():
        for prop in props:
            for value in _values(entity, prop):
                _add(fields.setdefault(key, []), value if isinstance(value, str) else None)
    for value in _values(entity, "P1843"):
        if isinstance(value, dict) and value.get("language") == VERNACULAR_LANGUAGE:
            _add(fields.setdefault("vernacular_name", []), value.get("text"))
    return {key: values for key, values in sorted(fields.items()) if values}

def _first_value(entity: dict, prop: str) -> object:
    values = _values(entity, prop)
    return values[0] if values else None

def _full_text_url(entity: dict) -> str | None:
    """The first "full work available at URL" (P953); one in Dutch (language of work, P407) goes first."""
    urls = []
    for statement in _best_statements(entity, "P953"):
        value = statement["mainsnak"].get("datavalue", {}).get("value")
        if not isinstance(value, str) or not re.match(r"https?://", value):
            continue
        qualifiers = statement.get("qualifiers", {}).get("P407", [])
        languages = [_item_id(qualifier.get("datavalue", {}).get("value")) for qualifier in qualifiers]
        urls.append((DUTCH not in languages, len(urls), value))
    return min(urls)[2] if urls else None

def _item_id(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    qid = value.get("id") or (f"Q{value['numeric-id']}" if value.get("numeric-id") else None)
    return qid if isinstance(qid, str) and QID.fullmatch(qid) else None

def _item_ids(entity: dict, prop: str) -> list[str]:
    return [qid for qid in (_item_id(value) for value in _values(entity, prop)) if qid]

def _qid(uri: str) -> str:
    match = ENTITY_URL.match(uri)
    if match is None:
        raise ValueError(f"Not a Wikidata URI: {uri}")
    return match.group(3)

def _read_labels(qids: list[str], cache: Cache) -> dict[str, str]:
    """Labels of items from the cache, as Q number to label; items without a label are omitted."""
    labels = {}
    for url in labels_urls(qids):
        data = cache.get_json(url)
        if not isinstance(data, dict):
            logger.warning(f"No labels from Wikidata in the cache for {url}")
            continue
        for qid, entity in (data.get("entities") or {}).items():
            label = _text(entity.get("labels"), LABEL_LANGUAGES) if isinstance(entity, dict) else None
            if not label:
                continue
            labels[qid] = label
            source = (entity.get("redirects") or {}).get("from")
            if source:
                labels[source] = label
    return labels

def _referenced_ids(entity: dict) -> list[str]:
    """All items the fields refer to; their labels are needed."""
    return [qid for props in ITEM_FIELDS.values() for prop in props for qid in _item_ids(entity, prop)]

def _text(values: dict | None, languages: tuple[str, ...]) -> str | None:
    for language in languages:
        text = (values or {}).get(language, {}).get("value")
        if text:
            return text
    return None

def _time(value: dict | None) -> str | None:
    """Wikidata time as an ISO string, as precise as the precision allows."""
    if not isinstance(value, dict):
        return None
    match = TIME_VALUE.match(str(value.get("time", "")))
    if match is None:
        return None
    sign, year, month, day = match.groups()
    precision = int(value.get("precision", 9))
    text = f"{'-' if sign == '-' else ''}{int(year):04d}"
    if precision >= 10 and month != "00":
        text += f"-{month}"
        if precision >= 11 and day != "00":
            text += f"-{day}"
    return text

def _values(entity: dict, prop: str) -> list[object]:
    """The values of the best statements, in order."""
    return [statement["mainsnak"].get("datavalue", {}).get("value") for statement in _best_statements(entity, prop)]
