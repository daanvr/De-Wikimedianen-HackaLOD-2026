"""Adapter for records of the Stadsarchief Amsterdam, through their Linked Data (JSON-LD) at id.archief.amsterdam."""
from __future__ import annotations

from typing import TYPE_CHECKING
import re

from loguru import logger

from siboga.models import ImageInfo, SourceData
from siboga.sources.base import SourceAdapter
from siboga.sources.gbif import license_name

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

# The beta site fetches this same JSON-LD itself; the same address returns HTML or Turtle with a different Accept.
ACCEPT_JSON_LD = {"Accept": "application/ld+json"}
DCTERMS = "http://purl.org/dc/terms/"
DEFAULT_CREDIT = "Stadsarchief Amsterdam"
ID_BASE = "https://id.archief.amsterdam/"
ISO_DATE = re.compile(r"\d{4}(-\d{2}(-\d{2})?)?")
LICENSE_PROPERTIES = (
    "http://schema.org/license",
    f"{DCTERMS}license",
    f"{DCTERMS}rights",
    "http://www.europeana.eu/schemas/edm/rights"
)
MEMORIX = "http://memorix.io/ontology#"
PNV = "https://w3id.org/pnv#"
RECORD_URL = re.compile(
    r"https?://(beta\.)?archief\.amsterdam/(zoeken/)?detail/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE
)
RICO = "https://www.ica.org/standards/RiC/ontology#"
SAA = "https://data.archief.amsterdam/ontology#"
SCHEMA = "http://schema.org/"
SKOS_LABEL = "http://www.w3.org/2004/02/skos/core#prefLabel"
# Memorix stores a bare year as 1 January of that year.
YEAR_ONLY = re.compile(r"(\d{4})-01-01")

class ArchiefAmsterdamAdapter(SourceAdapter):
    name = "archief_amsterdam"

    def __init__(self, image_width: int):
        self.image_width = image_width

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        record_iri = _record_iri(uri)
        graph = _graph(fetcher.get_json(record_iri, self.name, headers = ACCEPT_JSON_LD))
        if record_iri not in graph:
            logger.warning(f"No record in the Stadsarchief JSON-LD for {uri}")
            return
        for person_iri in _person_iris(graph, record_iri):
            fetcher.get(person_iri, self.name, headers = ACCEPT_JSON_LD)
        image = _image(graph, record_iri, uri, self.image_width)
        if image is not None:
            fetcher.download(image.download_url, self.name)

    def matches(self, uri: str) -> bool:
        return RECORD_URL.match(uri) is not None

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        record_iri = _record_iri(uri)
        graph = _graph(cache.get_json(record_iri))
        record = graph.get(record_iri)
        if record is None:
            logger.warning(f"No Stadsarchief record in the cache for {uri}")
            return None
        return SourceData(
            description = _description(graph, record_iri, cache),
            fields = _fields(graph, record_iri),
            image = _image(graph, record_iri, uri, self.image_width),
            label = _literal(record, f"{RICO}title") or _record_title(graph, record_iri)
        )

def _as_list(value: object) -> list:
    if isinstance(value, dict) and "@list" in value:
        return value["@list"]
    return value if isinstance(value, list) else [value]

def _capitalize(text: str) -> str:
    return f"{text[0].upper()}{text[1:]}" if text else text

def _date(record: dict) -> str | None:
    """The normalized date as YYYY, YYYY-MM or YYYY-MM-DD."""
    date = _literal(record, f"{RICO}normalizedDateValue")
    if not date:
        return None
    date = date.split("T", 1)[0]
    if YEAR_ONLY.fullmatch(date):
        return date[:4]
    return date if ISO_DATE.fullmatch(date) else None

def _description(
    graph: dict,
    record_iri: str,
    cache: Cache
) -> str | None:
    """Document type, specifications, persons involved and archive, in the archive's own words."""
    record = graph[record_iri]
    sentences = []
    form = _label(graph, _ref(record, f"{RICO}hasDocumentaryFormType"))
    category = _label(graph, _ref(record, f"{RICO}hasOrHadCategory"))
    if form and category:
        sentences.append(f"{_capitalize(form)} ({category})")
    elif form or category:
        sentences.append(_capitalize(form or category))
    for node in _nodes(graph, record, f"{SAA}hasSpecification"):
        kind = _label(graph, _ref(node, f"{SAA}specificationType"))
        value = _literal(node, f"{SAA}specificationTextualValue")
        if value:
            sentences.append(f"{_capitalize(kind)}: {value}" if kind else value)
    for node in _nodes(graph, record, f"{RICO}hasOrHadSubject"):
        person = _person(_ref(node, f"{SAA}relatedPersonObservation"), cache)
        role = _label(graph, _ref(node, f"{SAA}relatedPersonObservationRole"))
        if person:
            sentences.append(f"{_capitalize(role)}: {person}" if role else person)
    archive = _record_title(graph, _ref(record, f"{SAA}isOrWasAlsoIncludedIn"))
    if archive:
        sentences.append(f"Archief: {archive}")
    return ". ".join(sentences) + "." if sentences else None

def _dutch_date(value: str) -> str:
    """2026-10-30 becomes 30-10-2026; everything else stays as it is."""
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    return f"{match.group(3)}-{match.group(2)}-{match.group(1)}" if match else value

