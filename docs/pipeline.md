# Pipeline
[Documentatie](README.md) › Pipeline

Een Python-programma in `pipeline/` dat van de [content-repo](content-repo.md) en de Linked Data de [frontend data](frontend-data.md) maakt. Aanvullende instructies komen nog in [CLAUDE.md](../CLAUDE.md).

De pipeline haalt van elke bron een **volledige kopie** op en kiest pas daarna lokaal wat we tonen. Zo kunnen we bouwen en presenteren als een bron uitvalt, en kost een ander filter geen nieuwe verzoeken.

## Stappen
| Stap    | Doet                                                      | Internet |
| ------- | --------------------------------------------------------- | -------- |
| `fetch` | Bronnen van alle records ophalen en in de cache zetten, plus de GBIF-records van de [ontdekmodus](#ontdekmodus) | ja |
| `build` | Content en cache combineren tot `siboga.json`, `explorer.json` en `media/` | nee |
| `check` | De uitvoer controleren tegen het contract                 | nee      |

```bash
cd pipeline
uv run siboga fetch            # --refresh haalt alles opnieuw op
uv run siboga build
uv run siboga all              # fetch en build
uv run siboga check            # klopt elke ref, bestaat elk bestand, heeft elk plaatje een licentie?
```

Met `-v` zie je ook de debugmeldingen. Waarschuwingen over de content (kapotte links, een `uri` die geen URL is) staan in de log met de bestandsnaam erbij; ze houden de build niet tegen. `build` schrijft eerst naar een tijdelijke map en vervangt de oude uitvoer pas als alles gelukt is.

## Modules
```
pipeline/src/siboga/
├── cli.py         ← de commando's
├── config.py      ← defaults.toml, overschreven door config.toml
├── models.py      ← gedeelde datatypes
├── fields.py      ← fields.toml lezen: velden per contenttype
├── content.py     ← chapters, records, pages en i18n lezen, wikilinks omzetten
├── fetcher.py     ← HTTP: User-Agent, pauze per host, retries volgens de rate limit van de adapter
├── cache.py       ← SQLite en gedownloade bestanden
├── sources/       ← één adapter per soort bron
├── explorer.py    ← GBIF-records en foto's van de specimens in de ontdekmodus
└── build.py       ← frontend data schrijven en controleren
```

## Bronadapters
```python
class SourceAdapter:
    name: str
    rate_limit: RateLimit = RateLimit()

    def fetch(self, uri: str, fetcher: Fetcher) -> None:
        ...

    def matches(self, uri: str) -> bool:
        ...

    def normalize(self, uri: str, cache: Cache) -> SourceData | None:
        ...
```

- `fetch` haalt via de fetcher alles op wat nodig is, inclusief plaatjes. Alleen in de stap `fetch`.
- `matches` zegt of de adapter bij een URI hoort.
- `rate_limit` zegt hoe beleefd de fetcher de bron benadert: de pauze tussen verzoeken aan dezelfde host, het aantal herpogingen bij een netwerkfout, 429 of 5xx, en hoe lang hij dan wacht. Stuurt de server een `Retry-After` mee (in seconden of als datum), dan wacht de fetcher zo lang, tot hoogstens een minuut. Anders wacht hij bij een 429 een vaste tijd en bij de rest steeds twee keer zo lang. `wikidata` en `commons` gebruiken `WIKIMEDIA_RATE_LIMIT`: één verzoek per seconde en vijf herpogingen. `nta` wacht ook een seconde tussen verzoeken. De andere adapters houden de standaard: 0,2 seconde en drie herpogingen.
- `normalize` leest uitsluitend uit de cache en geeft label, beschrijving, afbeelding (met bronvermelding en licentie), coördinaten en **alle velden die de bron kan vullen** terug. Alleen in de stap `build`.

| Adapter             | URI's                                               | Wat hij ophaalt                                                                  |
| ------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------- |
| `wikidata`          | `wikidata.org/wiki/Q…`                              | Het hele item (`Special:EntityData/Q….json`), en het plaatje uit P18 via Commons |
| `commons`           | `commons.wikimedia.org/wiki/File:…` en `/entity/M…` | De imageinfo met metadata en licentie, en het plaatje op 1600 px                 |
| `gbif`              | `gbif.org/taxon/…`, `/species/…` en `/occurrence/…` | Het taxon via ChecklistBank of de GBIF-API; een plaatje alleen met licentie. Bij een occurrence (een specimen) ook het museum, de soort en de gegevens van het exemplaar zelf |
| `archief_amsterdam` | `archief.amsterdam/detail/…`                        | Het record als JSON-LD via `id.archief.amsterdam`; een scan alleen met licentie  |
| `nta`               | `data.bibliotheken.nl/id/thes/p…`                   | De persoon als JSON-LD, met de titels van de werken in hetzelfde antwoord        |

Een `gbif.org/occurrence/…` is één museumexemplaar. De adapter haalt de occurrence op, het museum via GRSciColl (`institutionKey`) en de soort met Nederlandse namen via `taxonKey`. Het label is de naam op het exemplaar, ook als dat een oud synoniem is. Naast de taxonvelden vult hij `type_status`, `collection`, `catalog_number`, `collector`, `collection_date`, `locality`, `depth` en de coördinaten. Het plaatje komt alleen van het exemplaar zelf: een foto van een ander exemplaar van dezelfde soort zou hier misleiden.

Een adapter hoeft geen Linked Data te lezen: elke bron met een API kan er een krijgen. Een URI zonder adapter geeft een waarschuwing; het record komt er dan zonder verrijking in.

### Gekoppelde bronnen via Wikidata
Een record heeft één `uri`, maar een Wikidata-item kan naar andere bronnen verwijzen. De Wikidata-adapter volgt een vaste lijst van zulke identifiers, `LINKED_SOURCES` in [wikidata.py](../pipeline/src/siboga/sources/wikidata.py):

| Property | Bron | Adapter |
| -------- | ---- | ------- |
| `P1006`  | NTA (Nederlandse Thesaurus van Auteursnamen, KB) | `nta` |

- Precies één stap ver: alleen de Wikidata-adapter volgt links, de gekoppelde adapter haalt alleen zijn eigen record op en volgt zelf niets. Zo kan het nooit uitdijen.
- Alleen de beste statements tellen, net als bij de velden: staat er een *preferred* ID, dan alleen dat.
- `normalize` vult met de gekoppelde bron alleen aan wat Wikidata leeg laat (`SourceData.fill_from`). Wikidata wint altijd, dus de NTA levert vooral `alternate_name` en `work`. `fill_from` houdt bij welke bron wat invulde, zodat in de frontend data bij elke waarde de bron staat; zie [frontend-data.md](frontend-data.md#sibogajson).
- Een kapotte of ontbrekende gekoppelde bron geeft een waarschuwing in de log; het Wikidata-item komt er gewoon in.
- Een bron erbij is een regel in `LINKED_SOURCES` plus een adapter die je in `build_registry` aan de Wikidata-adapter meegeeft.

## Velden per contenttype
De adapter bepaalt wat er uit een bron te halen is; het contenttype van het record bepaalt wat er getoond wordt. Een Wikidata-item over een persoon en een Wikidata-item over een soort gaan door dezelfde adapter, maar tonen andere velden.

- Elke adapter vult alle velden die hij kan, met vaste namen zoals `birth_date`, `occupation` of `scientific_name`.
- [pipeline/fields.toml](../pipeline/fields.toml) zegt per contenttype welke velden getoond worden en in welke volgorde, en per veld of het een `date` of `text` is.
- `build` kiest per record de velden van zijn contenttype en zet ze als `fields` in `siboga.json`. Een datum die geen `YYYY`, `YYYY-MM` of `YYYY-MM-DD` is, geeft een waarschuwing.

Een veld erbij voor een contenttype is dus een regel in `fields.toml`. Een nieuw soort veld vraagt ook een regel in de adapter die het moet vullen. Bij Wikidata haalt `fetch` ook de labels op van items waar een veld naar verwijst (zoals het beroep of de geboorteplaats), zodat de site namen toont en geen Q-nummers.

## Cache
Eén SQLite-bestand in `pipeline/cache/` (niet in git), met de ruwe antwoorden per opgevraagde URL:

```sql
CREATE TABLE response (
    url TEXT PRIMARY KEY,
    adapter TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status INTEGER NOT NULL,
    content_type TEXT,
    body BLOB
);
```

- Een mislukte poging overschrijft nooit een eerder goed antwoord of een eerder gedownload bestand.
- Plaatjes staan in `pipeline/cache/media/`, met `body` leeg in de tabel. In de uitvoer komt een plaatje alleen met licentie en bronvermelding.
- `build` maakt van elk plaatje van een record ook een thumbnail in `media/thumbs/` ([thumbnails.py](../pipeline/src/siboga/thumbnails.py)). Dat gebeurt elke build opnieuw en zonder internet; voor zo'n 60 plaatjes duurt het minder dan een seconde.
- Antwoorden ouder dan `max_age_days` (standaard 30) worden bij `fetch` opnieuw opgehaald.

## Ontdekmodus
De [ontdekmodus](ontdekmodus.md) toont de specimens uit de [gouden dataset](gouden-dataset.md) die aan een station gekoppeld zijn. `explorer.py` behandelt die als records zonder markdown-bestand: `fetch` haalt per specimen het GBIF-record en de foto op (via dezelfde cache en dezelfde regels voor licentie en naam als de GBIF-adapter), en `build` kopieert de foto's naar `media/specimen-<gbif>.jpg` en schrijft `explorer.json` met per specimen de foto, alle determinaties en de verzamelaars uit `recordedBy`. Hetzelfde doet `explorer.py` voor de stations uit `route-stations.json`: `fetch` vraagt hun Wikidata-items op (vijftig per verzoek, `wbgetentities`) en haalt van wie een afbeelding heeft (P18) de foto op Commons op; `build` kopieert die naar `media/station-<nummer>.jpg` en maakt er een kleine versie van in `media/thumbs/` voor de kaart. Waar de bestanden staan, zeggen `[explorer] gold_path` en `stations_path` in `defaults.toml`.

## Configuratie
`pipeline/defaults.toml` staat in git; `pipeline/config.toml` (niet in git) overschrijft wat je wilt. Paden zijn relatief aan de root van de repo.

```toml
[content]
path = "content"

[output]
path = "frontend/public/data"
```

## Tests
`uv run pytest` in `pipeline/`. De tests draaien zonder internet, op een kleine voorbeeldkluis en echte, ingekorte antwoorden van de bronnen in `tests/fixtures/`.
