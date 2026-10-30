# Data

Datasets die team De Wikimedianen vóór de HackaLOD heeft samengesteld. Per dataset staat er een spreadsheet (het werkbestand, met toelichting in een apart tabblad) en een CSV-export (makkelijker in code en beter leesbaar in git-diffs).

| Bestand | Inhoud | Rijen |
|---|---|---|
| `Siboga_stations_v2_5.xlsx` / `siboga_stations_v2_5.csv` | Stationslijst van de expeditie: datum, positie, diepte, bodem, vangtuig | 363 (323 genummerde stations + lettervarianten) |
| `Siboga_opvarenden_index.xlsx` / `siboga_opvarenden_index_nl.csv` / `_en.csv` | Index van opvarenden: wie wordt waar genoemd in drie publicaties | 28 personen en groepen |

Uitleg per dataset, inclusief herkomst, betrouwbaarheid en open punten: zie [`../voorwerk/`](../voorwerk/).

## Gebruik in code

- De CSV's zijn UTF-8, met komma als scheidingsteken en een kopregel. De kolomnamen zijn gelijk aan die in de spreadsheet.
- **Data staan als tekst `JJJJ-MM-DD`**, geen datumwaarden. Excel kan geen data vóór 1900 aan.
- **Coördinaten**: zuiderbreedte negatief, oosterlengte positief. Er zijn drie soorten posities, die je op de kaart van elkaar moet kunnen onderscheiden:
  - `Latitude/Longitude (decimal)`: positie zoals opgegeven in de bron (255 rijen)
  - `Derived latitude/longitude (bearing)`: berekend uit afstand en peiling vanaf een landmerk (9 rijen, de 225-reeks)
  - `Latitude/Longitude (extrapolated)`: geschat door lineaire interpolatie tussen buurstations (97 rijen). **Dit zijn schattingen, geen waarnemingen.**
- Kolom `Depth type` scheidt echte bodemlodingen van apparaatdieptes (12 rijen). Laat die laatste weg uit dieptestatistieken.

## Licentie

❓ Nog vast te leggen. Voorstel: CC0, gelijk aan Wikidata. De stationsdataset gaat ook naar Zenodo; gebruik daar dezelfde licentie.
