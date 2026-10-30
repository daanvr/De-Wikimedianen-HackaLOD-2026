# Documentatie De Siboga Expeditie
Dit is de technische documentatie van de website De Siboga Expeditie. Ze is geschreven vóór er code was, als startpunt. Voor elke concrete taak maken we daarna een apart plan.

Status: ontwerp (2026-10-30). Wat hier staat is het afgesproken uitgangspunt; wat nog open staat, staat in [beslissingen.md](beslissingen.md).

## Bestanden
| Bestand | Inhoud |
|---|---|
| [architectuur.md](architectuur.md) | Het geheel: de twee repo's, de datastroom, de onderdelen en hoe ze op elkaar aansluiten |
| [content-repo.md](content-repo.md) | De content-repo: Obsidian-markdown, frontmatter, wikilinks, en wat de pipeline ervan mag verwachten |
| [pipeline.md](pipeline.md) | De Python-pipeline: Linked Data ophalen, cachen in SQLite, frontend data bouwen |
| [frontend-data.md](frontend-data.md) | Het contract tussen pipeline en frontend: `siboga.json` en de mediabestanden |
| [frontend.md](frontend.md) | De Vue-frontend: stack, structuur, store, live bronnen, styling |
| [ontwikkelen.md](ontwikkelen.md) | Lokaal ontwikkelen, de `justfile`, en later uitrollen naar de server |
| [beslissingen.md](beslissingen.md) | Genomen beslissingen, voorstellen die nog bevestigd moeten worden, en open vragen |

De codeconventies staan in [CLAUDE.md](../CLAUDE.md) in de root van de repo. Ze gelden voor mensen en voor code agents.

## Begrippen
| Begrip | Betekenis |
|---|---|
| Content-repo | De GitHub-repo met markdownbestanden ([hay/siboga-content](https://github.com/hay/siboga-content)), geschreven in Obsidian. Het redactiesysteem en de *source of truth*. |
| Code-repo | Deze repo. Hier staat alle techniek. |
| Record | Een markdownbestand met `type: record`: een persoon, voorwerp, plek, foto, artikel enzovoort, met een verwijzing naar een bron. |
| Chapter | Een markdownbestand met `type: chapter`: een hoofdstuk van het verhaal, met wikilinks naar records. |
| Bron | Een Linked Data-endpoint waar een record naar verwijst, bijvoorbeeld Wikidata. |
| Cache | De SQLite-database waarin de pipeline opgehaalde bronnen bewaart. Alleen voor de pipeline, nooit voor de frontend. |
| Frontend data | De uitvoer van de pipeline: één JSON-bestand plus mediabestanden. Het enige wat de frontend van de pipeline ziet. |
| Live bron | Data die de browser zelf ophaalt terwijl de site draait, zoals kaarttegels. |
