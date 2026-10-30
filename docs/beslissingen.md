# Beslissingen
[Documentatie](README.md) › Beslissingen

Wat vastligt en wat nog open staat. Nieuwe beslissingen bovenaan toevoegen.

## Besloten
| Beslissing                                                                                       | Waar                                                |
| ------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| Een record heeft precies één `uri`. Overige bronnen komen in een apart veld `sources`            | [content-repo.md](content-repo.md#frontmatter)      |
| De pipeline zet markdown niet om in HTML; de frontend doet dat met een markdown-parser           | [frontend-data.md](frontend-data.md#tekst-en-links) |
| Plaatjes altijd lokaal ophalen, en altijd licentie en bronvermelding overnemen                   | [pipeline.md](pipeline.md#cache)                    |
| Alles wat de site toont staat lokaal, zodat we kunnen presenteren als een externe dienst uitvalt | [architectuur.md](architectuur.md#principes)        |
| De pipeline haalt volledige kopieën van de bronnen op en filtert daarna lokaal                   | [pipeline.md](pipeline.md)                          |
| Pipeline in twee stappen: `fetch` en `build`                                                     | [pipeline.md](pipeline.md)                          |
| Eén adapter per soort bron, met `fetch`, `matches` en `normalize`                                | [pipeline.md](pipeline.md#bronadapters)             |
| De cache bewaart alleen ruwe antwoorden; normaliseren gebeurt bij `build`                        | [pipeline.md](pipeline.md#cache)                    |
| Twee soorten data: chapters (verhalen) en records (verwijzingen naar Linked Data elders)         | [content-repo.md](content-repo.md)                  |
| De pipeline kijkt naar `type` in de frontmatter, niet naar de map                                | [content-repo.md](content-repo.md)                  |
| Content lokaal in `content/`, pad in te stellen                                                  | [ontwikkelen.md](ontwikkelen.md)                    |
| Interne links worden URL's, zodat de verwijzingen behouden blijven                               | [frontend-data.md](frontend-data.md#urls)           |
| Ids zijn een slug van de bestandsnaam                                                            | [frontend-data.md](frontend-data.md#urls)           |
| camelCase in `siboga.json`                                                                       | [frontend-data.md](frontend-data.md)                |
| Voorbeeld-JSON in `frontend/fixtures/`                                                           | [frontend-data.md](frontend-data.md)                |
| De frontend krijgt één JSON-bestand plus losse bestanden                                         | [frontend-data.md](frontend-data.md)                |
| Router met volledige paden, geen hashes                                                          | [frontend.md](frontend.md#routes)                   |
| Leaflet voor de kaart                                                                            | [frontend.md](frontend.md)                          |
| Store via `provide`/`inject`                                                                     | [frontend.md](frontend.md)                          |
| Live bronnen, zoals kaarttegels, haalt de frontend zelf op                                       | [frontend.md](frontend.md)                          |
| Vue 3, JavaScript (geen TypeScript), SCSS; vertrekpunt is Hays template vue3-pinia               | [frontend.md](frontend.md)                          |
| Pipeline in Python, met uv                                                                       | [pipeline.md](pipeline.md)                          |
| Statische website, geen eigen backend                                                            | [architectuur.md](architectuur.md)                  |
| Twee repo's: de content-repo is alleen bron; alle techniek staat in de code-repo                 | [architectuur.md](architectuur.md)                  |
| Markdown in de code-repo is GitHub-markdown; in de content-repo Obsidian-markdown                | [CLAUDE.md](../CLAUDE.md)                           |
| Eerst lokaal ontwikkelen, daarna de server                                                       | [ontwikkelen.md](ontwikkelen.md)                    |
| Codeconventies volgens CLAUDE.md                                                                 | [CLAUDE.md](../CLAUDE.md)                           |

## Open vragen
- Welke velden halen we per `contenttype` uit de bronnen en tonen we?
	- Bepalen we later.
- Hoe gaan we om met bronnen zonder Linked Data-endpoint, zoals Delpher en het Stadsarchief Amsterdam?
	- Kijk of er een …
- Hoe ziet het veld `sources` er precies uit, en doet de pipeline er iets mee?
	- Het veld sources is niet nodig. Bronnen kunnen op Wikidata komen en eventueel in de lopende tekst als reguliere externe links.
- Waarvoor gebruiken we `location` bij een chapter: alleen voor de kaart, of ook voor de volgorde?
	- Location is puur voor locatie op de kaart, niet voor de volgorde
- Is de site alleen Nederlands? `description_nl` doet vermoeden dat er later meer talen komen.
	- Voor nu alleen Nederlands. 
- Welke live bronnen komen er naast de kaarttegels?
	- NTB
- Wanneer bouwen we opnieuw, en waar draait de pipeline dan: met de hand, of automatisch bij een wijziging in de content-repo?
	- Bij elke push naar Git wordt de content repo gedownload en draait build/fetch. Dit kan via een cronjob.
