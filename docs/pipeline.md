# Pipeline
[Documentatie](README.md) › Pipeline

De pipeline is een Python-programma in `pipeline/`. Hij maakt van de [content-repo](content-repo.md) en de Linked Data-bronnen de [frontend data](frontend-data.md).

Aanvullende instructies over wat de pipeline wel en niet moet doen, komen nog in [CLAUDE.md](../CLAUDE.md) onder "Pipeline: aanvullende instructies".

## Uitgangspunt: eerst alles kopiëren, dan lokaal filteren
De records in de content-repo verwijzen naar Linked Data op allerlei plekken: Wikidata vooral, maar ook archieven en andere databanken. De pipeline haalt van elk item een **volledige kopie** binnen, met alle triples, en bewaart die in de cache. Pas daarna kiest de pipeline, lokaal, welke gegevens we gebruiken en hoe we ze tonen.

Daar zijn twee redenen voor:
- **Niet afhankelijk van externe diensten.** Valt een bron uit, ook midden in de hackathon, dan staat alles nog in de cache en kunnen we gewoon bouwen en presenteren. Zie [architectuur.md](architectuur.md#principes).
- **Filteren kost geen nieuwe verzoeken.** Willen we een gegeven extra tonen, dan passen we het filter aan en bouwen opnieuw. Er hoeft niets opnieuw opgehaald te worden.

## Twee stappen
| Stap | Leest | Schrijft | Internet nodig |
|---|---|---|---|
| `fetch` | content, cache | cache | ja |
| `build` | content, cache | frontend data | nee |

`fetch` verzamelt alle bron-URI's uit de frontmatter, haalt op wat nog niet (of te lang geleden) in de cache staat, en bewaart de volledige antwoorden plus alle plaatjes en andere bestanden. `build` leest de content en de cache, filtert, en schrijft `siboga.json` en `media/`.

## Commando's
```bash
uv run siboga fetch
uv run siboga fetch --refresh
uv run siboga build
uv run siboga all
```

- `--refresh` haalt alles opnieuw op, ook wat al in de cache staat.
- `all` doet `fetch` en daarna `build`.
- Gewone aanroep vanuit de root van de repo gaat via de `justfile`, zie [ontwikkelen.md](ontwikkelen.md#justfile).

## Modules
```
pipeline/src/siboga/
├── cli.py              ← commando's (fetch, build, all)
├── config.py           ← laadt defaults.toml en daarna config.toml
├── content/            ← de content-repo lezen
│   ├── models.py       ← Pydantic-modellen voor record- en chapter-frontmatter
│   ├── reader.py       ← bestanden vinden, frontmatter parsen
│   └── links.py        ← wikilinks, embeds en markdownlinks vinden en oplossen
├── sources/            ← één adapter per soort bron
│   ├── base.py         ← de basisklasse
│   ├── registry.py     ← kiest de adapter bij een URI
│   └── wikidata.py
├── cache.py            ← SQLite
└── build/              ← frontend data samenstellen
    ├── models.py       ← Pydantic-modellen voor de uitvoer (dit is het contract)
    ├── select.py       ← triples filteren tot facts, datums, afbeelding, coördinaten
    ├── markdown.py     ← markdown naar HTML, interne links naar URL's
    ├── media.py        ← bestanden uit de cache naar media/
    └── writer.py       ← siboga.json schrijven
```

## Bronadapters
Elke soort bron is anders: een andere URL voor de machineleesbare versie, een ander formaat, soms helemaal geen Linked Data. Daarom heeft elke soort bron één adapter. De registry loopt de adapters langs en neemt de eerste waarvan `matches()` ja zegt.

```python
class SourceAdapter:
    name: str

    def fetch(self, uri: str) -> CachedResponse:
        ...

    def matches(self, uri: str) -> bool:
        ...

    def triples(self, response: CachedResponse) -> list[Triple]:
        ...
```

- `fetch` haalt de meest volledige machineleesbare versie op. Waar het kan is dat RDF (Turtle of JSON-LD), via de URL die de bron daarvoor heeft of via content negotiation.
- `triples` maakt van het ruwe antwoord triples. Voor RDF is dat voor elke bron hetzelfde (met `rdflib`); alleen bronnen zonder RDF hebben hier eigen code nodig.
- Een URI waar geen adapter bij past, geeft een waarschuwing. Het record komt wel in de frontend data, alleen zonder verrijking.

De eerste adapter is **Wikidata**. Die haalt `https://www.wikidata.org/wiki/Special:EntityData/Q….ttl` op: het hele item met alle triples. Daarna volgen de andere bronnen uit de content: Stadsarchief Amsterdam, GBIF en Delpher.

### Eén stap verder
Een triple verwijst vaak naar een ander item: Anna Weber heeft als beroep `Q2374149`. Om dat te kunnen tonen is het label van dat item nodig. `fetch` haalt daarom ook de items op waar de gekozen eigenschappen naar verwijzen, maar alleen één stap diep en alleen voor de eigenschappen uit het filter.

## Cache
Eén SQLite-bestand, standaard `pipeline/cache/siboga.sqlite`. Niet in git, maar wel bewaard: op de server en op de laptops waarmee we presenteren.

```sql
CREATE TABLE response (
    uri TEXT PRIMARY KEY,
    adapter TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status INTEGER NOT NULL,
    content_type TEXT,
    body BLOB
);

CREATE TABLE triple (
    source_uri TEXT NOT NULL REFERENCES response (uri),
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    datatype TEXT,
    lang TEXT
);
```

- `response` is de volledige kopie: het ruwe antwoord, precies zoals het binnenkwam.
- `triple` wordt afgeleid uit `response` en kan altijd opnieuw opgebouwd worden. Hij is er om makkelijk op te kunnen filteren en zoeken.
- Mislukte verzoeken worden ook bewaard (met hun status), zodat een kapotte URI niet bij elke run opnieuw geprobeerd wordt.
- Een mislukte nieuwe poging overschrijft nooit een eerder goed antwoord. Valt een bron uit, dan blijft de oude kopie staan.
- Een antwoord ouder dan `cache.max_age_days` wordt bij `fetch` opnieuw opgehaald.
- Plaatjes en andere bestanden staan als losse bestanden in `pipeline/cache/media/`, met hun URI in `response` en `body` leeg. Ze worden altijd gedownload, ook als de frontend ze (nog) niet toont.

## Filteren
Welke gegevens we per soort record tonen, staat in de configuratie, per `contenttype` en per bron. `build/select.py` zoekt die triples op in de cache en maakt er `facts`, `dates`, `image` en `coordinates` van (zie [frontend-data.md](frontend-data.md#velden-van-chapters-en-records)).

```toml
[select.person.wikidata]
image = "P18"
birth = "P569"
death = "P570"
facts = ["P106", "P27", "P108"]

[select.location.wikidata]
image = "P18"
coordinates = "P625"
```

Wat we tonen, en in welke volgorde, is een redactionele keuze. Die maken we per taak, niet nu.

## Beleefd ophalen
- Altijd een eigen `User-Agent` met contactgegevens. Wikimedia weigert verzoeken zonder.
- Een kleine pauze tussen verzoeken naar dezelfde host (`http.delay_seconds`).
- Niet meer ophalen dan nodig: de cache gaat voor.

## Configuratie
`pipeline/defaults.toml` staat in git. `pipeline/config.toml` staat niet in git en overschrijft alleen de waarden die je wilt veranderen. Paden zijn relatief aan de root van de code-repo.

```toml
[content]
path = "content"

[cache]
path = "pipeline/cache/siboga.sqlite"
max_age_days = 7

[output]
path = "frontend/public/data"

[http]
user_agent = "SibogaExpeditie/0.1 (https://siboga.nl)"
delay_seconds = 0.5
```

## Robuustheid en logging
- Logging met Loguru. Elke waarschuwing noemt het bestand in de content-repo, zodat de redactie weet waar het zit.
- Aan het eind van `fetch` en `build` een samenvatting: hoeveel records en chapters, hoeveel bronnen opgehaald, hoeveel waarschuwingen.
- Content-fouten zijn waarschuwingen, geen crashes. Zie [content-repo.md](content-repo.md#wat-de-pipeline-moet-verdragen) voor wat er nu al voorkomt.
- De uitvoer wordt gevalideerd met de Pydantic-modellen uit `build/models.py` voordat hij wordt weggeschreven.

## Tests
- Pytest, in `pipeline/tests/`.
- Een kleine voorbeeldkluis in `pipeline/tests/fixtures/content/` met de lastige gevallen uit [content-repo.md](content-repo.md).
- Adapters testen op opgeslagen ruwe antwoorden, niet op het echte internet.

## Wat de pipeline niet doet
- Niet schrijven in de content-repo.
- Geen server of API: de uitvoer zijn bestanden.
- De SQLite-cache gaat nooit naar de frontend.

## Zie ook
- [content-repo.md](content-repo.md): wat de pipeline leest
- [frontend-data.md](frontend-data.md): wat de pipeline schrijft
- [ontwikkelen.md](ontwikkelen.md): de pipeline draaien, en presenteren zonder internet
- [beslissingen.md](beslissingen.md): wat hiervan nog bevestigd moet worden