def _expand(term: str, context: dict) -> str:
    prefix, _, local = term.partition(":")
    namespace = context.get(prefix)
    return f"{namespace}{local}" if isinstance(namespace, str) and local else term

def _fields(graph: dict, record_iri: str) -> dict[str, list[str]]:
    """Date of the document and the archive (fonds) that contains it."""
    record = graph[record_iri]
    fields = {}
    date = _date(record)
    if date:
        fields["created"] = [date]
        fields["point_in_time"] = [date]
    archive = _record_title(graph, _ref(record, f"{SAA}isOrWasAlsoIncludedIn"))
    if archive:
        fields["archive"] = [archive]
    return fields

def _graph(data: dict | list | None) -> dict[str, dict[str, list]]:
    """The JSON-LD as {iri: {full property IRI: [values]}}; a reference is {"@id": iri}."""
    if not isinstance(data, dict):
        return {}
    context = data.get("@context") if isinstance(data.get("@context"), dict) else {}
    graph = {}
    for node in data.get("@graph") or []:
        if not isinstance(node, dict) or "@id" not in node:
            continue
        properties = {}
        for key, value in node.items():
            if key == "@id":
                continue
            if key == "@type":
                properties[key] = [{"@id": _expand(item, context)} for item in _as_list(value)]
                continue
            properties[_expand(key, context)] = [_term(item, context) for item in _as_list(value)]
        graph[_expand(node["@id"], context)] = properties
    return graph

def _image(
    graph: dict,
    record_iri: str,
    uri: str,
    width: int
) -> ImageInfo | None:
    """The first scan of the record, but only if the archive states a license for it."""
    uuid = record_iri.rsplit("/", 1)[1]
    rights = graph.get(f"{ID_BASE}resources/records/{uuid}/accessibility_and_rights", {})
    license_info = None
    for node in (rights, graph[record_iri]):
        for prop in LICENSE_PROPERTIES:
            license_info = license_info or license_name(_ref(node, prop) or _literal(node, prop))
    if license_info is None:
        logger.debug(f"No license for the scans of {uri}; no image")
        return None
    context = graph.get(f"{ID_BASE}resources/records/{uuid}/context", {})
    assets = context.get(f"{MEMORIX}hasDigitalDocument") or []
    asset = graph.get(assets[0].get("@id"), {}) if assets and isinstance(assets[0], dict) else {}
    service = _ref(asset, f"{MEMORIX}iiif")
    if not service:
        return None
    asset_width = _literal(asset, f"{SCHEMA}width")
    size = "max" if asset_width and asset_width.isdigit() and int(asset_width) <= width else f"{width},"
    holder = _record_title(graph, _ref(rights, f"{SCHEMA}copyrightHolder"))
    return ImageInfo(
        credit = holder or DEFAULT_CREDIT,
        download_url = f"{service}/full/{size}/0/default.jpg",
        license = license_info[0],
        license_url = license_info[1],
        source_url = uri
    )

def _label(graph: dict, iri: str | None) -> str | None:
    return _literal(graph.get(iri, {}), SKOS_LABEL) if iri else None

def _literal(node: dict, prop: str) -> str | None:
    for value in node.get(prop) or []:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None

def _nodes(
    graph: dict,
    node: dict,
    prop: str
) -> list[dict]:
    return [graph[value["@id"]] for value in node.get(prop) or [] if isinstance(value, dict) and value.get("@id") in graph]

def _person(iri: str | None, cache: Cache) -> str | None:
    """Name and date of birth from the person observation's own JSON-LD."""
    if not iri:
        return None
    graph = _graph(cache.get_json(iri))
    node = graph.get(iri)
    if node is None:
        return None
    names = _nodes(graph, node, f"{PNV}hasName")
    name = _literal(names[0], f"{PNV}literalName") if names else None
    name = name or _record_title(graph, iri)
    if not name:
        return None
    birth = _literal(node, f"{SCHEMA}birthDate")
    return f"{name} (geboren {_dutch_date(birth)})" if birth else name

def _person_iris(graph: dict, record_iri: str) -> list[str]:
    iris = []
    for node in _nodes(graph, graph[record_iri], f"{RICO}hasOrHadSubject"):
        iri = _ref(node, f"{SAA}relatedPersonObservation")
        if iri and iri.startswith(ID_BASE) and iri not in iris:
            iris.append(iri)
    return iris

def _record_iri(uri: str) -> str:
    match = RECORD_URL.match(uri)
    if match is None:
        raise ValueError(f"Not a Stadsarchief Amsterdam URI: {uri}")
    return f"{ID_BASE}{match.group(3).lower()}"

def _record_title(graph: dict, iri: str | None) -> str | None:
    """Title of another record, from its context node in the same JSON-LD."""
    if not iri or not iri.startswith(ID_BASE):
        return None
    uuid = iri.rstrip("/").rsplit("/", 1)[1]
    return _literal(graph.get(f"{ID_BASE}resources/records/{uuid}/context", {}), f"{DCTERMS}title")

def _ref(node: dict, prop: str) -> str | None:
    for value in node.get(prop) or []:
        if isinstance(value, dict) and value.get("@id"):
            return value["@id"]
    return None

def _term(value: object, context: dict) -> object:
    """A reference becomes {"@id": full IRI}, a literal a string."""
    if isinstance(value, dict):
        if "@id" in value:
            return {"@id": _expand(value["@id"], context)}
        if "@value" in value:
            return str(value["@value"])
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
