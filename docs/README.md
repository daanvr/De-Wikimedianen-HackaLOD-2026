# Documentatie De Siboga Expeditie
Dit is de technische documentatie van de website De Siboga Expeditie, en het startpunt voor alle andere documenten. Ze is geschreven vóór er code was. Voor elke concrete taak maken we daarna een apart plan.

Status: ontwerp (2026-10-30). Wat hier staat is het afgesproken uitgangspunt; wat nog open staat, staat in [beslissingen.md](beslissingen.md).

## In het kort
- De site is **statisch**: een [Vue-frontend](frontend.md) die één JSON-bestand en een map met plaatjes leest, de [frontend data](frontend-data.md).
- De inhoud komt uit de [content-repo](content-repo.md), geschreven in Obsidian. Daarin staan twee soorten bestanden: **chapters** (de verhalen) en **records** (verwijzingen naar Linked Data elders, zoals Wikidata).
- Een [Python-pipeline](pipeline.md) haalt van elke bron een volledige kopie op, bewaart die in SQLite, filtert lokaal wat we tonen, en schrijft de frontend data.
- **Alles staat lokaal.** Valt een externe dienst uit, dan werkt de site nog. Zie de [principes](architectuur.md#principes).
- **Links blijven links.** Elke chapter en elk record krijgt een eigen URL, en de interne links uit de content wijzen daarheen. Zie de [URL-structuur](frontend-data.md#url-structuur).

## Leesvolgorde
1. [architectuur.md](architectuur.md) voor het geheel.
2. [content-repo.md](content-repo.md), [pipeline.md](pipeline.md), [frontend-data.md](frontend-data.md) en [frontend.md](frontend.md): de onderdelen, in de volgorde waarin de data erdoorheen stroomt.
3. [ontwikkelen.md](ontwikkelen.md) om aan de slag te gaan.
4. [beslissingen.md](beslissingen.md) voor wat vastligt en wat nog open staat.

## Bestanden
| Bestand                              | Inhoud                                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| [architectuur.md](architectuur.md)   | Het geheel: de twee repo's, de datastroom, de onderdelen, de naden ertussen en de principes             |
| [content-repo.md](content-repo.md)   | De content-repo: chapters en records, frontmatter, Obsidian-markdown, en wat de pipeline moet verdragen |
| [pipeline.md](pipeline.md)           | De Python-pipeline: volledige kopieën ophalen, cachen in SQLite, lokaal filteren, frontend data bouwen  |
| [frontend-data.md](frontend-data.md) | Het contract tussen pipeline en frontend: `siboga.json`, de mediabestanden en de URL-structuur          |
| [frontend.md](frontend.md)           | De Vue-frontend: stack, structuur, routes, store, live bronnen met terugvaloptie, styling               |
| [ontwikkelen.md](ontwikkelen.md)     | Lokaal ontwikkelen, de `justfile`, presenteren zonder internet, en uitrollen naar de server             |
| [beslissingen.md](beslissingen.md)   | Genomen beslissingen, voorstellen die nog bevestigd moeten worden, en open vragen                       |

De codeconventies staan in [CLAUDE.md](../CLAUDE.md) in de root van de repo. Ze gelden voor mensen en voor code agents. Het inhoudelijke overzicht van de expeditie zelf staat in [expeditie/](../expeditie/README.md).

## Begrippen
| Begrip        | Betekenis                                                                                                                                                                                                        |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Content-repo  | De GitHub-repo met markdownbestanden ([hay/siboga-content](https://github.com/hay/siboga-content)), geschreven in Obsidian. Het redactiesysteem en de *source of truth*. Zie [content-repo.md](content-repo.md). |
| Code-repo     | Deze repo ([daanvr/De-Wikimedianen-HackaLOD-2026](https://github.com/daanvr/De-Wikimedianen-HackaLOD-2026)). Hier staat alle techniek.                                                                           |
| Chapter       | Een markdownbestand met `type: chapter`: een verhaal, met tekst en links naar records, andere chapters en externe pagina's.                                                                                      |
| Record        | Een markdownbestand met `type: record`: een persoon, voorwerp, plek, foto, artikel enzovoort. Vooral frontmatter, met een verwijzing naar Linked Data elders.                                                    |
| Bron          | Een plek met Linked Data waar een record naar verwijst, bijvoorbeeld Wikidata. Elke soort bron heeft een eigen [adapter](pipeline.md#bronadapters).                                                              |
| Triple        | Eén gegeven uit Linked Data: onderwerp, eigenschap, waarde. Bijvoorbeeld: Anna Weber, geboortedatum, 27 maart 1852.                                                                                              |
| Cache         | De SQLite-database met de volledige kopieën van de bronnen. Alleen voor de pipeline, nooit voor de frontend. Zie [pipeline.md](pipeline.md#cache).                                                               |
| Frontend data | De uitvoer van de pipeline: één JSON-bestand plus mediabestanden. Het enige wat de frontend van de pipeline ziet. Zie [frontend-data.md](frontend-data.md).                                                      |
| Ref           | Hoe items in de frontend data naar elkaar verwijzen, bijvoorbeeld `records/anna-weber`. Met een `/` ervoor is het de URL op de site.                                                                             |
| Live bron     | Data die de browser zelf ophaalt terwijl de site draait, zoals de kaarttegels voor de interactieve kaart. Zie [frontend.md](frontend.md#live-bronnen).                                                           |
