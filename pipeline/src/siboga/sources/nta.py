"""Adapter for persons in the NTA (Nederlandse Thesaurus van Auteursnamen) of the KB, as JSON-LD."""
from __future__ import annotations

from typing import TYPE_CHECKING
import re

from loguru import logger

from siboga.models import SourceData
from siboga.sources.base import RateLimit, SourceAdapter

if TYPE_CHECKING:
    from siboga.cache import Cache
    from siboga.fetcher import Fetcher

# The IRI redirects to api.bibliotheken.nl, which returns expanded JSON-LD for this Accept.
ACCEPT_JSON_LD = {"Accept": "application/ld+json"}
# Descriptions that only cite where the KB got its information from.
CITATION = re.compile(r"^bron:", re.IGNORECASE)
IRI_BASE = "http://data.bibliotheken.nl/id/thes/p"
ISO_DATE = re.compile(r"\d{4}(-\d{2}(-\d{2})?)?")
PERSON_URL = re.compile(r"https?://data\.bibliotheken\.nl/id/thes/p(\d{8}[\dX])(?![\w])", re.IGNORECASE)
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
SCHEMA = "http://schema.org/"
# A work's label is "title / statement of responsibility"; only the title is shown.
TITLE_SEPARATOR = " / "

class NtaAdapter(SourceAdapter):
    name = "nta"
    rate_limit = RateLimit(min_interval_seconds = 1.0)

    def fetch(
        self,
        uri: str,
        fetcher: Fetcher
    ) -> None:
        # Works are in the same response, so this is the only request; links are never followed.
        fetcher.get_json(person_iri(uri), self.name, headers = ACCEPT_JSON_LD)

    def matches(self, uri: str) -> bool:
        return PERSON_URL.match(uri) is not None

    def normalize(
        self,
        uri: str,
        cache: Cache
    ) -> SourceData | None:
        iri = person_iri(uri)
        graph = _graph(cache.get_json(iri))
        person = graph.get(iri)
        if person is None:
            logger.warning(f"No NTA person in the cache for {uri}")
            return None
        return SourceData(
            description = next((text for text in _literals(person, "description") if not CITATION.match(text)), None),
            fields = _fields(graph, iri),
            label = next(iter(_literals(person, "name")), None)
        )

def person_iri(uri: str) -> str:
    match = PERSON_URL.match(uri)
    if match is None:
        raise ValueError(f"Not an NTA URI: {uri}")
    return f"{IRI_BASE}{match.group(1).upper()}"

def _add(values: list[str], value: str | None) -> None:
    if value and value.strip() and value.strip() not in values:
        values.append(value.strip())

def _fields(graph: dict[str, dict], iri: str) -> dict[str, list[str]]:
    person = graph[iri]
    fields: dict[str, list[str]] = {}
    for key, prop in (("birth_date", "birthDate"), ("death_date", "deathDate")):
        for value in _literals(person, prop)[:1]:
            if ISO_DATE.fullmatch(value):
                _add(fields.setdefault(key, []), value)
    for value in _literals(person, "alternateName"):
        _add(fields.setdefault("alternate_name", []), value)
    for node in graph.values():
        if {"@id": iri} in node.get(f"{SCHEMA}author", []):
            for label in _literals(node, RDFS_LABEL):
                _add(fields.setdefault("work", []), label.split(TITLE_SEPARATOR)[0])
    return {key: values for key, values in sorted(fields.items()) if values}

def _graph(data: dict | list | None) -> dict[str, dict]:
    """Expanded JSON-LD as {iri: node}."""
    if isinstance(data, dict):
        data = data.get("@graph", [data])
    if not isinstance(data, list):
        return {}
    return {node["@id"]: node for node in data if isinstance(node, dict) and isinstance(node.get("@id"), str)}

def _literals(node: dict, prop: str) -> list[str]:
    """The literal values of prop; a short name is taken to be a schema.org property."""
    key = prop if prop.startswith("http") else f"{SCHEMA}{prop}"
    return [
        str(value["@value"]) for value in node.get(key, [])
        if isinstance(value, dict) and "@value" in value
    ]