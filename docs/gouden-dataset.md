# Gouden dataset
[Documentatie](README.md) › Gouden dataset

Een vaste dataset met de specimens waarvan met hoge zekerheid vaststaat dat ze door de Siboga-expeditie zijn verzameld, en bij een deel ook bij welk station. Bedoeld voor interactieve onderdelen van de site: kaart, tijdlijn, lijsten en filters.

```
frontend/public/datasets/
└── siboga-goud.json       ← in git, op de site te vinden als /datasets/siboga-goud.json
```

Het bestand staat los van de [frontend data](frontend-data.md): de pipeline maakt het niet en raakt het niet aan. Het wordt als geheel vervangen door een nieuwe versie.

## In het kort
| | |
| --- | --- |
| Versie | 1.0 (31 oktober 2026) |
| Specimens | 6.714, waarvan 183 met station |
| Stations | 50 (16 met gedrukte positie, 34 ankerplaatsen met geschatte positie) |
| Typemateriaal | 1.422: 425 naamdragend (372 holotypes, 53 lectotypes), 575 syntypes, 237 type zonder soort, 183 aanvullend, 2 topotypes |
| Beschermd gebied vandaag | stations: 6 binnen, 4 binnen 5 km; vindplaatsen met eigen coördinaten: 340 binnen, 304 binnen 5 km |
| Musea / uitgevers | 17, uit 29 GBIF-datasets |
| Grootte | 1,8 MB; over het net 236 KB met gzip, 152 KB met brotli |

## Hoe zeker
Een specimen zit erin als het GBIF-record de expeditie of het schip zelf letterlijk noemt in een veld over het verzamelen, en een datum op dagniveau heeft binnen 7 maart 1899 – 26 februari 1900. Literatuurrecords en waarnemingen tellen niet mee.

Een station staat er alleen bij als:
- stationnummer en "Siboga" in hetzelfde veld staan;
- de datum van het record binnen die van het station valt;
- er niets anders tegenspreekt: geen twijfelwoord, geen tweede station, een eventuele positie binnen 10 km, geen verwarring met lettervarianten zoals 225a–h.

Een steekproef van 100 stationkoppelingen en 50 expeditiekoppelingen is met de hand gelezen. Daarna bleef er geen fout over.

De set is bewust klein en zeker, niet volledig. Er zijn ruim 20.000 Siboga-records bij GBIF; de meeste missen een dagdatum of een stationnummer.

## Verrijkingen
- **Typestatus.** Wat het specimen betekent voor de eerste beschrijving van zijn soort, als `type_rang`:
  - 1: holo-, lecto- of neotype, het exemplaar dat de naam vastlegt;
  - 2: syntype;
  - 3: type zonder soort;
  - 4: para-, paralecto- of isotype;
  - 5: topotype.

  De typestatus zelf komt van het museum. Bij 125 types is de naam ouder dan 1899; die hebben een waarschuwing in `type_opmerking`.
- **Beschermd gebied vandaag.** Punt-in-vlak tegen de WDPA van oktober 2026 (Indonesië, Filipijnen, Oost-Timor), alleen gebieden die van kracht zijn. Getoetst worden de gedrukte stationsposities en de coördinaten uit de records zelf, niet de geschatte posities.
- **Namen en rollen.** Verzamelaar, determinator, eerste determinatie en herdeterminatie, gelezen uit de GBIF-velden. Spellingvarianten zijn samengevoegd; de letterlijke schrijfwijzen staan erbij.
- **Groep en museum in gewone taal**, en de soort zonder auteursnaam.

## Formaat
Tabellen staan als `{"velden": [...], "rijen": [[...], ...]}`. Waarden die vaak terugkomen staan één keer in `lijsten` en worden met hun index (vanaf 0) gebruikt. URL's maak je met de voorvoegsels in `url`.

| Onderdeel | Velden |
| --- | --- |
| `stations` | nummer, wikidata, datum, tot, plaats, lat, lon, positie_geschat, diepte_m, bodem, tuig, pagina, beschermd, gebieden |
| `gebieden` | wdpa, naam, aanduiding, iucn, jaar, omgeving, land |
| `musea` | naam, organisatie, stad, land, lat, lon |
| `namen` | naam, persoon, verzameld, gedetermineerd, eerste_determinatie, herdeterminatie, varianten |
| `datasets` | gbif_dataset, titel, uitgever, licentie, doi, bronvermelding |
| `specimens` | gbif, soort, familie, groep, museum, datum, station, type_rang, typestatus, oorspronkelijke_naam, jaar, verzameld, gedetermineerd, hergedetermineerd, lat, lon, beschermd, gebieden, beschermd_via_station, licentie, dataset, wetenschappelijke_naam, catalogus, vindplaats, type_opmerking, bewijs_expeditie, bewijs_station |

Indexen in een specimenrij:
- `soort`, `familie`, `groep`, `licentie`, `typestatus` en `beschermd` verwijzen naar `lijsten.<veld>`.
- `station`, `museum` en `dataset` verwijzen naar een rij in hun tabel.
- `verzameld`, `gedetermineerd`, `hergedetermineerd` en `gebieden` zijn lijsten van rijnummers.
- Het bewijs is `[veld, tekst, match]`: `veld` en `tekst` verwijzen naar `lijsten.bewijs_veld` en `lijsten.bewijs_tekst`, en `match` is het stuk tekst dat de regel raakte (bv. "Sta. 80").

Coördinaten zijn afgerond op 4 decimalen (ongeveer 11 m).

```js
const d = await fetch('/datasets/siboga-goud.json').then((r) => r.json());
const table = (t) => t.rijen.map((r) => Object.fromEntries(t.velden.map((v, i) => [v, r[i]])));
const stations = table(d.stations);
const specimens = table(d.specimens);
const name = d.lijsten.soort[specimens[0].soort];
const url = d.url.gbif + specimens[0].gbif;
```

## Licenties en bronvermelding
- **Records**: licentie per specimen (`licentie`): 6.335 CC0, 238 CC BY 4.0, 141 CC BY-NC 4.0. De citatie per GBIF-dataset staat in `datasets`.
- **Stationslijst**: CC0. Citeer: Fauconnier, S. (2026). *Station list of the Siboga Expedition (1899-1900) cross-referenced with Wikidata* [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.23433434. De lijst komt uit Weber (1902), *Siboga-Expeditie* Monographie I (publiek domein).
- **Wikidata**: CC0.
- **WDPA**, voor `beschermd`, `gebieden` en `beschermd_via_station`:
  - niet-commercieel gebruik;
  - geen herverspreiding van de WDPA-data zelf;
  - waar de site deze gegevens toont, moet deze bronvermelding zichtbaar zijn: *UNEP-WCMC and IUCN (2026), Protected Planet: The World Database on Protected Areas (WDPA) and the World Database on Other Effective Area-based Conservation Measures (WD-OECM) [On-line], October 2026, Cambridge, UK: UNEP-WCMC and IUCN. Available at: www.protectedplanet.net.*

De teksten staan ook in het bestand zelf, onder `bronvermelding`.
