# Wikidata

Wat er van de expeditie al op Wikidata staat, en hoe het gemodelleerd is.

## Stations

De stations uit de [stationslijst](stationslijst.md) zijn als items op Wikidata gezet, één item per station.

❓ Aanvullen: een voorbeeld-item, de SPARQL-query om ze allemaal op te halen, en hoe de geschatte posities zijn behandeld.

Uitgangspunten voor de modellering:

- P31: oceanografisch meet- of bemonsteringsstation
- P361 (onderdeel van): de Siboga-expeditie
- P625 (coördinaten): uit de decimale kolommen. Geschatte posities met lage rang of een kwalificator
- P585 / P580 / P582 (tijdstip / begin / einde): uit de datumkolommen
- Diepte, bodemsoort en vangtuig als statements met kwalificatoren
- Bron: verwijzing naar de pagina in de *Liste des Stations*

## Publicatiereeks

De monografiereeks *Siboga-Expeditie* is [Q47059163](https://www.wikidata.org/wiki/Q47059163). Het doel is dat alle 148 afleveringen er als apart item op staan, met P31 *wetenschappelijk artikel* voor de afleveringen.

❓ Aanvullen: hoeveel afleveringen er nu op staan.

## Opvarenden

❓ Aanvullen: welke opvarenden een item hebben. Bij Europese opvarenden: P27 = [Q29999](https://www.wikidata.org/wiki/Q29999) (Koninkrijk der Nederlanden), niet Q55.
