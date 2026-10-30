# Beslissingen
[Documentatie](README.md) › Beslissingen

Wat vastligt en wat nog open staat. Nieuwe beslissingen bovenaan toevoegen.

## Besloten
| Beslissing                                                                                                           | Waar                                                |
| -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Bij elke waarde in de frontend data staat uit welke bron die komt (`sources`, `labelSource`, `source` per veld, enz.) | [frontend-data.md](frontend-data.md) |
| De Wikidata-adapter volgt een vaste lijst identifiers (nu alleen P1006, de NTA) precies één stap; die bron vult alleen aan wat Wikidata leeg laat | [pipeline.md](pipeline.md#gekoppelde-bronnen-via-wikidata) |
| Het contenttype bepaalt welke velden een record toont, niet de bron; vastgelegd in `pipeline/fields.toml`            | [pipeline.md](pipeline.md#velden-per-contenttype)   |
| Nieuw type `page` (map `pages/`): vaste pagina's met `title` en gewone markdown, URL `/pages/<id>`                   | [content-repo.md](content-repo.md#types)            |
| Nieuw type `i18n` (map `etc/`): alle tekst van de site zelf komt uit berichten, ook al is de site alleen Nederlands  | [content-repo.md](content-repo.md#types)            |
| Bronnen zonder Linked Data-endpoint krijgen ook een adapter, op hun eigen API (bijvoorbeeld JSON)                    | [pipeline.md](pipeline.md#bronadapters)             |
| Bij een nieuwe commit in de content-repo bouwt een cronjob de site opnieuw                                           | [ontwikkelen.md](ontwikkelen.md#automatisch-bouwen) |
| De site is voorlopig alleen Nederlands                                                                               | [content-repo.md](content-repo.md#frontmatter)      |
| `location` bij een chapter is verplicht en alleen voor de kaart, niet voor de volgorde                               | [content-repo.md](content-repo.md#frontmatter)      |
| Een record heeft precies één `uri`; geen veld `sources`. Overige bronnen op Wikidata of als externe link in de tekst | [content-repo.md](content-repo.md#frontmatter)      |
| De pipeline zet markdown niet om in HTML; de frontend doet dat met een markdown-parser                               | [frontend-data.md](frontend-data.md#tekst-en-links) |
| Plaatjes altijd lokaal ophalen, en altijd licentie en bronvermelding overnemen                                       | [pipeline.md](pipeline.md#cache)                    |
| Alles wat de site toont staat lokaal, zodat we kunnen presenteren als een externe dienst uitvalt                     | [architectuur.md](architectuur.md#principes)        |
| De pipeline haalt volledige kopieën van de bronnen op en filtert daarna lokaal                                       | [pipeline.md](pipeline.md)                          |
| Pipeline in twee stappen: `fetch` en `build`                                                                         | [pipeline.md](pipeline.md)                          |
| Eén adapter per soort bron, met `fetch`, `matches` en `normalize`                                                    | [pipeline.md](pipeline.md#bronadapters)             |
| De cache bewaart alleen ruwe antwoorden; normaliseren gebeurt bij `build`                                            | [pipeline.md](pipeline.md#cache)                    |
| Twee soorten data: chapters (verhalen) en records (verwijzingen naar Linked Data elders)                             | [content-repo.md](content-repo.md)                  |
| De pipeline kijkt naar `type` in de frontmatter, niet naar de map                                                    | [content-repo.md](content-repo.md)                  |
| Content lokaal in `content/`, pad in te stellen                                                                      | [ontwikkelen.md](ontwikkelen.md)                    |
| Interne links worden URL's, zodat de verwijzingen behouden blijven                                                   | [frontend-data.md](frontend-data.md#urls)           |
| Ids zijn een slug van de bestandsnaam                                                                                | [frontend-data.md](frontend-data.md#urls)           |
| camelCase in `siboga.json`                                                                                           | [frontend-data.md](frontend-data.md)                |
| Voorbeeld-JSON in `frontend/fixtures/`                                                                               | [frontend-data.md](frontend-data.md)                |
| De frontend krijgt één JSON-bestand plus losse bestanden                                                             | [frontend-data.md](frontend-data.md)                |
| Router met volledige paden, geen hashes                                                                              | [frontend.md](frontend.md#routes)                   |
| Leaflet voor de kaart                                                                                                | [frontend.md](frontend.md)                          |
| Store via `provide`/`inject`                                                                                         | [frontend.md](frontend.md)                          |
| Live bronnen, zoals kaarttegels, haalt de frontend zelf op                                                           | [frontend.md](frontend.md)                          |
| Vue 3, JavaScript (geen TypeScript), SCSS; vertrekpunt is Hays template vue3-pinia                                   | [frontend.md](frontend.md)                          |
| Pipeline in Python, met uv                                                                                           | [pipeline.md](pipeline.md)                          |
| Statische website, geen eigen backend                                                                                | [architectuur.md](architectuur.md)                  |
| Twee repo's: de content-repo is alleen bron; alle techniek staat in de code-repo                                     | [architectuur.md](architectuur.md)                  |
| Markdown in de code-repo is GitHub-markdown; in de content-repo Obsidian-markdown                                    | [CLAUDE.md](../CLAUDE.md)                           |
| Eerst lokaal ontwikkelen, daarna de server                                                                           | [ontwikkelen.md](ontwikkelen.md)                    |
| Codeconventies volgens CLAUDE.md                                                                                     | [CLAUDE.md](../CLAUDE.md)                           |

## Open vragen
- Welke velden halen we per `contenttype` uit de bronnen en tonen we? Bepalen we later.
- Welke live bronnen komen er naast de kaarttegels? Nog te bepalen.
