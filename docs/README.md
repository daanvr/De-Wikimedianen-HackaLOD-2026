# Documentatie De Siboga Expeditie
Technische documentatie van de website De Siboga Expeditie, en het startpunt voor alle andere documenten. Het is een hackathon: dit beschrijft het kleinste dat werkt, geen definitieve infrastructuur. Voor concrete taken maken we per taak een plan.

## In het kort
- De site is statisch: een [Vue-frontend](frontend.md) die één JSON-bestand en een map met plaatjes leest, de [frontend data](frontend-data.md).
- De inhoud komt uit de [content-repo](content-repo.md), geschreven in Obsidian: **chapters** (verhalen), **records** (verwijzingen naar Linked Data elders), **pages** (vaste pagina's), **plugins** (interactieve onderdelen) en **i18n** (de teksten van de site zelf).
- Welke gegevens een record toont, hangt af van zijn contenttype ([velden per contenttype](pipeline.md#velden-per-contenttype)).
- Een [Python-pipeline](pipeline.md) haalt de bronnen op, bewaart ze in SQLite en schrijft de frontend data.
- Alles staat lokaal. Valt een externe dienst uit, dan kunnen we nog presenteren.
- Elke chapter en elk record heeft een eigen URL. De interne links uit de content wijzen daarheen.

## Deployment
Uiteindelijke website draait op Ubuntu 26.04 met nginx en Python via uv. Verder is alles statisch.

## Documenten
| Document                             | Inhoud                                              |
| ------------------------------------ | --------------------------------------------------- |
| [architectuur.md](architectuur.md)   | Het geheel: datastroom, onderdelen, principes       |
| [content-repo.md](content-repo.md)   | Chapters en records, frontmatter, Obsidian-markdown |
| [pipeline.md](pipeline.md)           | Bronnen ophalen, cachen, frontend data bouwen       |
| [frontend-data.md](frontend-data.md) | Het contract tussen pipeline en frontend            |
| [gouden-dataset.md](gouden-dataset.md) | De vaste dataset met zekere specimens en stations |
| [ontdekmodus.md](ontdekmodus.md)     | De datavisualisatie (ontdekmodus): kaart, tijdlijn, duik en zijn data |
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
| Contenttype   | Soort record (`person`, `specimen`, `media` ...). Bepaalt welke velden het record toont                     |
| Veld          | Eén gegeven van een record, zoals `birth_date` of `scientific_name`                                         |
| Page          | Een vaste pagina, zoals welkom of over ons                                                                  |
| Plugin        | Een interactief onderdeel, zoals een IIIF-viewer: schermvullend in de ontdekmodus of in de tekst            |
| Bericht       | Een tekst van de site zelf (knop, menu, veldnaam), uit `type: i18n`                                         |
| Bron          | Waar een record naar verwijst: Linked Data zoals Wikidata, of een andere API                                |
| Cache         | SQLite-database met de opgehaalde bronnen; alleen voor de pipeline                                          |
| Frontend data | `siboga.json` plus `media/`: het enige wat de frontend van de pipeline ziet                                 |
| Ref           | Verwijzing naar een item, zoals `records/anna-weber` of `pages/about`. Met een `/` ervoor is het de URL     |
| Live bron     | Data die de browser zelf ophaalt, zoals kaarttegels                                                         |
