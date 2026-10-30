# Beslissingen
[Documentatie](README.md) › Beslissingen

Wat vastligt, wat voorgesteld is, en wat nog open staat. Voeg nieuwe beslissingen bovenaan de juiste tabel toe, met datum.

## Genomen
| Datum      | Beslissing                                                                                                                                      | Waar                                                                             |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 2026-10-30 | Alles wat de site toont, staat lokaal (cache en frontend data, plaatjes inbegrepen), zodat we kunnen presenteren als een externe dienst uitvalt | [architectuur.md](architectuur.md#principes)                                     |
| 2026-10-30 | De pipeline haalt volledige kopieën van de bronnen op (alle triples) en filtert daarna lokaal wat we tonen                                      | [pipeline.md](pipeline.md#uitgangspunt-eerst-alles-kopiëren-dan-lokaal-filteren) |
| 2026-10-30 | Plaatjes en andere bestanden serveren we zelf, uit `media/`                                                                                     | [frontend-data.md](frontend-data.md#bestanden)                                   |
| 2026-10-30 | Twee soorten data in de content: chapters (verhalen) en records (verwijzingen naar Linked Data elders)                                          | [content-repo.md](content-repo.md#twee-soorten-data-chapters-en-records)         |
| 2026-10-30 | De interne links tussen chapters en records worden omgezet naar een URL-structuur, zodat ze behouden blijven                                    | [frontend-data.md](frontend-data.md#url-structuur)                               |
| 2026-10-30 | Live bronnen, zoals de kaarttegels voor de interactieve kaart, haalt de frontend zelf op                                                        | [frontend.md](frontend.md#live-bronnen)                                          |
| 2026-10-30 | Markdown in de code-repo is GitHub-markdown (lezen in de browser); in de content-repo is het Obsidian-markdown                                  | [CLAUDE.md](../CLAUDE.md#markdown-github-hier-obsidian-in-de-content-repo)       |
| 2026-10-30 | De website is statisch. Geen eigen backend                                                                                                      | [architectuur.md](architectuur.md)                                               |
| 2026-10-30 | Frontend: Vue 3 met componenten, JavaScript (geen TypeScript), SCSS, HTML. Vertrekpunt is Hays template vue3-pinia                              | [frontend.md](frontend.md#stack)                                                 |
| 2026-10-30 | Pipeline in Python, met uv                                                                                                                      | [pipeline.md](pipeline.md)                                                       |
| 2026-10-30 | Twee repo's: de content-repo is de *source of truth* en alleen bron; alle techniek staat in de code-repo                                        | [content-repo.md](content-repo.md)                                               |
| 2026-10-30 | Linked Data uit de frontmatter wordt opgehaald en gecachet in SQLite                                                                            | [pipeline.md](pipeline.md#cache)                                                 |
| 2026-10-30 | De frontend krijgt één JSON-bestand plus losse bestanden (plaatjes, later misschien audio en andere)                                            | [frontend-data.md](frontend-data.md)                                             |
| 2026-10-30 | Eerst lokaal ontwikkelen, daarna de server                                                                                                      | [ontwikkelen.md](ontwikkelen.md)                                                 |
| 2026-10-30 | Codeconventies volgens CLAUDE.md                                                                                                                | [CLAUDE.md](../CLAUDE.md)                                                        |

## Verder genomen beslissingen
Waar een vinkje (✅) voorstaat is besloten

| Besloten | Voorstel                                                          | Waarom                                                                                | Waar                                 |
| -------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------ |
| ✅        | Pipeline in twee stappen, `fetch` en `build`                      | `build` blijft snel en werkt offline                                                  | [pipeline.md](pipeline.md)           |
| ✅        | Eén adapter per soort bron, met `fetch`, `matches` en `normalize` | Een bron toevoegen is één bestand                                                     | [pipeline.md](pipeline.md)           |
| ✅        | De cache bewaart alleen ruwe antwoorden                           | Normalisatie aanpassen zonder opnieuw op te halen                                     | [pipeline.md](pipeline.md)           |
| ✅        | Content lokaal in `content/`, pad in te stellen                   | Geen submodule nodig, wel overal hetzelfde                                            | [content-repo.md](content-repo.md)   |
| ✅        | De pipeline kijkt naar `type`, niet naar de map                   | Robuust voor bestanden in de verkeerde map                                            | [content-repo.md](content-repo.md)   |
| ✅        | `uri` mag geen lijst zijn                                         | Een record kan maar één bron hebben                                                   | [content-repo.md](content-repo.md)   |
| ✅        | De pipeline zet markdown NIET om in HTML                          | De frontend maakt gebruik van een markdown parser om de markdown om te zetten in HTML | [frontend-data.md](frontend-data.md) |
| ✅        | camelCase in `siboga.json`                                        | Sluit aan bij de JavaScript-conventies                                                | [frontend-data.md](frontend-data.md) |
| ✅        | Ids als slug van de bestandsnaam                                  | Leesbare URL's, geen extra veld nodig in de content                                   | [frontend-data.md](frontend-data.md) |
| ✅        | Voorbeeld-JSON in `frontend/fixtures/`                            | Frontend bouwen zonder pipeline                                                       | [frontend-data.md](frontend-data.md) |
| ✅        | Router maakt gebruik van volledige paden (geen hashes)            |                                                                                       | [frontend.md](frontend.md)           |
| ✅        | Leaflet voor de kaart                                             | Al gebruikt in het kaartprototype                                                     | [frontend.md](frontend.md)           |
| ✅        | Store via `provide`/`inject`                                      | Zo staat het in de conventies, hoewel de template `useStore()` direct importeert      | [frontend.md](frontend.md)           |

## Open vragen
- Welke velden willen we per `contenttype` uit de bronnen halen en tonen?
	- Dit gaan we nog later bepalen
- Hoe schrijft een redacteur meerdere bronnen voor één record: `uri` als lijst, of een apart veld `sources`?
	- Apart veld sources, een record mag altijd maar één uri hebben
- Plaatjes zelf serveren (downloaden naar `media/`) of rechtstreeks van Wikimedia Commons en archieven laden? Zelf serveren is sneller en betrouwbaarder, maar dan moeten we licentie en bronvermelding goed overnemen.
	- Altijd licentie en bronvermelding overnemen! Plaatjes lokaal ophalen
- Hoe gaan we om met bronnen zonder Linked Data-endpoint, zoals Delpher en het Stadsarchief Amsterdam?
	- Kijk of er een
- Waarvoor gebruiken we `location` bij een hoofdstuk: alleen voor de kaart, of ook voor de volgorde?
- Is de site alleen Nederlands? `description_nl` doet vermoeden dat er later meer talen komen.
- Welke live bronnen komen er naast de kaarttegels?
- Wanneer wordt er opnieuw gebouwd: met de hand, of automatisch bij een wijziging in de content-repo (bijvoorbeeld met een GitHub Action of een cronjob op de server)?
- Waar draait de pipeline als hij automatisch gaat: lokaal, op de server, of in GitHub Actions?

## Zie ook
- [README.md](README.md): overzicht van alle documentatie
- [architectuur.md](architectuur.md): het geheel waar deze beslissingen in passen
