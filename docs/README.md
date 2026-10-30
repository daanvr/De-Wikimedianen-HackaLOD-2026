# Documentatie De Siboga Expeditie
Technische documentatie van de website De Siboga Expeditie, en het startpunt voor alle andere documenten. Het is een hackathon: dit beschrijft het kleinste dat werkt, geen definitieve infrastructuur. Voor concrete taken maken we per taak een plan.

## In het kort
- De site is statisch: een [Vue-frontend](frontend.md) die één JSON-bestand en een map met plaatjes leest, de [frontend data](frontend-data.md).
- De inhoud komt uit de [content-repo](content-repo.md), geschreven in Obsidian: **chapters** (verhalen) en **records** (verwijzingen naar Linked Data elders).
- Een [Python-pipeline](pipeline.md) haalt de bronnen op, bewaart ze in SQLite en schrijft de frontend data.
- Alles staat lokaal. Valt een externe dienst uit, dan kunnen we nog presenteren.
- Elke chapter en elk record heeft een eigen URL. De interne links uit de content wijzen daarheen.

## Documenten
| Document                             | Inhoud                                              |
| ------------------------------------ | --------------------------------------------------- |
| [architectuur.md](architectuur.md)   | Het geheel: datastroom, onderdelen, principes       |
| [content-repo.md](content-repo.md)   | Chapters en records, frontmatter, Obsidian-markdown |
| [pipeline.md](pipeline.md)           | Bronnen ophalen, cachen, frontend data bouwen       |
| [frontend-data.md](frontend-data.md) | Het contract tussen pipeline en frontend            |
| [frontend.md](frontend.md)           | De Vue-frontend                                     |
| [ontwikkelen.md](ontwikkelen.md)     | Lokaal draaien, presenteren, uitrollen              |
| [beslissingen.md](beslissingen.md)   | Wat besloten is en wat nog open staat               |

Codeconventies staan in [CLAUDE.md](../CLAUDE.md). Het inhoudelijke overzicht van de expeditie staat in [expeditie/](../expeditie/README.md).

## Begrippen
| Begrip        | Betekenis                                                                                                   |
| ------------- | ----------------------------------------------------------------------------------------------------------- |
| Content-repo  | [hay/siboga-content](https://github.com/hay/siboga-content): de markdown uit Obsidian, de *source of truth* |
| Code-repo     | Deze repo: alle techniek                                                                                    |
| Chapter       | Een verhaal: tekst met links naar records, andere chapters en externe pagina's                              |
| Record        | Een persoon, voorwerp, plek, foto enzovoort, met één verwijzing naar Linked Data elders                     |
| Bron          | De Linked Data waar een record naar verwijst, bijvoorbeeld Wikidata                                         |
| Cache         | SQLite-database met de opgehaalde bronnen; alleen voor de pipeline                                          |
| Frontend data | `siboga.json` plus `media/`: het enige wat de frontend van de pipeline ziet                                 |
| Ref           | Verwijzing naar een item, zoals `records/anna-weber`. Met een `/` ervoor is het de URL                      |
| Live bron     | Data die de browser zelf ophaalt, zoals kaarttegels                                                         |
