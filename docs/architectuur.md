# Architectuur
De Siboga Expeditie is een statische website. Er draait geen eigen backend: alles wat de site nodig heeft, wordt vooraf gegenereerd en als gewone bestanden geserveerd. Alleen live bronnen, zoals de kaarttegels voor de interactieve kaart, haalt de browser zelf op.

## Datastroom
```mermaid
flowchart LR
    content["Content-repo<br>Obsidian-markdown + YAML"]
    ld["Linked Data-bronnen<br>Wikidata, archieven, ..."]
    subgraph pipeline["Pipeline (Python)"]
        fetch["fetch"]
        cache[("SQLite-cache")]
        build["build"]
    end
    data["Frontend data<br>siboga.json + media/"]
    frontend["Frontend (Vue)"]
    live["Live bronnen<br>kaarttegels, ..."]
    server["Webserver<br>siboga.nl"]
    content --> fetch
    ld --> fetch
    fetch --> cache
    content --> build
    cache --> build
    build --> data
    data --> frontend
    live --> frontend
    frontend -- "vite build" --> server
```

In woorden:
1. Redacteuren schrijven in Obsidian. Hun markdown komt in de content-repo.
2. `fetch` leest de content, verzamelt alle bron-URI's uit de frontmatter, haalt die op en bewaart de ruwe antwoorden in SQLite.
3. `build` leest de content opnieuw, combineert die met de cache en schrijft de frontend data: één `siboga.json` en een map `media/`.
4. De frontend laadt `siboga.json` bij het opstarten en toont alles daaruit. Live bronnen haalt hij zelf op.
5. `vite build` maakt er een statische map van, die naar de server gaat.

## Onderdelen
| Onderdeel | Map | Taal | Verantwoordelijk voor | Documentatie |
|---|---|---|---|---|
| Content | content-repo, lokaal gekloond in `content/` | Markdown + YAML | Het verhaal en de verwijzingen naar bronnen | [content-repo.md](content-repo.md) |
| Pipeline | `pipeline/` | Python (uv) | Bronnen ophalen, cachen, frontend data bouwen | [pipeline.md](pipeline.md) |
| Frontend data | `frontend/public/data/` | JSON + bestanden | Het contract tussen pipeline en frontend | [frontend-data.md](frontend-data.md) |
| Frontend | `frontend/` | Vue 3, JavaScript, SCSS | De website | [frontend.md](frontend.md) |
| Server | `etc/` | nginx | Het serveren van de statische bestanden | [ontwikkelen.md](ontwikkelen.md) |

## Naden tussen de onderdelen
Elk onderdeel praat met het volgende via één afgesproken formaat. Daardoor kan elk onderdeel apart gebouwd, getest en vervangen worden.
1. **Content → pipeline**: markdownbestanden met YAML-frontmatter en wikilinks. Zie [content-repo.md](content-repo.md).
2. **Bron → cache**: per soort bron één adapter in de pipeline. Een nieuwe bron toevoegen is één nieuw bestand. Zie [pipeline.md](pipeline.md).
3. **Pipeline → frontend**: de frontend data. Dit is de belangrijkste naad. De frontend weet niets van Obsidian, SQLite of Linked Data; hij kent alleen `siboga.json`. Zie [frontend-data.md](frontend-data.md).
4. **Frontend → live bronnen**: per live bron één module in de frontend. Componenten halen nooit zelf data op. Zie [frontend.md](frontend.md).

## Principes
- **De content-repo is alleen bron.** De pipeline leest hem en schrijft er nooit in.
- **Statisch.** Geen server-side code. De site werkt met elke webserver die bestanden kan serveren.
- **Modulair.** Eén adapter per bron, één view per scherm, één module per live bron. De frontend is te ontwikkelen met een voorbeeld-JSON, zonder dat de pipeline draait.
- **Cache als buffer.** De cache maakt de pipeline snel en herhaalbaar, en ontziet de endpoints. `build` werkt zonder internet.
- **Verdraagzaam voor content.** Content wordt door mensen geschreven en is vaak onaf. Ontbrekende velden of kapotte links geven een waarschuwing, geen crash.
- **Eenvoud boven volledigheid.** Het is een hackathon. Bouw het kleinste dat werkt, maar houd de naden hierboven heel.

## Voorgestelde indeling van de repo
```
├── CLAUDE.md                ← codeconventies en instructies voor agents
├── README.md
├── justfile                 ← alle commando's op één plek
├── docs/                    ← deze documentatie
├── content/                 ← lokale kloon van de content-repo (niet in git)
├── pipeline/                ← Python, beheerd met uv
│   ├── pyproject.toml
│   ├── defaults.toml        ← standaardconfiguratie (in git)
│   ├── config.toml          ← lokale overschrijvingen (niet in git)
│   ├── cache/               ← SQLite en gedownloade media (niet in git)
│   ├── src/siboga/
│   └── tests/
├── frontend/                ← Vue 3 + Vite, op basis van Hays template vue3-pinia
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── fixtures/            ← voorbeeld-frontend data (in git)
│   ├── public/data/         ← frontend data uit de pipeline (niet in git)
│   └── src/
├── etc/                     ← serverconfiguratie (nginx)
└── expeditie/               ← inhoudelijk overzicht van de expeditie (bestaat al)
```

De map `site/` met de huidige placeholder-pagina blijft staan tot de Vue-frontend live gaat.
