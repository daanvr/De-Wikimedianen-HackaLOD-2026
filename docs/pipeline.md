# Pipeline
[Documentatie](README.md) › Pipeline

Een Python-programma in `pipeline/` dat van de [content-repo](content-repo.md) en de Linked Data de [frontend data](frontend-data.md) maakt. Aanvullende instructies komen nog in [CLAUDE.md](../CLAUDE.md).

De pipeline haalt van elke bron een **volledige kopie** op en kiest pas daarna lokaal wat we tonen. Zo kunnen we bouwen en presenteren als een bron uitvalt, en kost een ander filter geen nieuwe verzoeken.

## Twee stappen
| Stap    | Doet                                                      | Internet |
| ------- | --------------------------------------------------------- | -------- |
| `fetch` | Bronnen van alle records ophalen en in de cache zetten    | ja       |
| `build` | Content en cache combineren tot `siboga.json` en `media/` | nee      |

```bash
uv run siboga fetch            # --refresh haalt alles opnieuw op
uv run siboga build
```

## Modules
```
pipeline/src/siboga/
├── cli.py
├── config.py      ← defaults.toml, overschreven door config.toml
├── content.py     ← markdown en frontmatter lezen
├── sources/       ← één adapter per soort bron
├── cache.py       ← SQLite
└── build.py       ← frontend data schrijven
```

## Bronadapters
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

- `fetch` haalt de volledige bron op (bij `fetch`).
- `matches` zegt of de adapter bij een URI hoort.
- `normalize` haalt uit het ruwe antwoord wat we tonen: label, beschrijving, afbeelding, coördinaten, datums (bij `build`).

De eerste adapter is Wikidata (`Special:EntityData/Q….json`). Een URI zonder adapter geeft een waarschuwing; het record komt er dan zonder verrijking in.

## Cache
Eén SQLite-bestand in `pipeline/cache/` (niet in git), met de ruwe antwoorden:

```sql
CREATE TABLE response (
    uri TEXT PRIMARY KEY,
    adapter TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status INTEGER NOT NULL,
    body BLOB
);
```

- Een mislukte poging overschrijft nooit een eerder goed antwoord.
- Plaatjes worden altijd gedownload naar `pipeline/cache/media/`, met licentie en bronvermelding.

## Configuratie
`defaults.toml` staat in git, `config.toml` (niet in git) overschrijft wat je wilt. Paden zijn relatief aan de root van de repo.

```toml
[content]
path = "content"

[output]
path = "frontend/public/data"

[http]
user_agent = "SibogaExpeditie/0.1 (https://siboga.nl)"
```

## Verder
- Logging met Loguru; aan het eind een samenvatting met het aantal waarschuwingen.
- Tests met Pytest, op een kleine voorbeeldkluis en opgeslagen antwoorden.
- Altijd een eigen `User-Agent` meesturen; Wikimedia weigert verzoeken zonder.
