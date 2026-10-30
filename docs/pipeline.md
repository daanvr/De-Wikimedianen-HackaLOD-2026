# Pipeline
De pipeline is een Python-programma in `pipeline/`. Hij maakt van de content-repo en de Linked Data-bronnen de frontend data.

Aanvullende instructies over wat de pipeline wel en niet moet doen, komen nog in [CLAUDE.md](../CLAUDE.md) onder "Pipeline: aanvullende instructies".

## Twee stappen
| Stap | Leest | Schrijft | Internet nodig |
|---|---|---|---|
| `fetch` | content, cache | cache | ja |
| `build` | content, cache | frontend data | nee |

`fetch` verzamelt alle bron-URI's uit de frontmatter, haalt op wat nog niet (of te lang geleden) in de cache staat, en bewaart de ruwe antwoorden. `build` leest de content en de cache en schrijft `siboga.json` en `media/`.

De stappen zijn gescheiden zodat je de frontend data snel en offline opnieuw kunt bouwen als alleen de content of de opmaak van de JSON verandert. Ophalen gebeurt alleen als er nieuwe bronnen zijn, of als je dat vraagt.

## Commando's
```bash
uv run siboga fetch
uv run siboga fetch --refresh
uv run siboga build
uv run siboga all
```

- `--refresh` haalt alles opnieuw op, ook wat al in de cache staat.
- `all` doet `fetch` en daarna `build`.
- Gewone aanroep vanuit de root van de repo gaat via de `justfile`, zie [ontwikkelen.md](ontwikkelen.md).

## Modules
```
pipeline/src/siboga/
├── cli.py              ← commando's (fetch, build, all)
├── config.py           ← laadt defaults.toml en daarna config.toml
├── content/            ← de content-repo lezen
│   ├── models.py       ← Pydantic-modellen voor record- en chapter-frontmatter
│   ├── reader.py       ← bestanden vinden, frontmatter parsen
│   └── wikilinks.py    ← [[...]] vinden en oplossen
├── sources/            ← één adapter per soort bron
│   ├── base.py         ← de basisklasse
│   ├── registry.py     ← kiest de adapter bij een URI
│   └── wikidata.py
├── cache.py            ← SQLite
└── build/              ← frontend data samenstellen
    ├── models.py       ← Pydantic-modellen voor de uitvoer (dit is het contract)
    ├── markdown.py     ← markdown naar HTML, wikilinks naar recordlinks
    ├── media.py        ← plaatjes uit de cache naar media/
    └── writer.py       ← siboga.json schrijven
```

## Bronadapters
Elke soort bron heeft één adapter. De registry loopt de adapters langs en neemt de eerste waarvan `matches()` ja zegt.

```python
class SourceAdapter:
    name: str

    def fetch(self, uri: str) -> CachedResponse:
        ...

    def matches(self, uri: str) -> bool:
        ...

    def normalize(self, response: CachedResponse) -> SourceData:
        ...
```

- `fetch` haalt de bron op en geeft het ruwe antwoord terug. Wordt alleen in de stap `fetch` gebruikt.
- `normalize` maakt van het ruwe antwoord velden die de frontend kan gebruiken: label, beschrijving, afbeelding, coördinaten, datums, links. Wordt alleen in de stap `build` gebruikt.
- Een URI waar geen adapter bij past, geeft een waarschuwing. Het record komt wel in de frontend data, alleen zonder verrijking.

De eerste adapter is **Wikidata**: `https://www.wikidata.org/wiki/Special:EntityData/Q….json`. Daaruit komen in ieder geval labels en beschrijvingen (nl, en), afbeelding (P18, via Wikimedia Commons), coördinaten (P625), en geboorte- en sterfdatum (P569, P570). Daarna volgen de andere bronnen uit de content: Stadsarchief Amsterdam, GBIF en Delpher.

Normaliseren gebeurt pas bij `build`, op het ruwe antwoord uit de cache. Zo kun je de normalisatie aanpassen zonder alles opnieuw op te halen.

## Cache
Eén SQLite-bestand, standaard `pipeline/cache/siboga.sqlite`. Niet in git.

```sql
CREATE TABLE response (
    uri TEXT PRIMARY KEY,
    adapter TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status INTEGER NOT NULL,
    content_type TEXT,
    body BLOB
);
```

- Er gaat alleen het **ruwe** antwoord in, niets genormaliseerds.
- Mislukte verzoeken worden ook bewaard (met hun status), zodat een kapotte URI niet bij elke run opnieuw geprobeerd wordt.
- Een antwoord ouder dan `cache.max_age_days` wordt bij `fetch` opnieuw opgehaald.
- Gedownloade plaatjes en andere bestanden staan als losse bestanden in `pipeline/cache/media/`, met hun URI in dezelfde tabel en `body` leeg.

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
- Content-fouten zijn waarschuwingen, geen crashes. Zie [content-repo.md](content-repo.md) voor wat er nu al voorkomt.
- De uitvoer wordt gevalideerd met de Pydantic-modellen uit `build/models.py` voordat hij wordt weggeschreven.

## Tests
- Pytest, in `pipeline/tests/`.
- Een kleine voorbeeldkluis in `pipeline/tests/fixtures/content/` met de lastige gevallen uit [content-repo.md](content-repo.md).
- Adapters testen op opgeslagen ruwe antwoorden, niet op het echte internet.

## Wat de pipeline niet doet
- Niet schrijven in de content-repo.
- Geen server of API: de uitvoer zijn bestanden.
- De SQLite-cache gaat nooit naar de frontend.
