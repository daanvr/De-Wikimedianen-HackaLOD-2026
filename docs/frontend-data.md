# Frontend data
[Documentatie](README.md) › Frontend data

De frontend data is het contract tussen de [pipeline](pipeline.md) en de [frontend](frontend.md). De pipeline schrijft het, de frontend leest het, en verder weten ze niets van elkaar.

## Bestanden
```
frontend/public/data/
├── siboga.json
└── media/
    ├── anna-weber.jpg
    └── ...
```

- In ontwikkeling schrijft de pipeline naar `frontend/public/data/`. Vite serveert dat als `/data/` en neemt het mee in de build.
- De map staat niet in git. Een kleine, met de hand gemaakte versie staat wel in git, in `frontend/fixtures/siboga.example.json`. Daarmee kun je aan de frontend werken zonder dat de pipeline draait.
- In `media/` staan **alle** plaatjes en andere bestanden (later misschien audio) die de site toont. De frontend laadt nooit een plaatje rechtstreeks van Wikimedia Commons of een archief, zodat de site blijft werken als zo'n dienst uitvalt. Zie [architectuur.md](architectuur.md#principes).
- De bestandsnaam in `media/` is het id van het record plus de extensie.

## URL-structuur
Chapters en records verwijzen in de content-repo naar elkaar met wikilinks (zie [content-repo.md](content-repo.md#tekst-obsidian-markdown)). Op de site wordt elke chapter en elk record een eigen pagina met een vaste URL, en elke interne link wordt een link naar die URL. Zo blijft het netwerk van verwijzingen uit de content behouden.

De URL volgt de mappen van de content-repo:

| In de content-repo | Op de site |
|---|---|
| `chapters/Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam.md` | `/chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam` |
| `records/Anna Weber.md` | `/records/anna-weber` |
| `[[Anna Weber]]` in een tekst | `<a href="/records/anna-weber">` |

Een **ref** is die URL zonder de eerste `/`: `records/anna-weber`. Overal in `siboga.json` waar naar een ander item verwezen wordt, staat een ref. De frontend maakt er een URL van door er `/` voor te zetten.

De soort (`chapters` of `records`) komt uit het veld `type` in de frontmatter, niet uit de map waar het bestand staat.

## siboga.json
De sleutels zijn camelCase, omdat de frontend JavaScript is. De pipeline zet ze om vanuit snake_case met Pydantic (`alias_generator`).

```json
{
    "meta": {
        "schemaVersion": 1,
        "generatedAt": "2026-10-30T14:00:00Z",
        "contentCommit": "dc048d0",
        "warnings": 3
    },
    "chapters": [
        {
            "id": "hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "ref": "chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "number": 1,
            "title": "Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam",
            "location": "records/haven-jakarta",
            "bodyHtml": "<p><a href=\"/records/anna-weber\" data-ref=\"records/anna-weber\">Anna Weber</a> was aan boord van de Siboga. ...</p>",
            "links": ["records/anna-weber", "records/foto-van-anna-weber-terwijl-ze-algen-onderzoekt"],
            "backlinks": []
        }
    ],
    "records": {
        "anna-weber": {
            "id": "anna-weber",
            "ref": "records/anna-weber",
            "title": "Anna Weber",
            "contentType": "person",
            "description": "Nederlands wierendeskundige",
            "bodyHtml": null,
            "sources": [
                {
                    "uri": "https://www.wikidata.org/wiki/Q1940785",
                    "adapter": "wikidata",
                    "fetchedAt": "2026-10-30T13:55:00Z"
                }
            ],
            "image": {
                "src": "media/anna-weber.jpg",
                "credit": "...",
                "license": "...",
                "sourceUrl": "https://commons.wikimedia.org/wiki/File:..."
            },
            "coordinates": null,
            "dates": {
                "birth": "1852-03-27",
                "death": "1942-10-29"
            },
            "facts": [
                {
                    "label": "Beroep",
                    "value": "botanicus",
                    "source": "https://www.wikidata.org/wiki/Q1940785"
                }
            ],
            "links": [],
            "backlinks": ["chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam"]
        }
    }
}
```

### meta
| Veld | Betekenis |
|---|---|
| `schemaVersion` | Versie van dit formaat. Gaat omhoog bij elke wijziging die de frontend kan breken. De frontend controleert hem bij het laden |
| `generatedAt` | Wanneer de pipeline dit bestand schreef |
| `contentCommit` | Commit van de content-repo waarvan gebouwd is, als die bekend is |
| `warnings` | Aantal waarschuwingen tijdens `build` |

### Velden van chapters en records
Chapters staan in een lijst, gesorteerd op `number`. Records staan in een object met het id als sleutel, zodat de frontend een record direct kan opzoeken.

| Veld | Chapter | Record | Betekenis |
|---|---|---|---|
| `id` | ja | ja | Slug van de bestandsnaam |
| `ref` | ja | ja | Soort plus id, zie [URL-structuur](#url-structuur) |
| `title` | ja | ja | Bestandsnaam zonder `.md` |
| `bodyHtml` | ja | ja | De tekst onder de frontmatter als HTML, met interne links omgezet. `null` als er geen tekst is |
| `links` | ja | ja | Refs van alle items waar dit item naar verwijst, in volgorde van voorkomen |
| `backlinks` | ja | ja | Refs van alle items die naar dit item verwijzen |
| `number` | ja | | Volgnummer uit `chapter` in de frontmatter |
| `location` | ja | | Ref van het record uit `location`, of `null` |
| `contentType` | | ja | Uit `contenttype` in de frontmatter |
| `description` | | ja | `description_nl` uit de frontmatter, anders de beschrijving uit de bron, anders `null` |
| `sources` | | ja | De bronnen uit `uri`, met de adapter die erbij hoort (`null` als er geen past) en wanneer ze zijn opgehaald |
| `image` | | ja | Afbeelding uit de bron, of `null`. `src` is relatief aan `data/` en wijst altijd naar `media/` |
| `coordinates` | | ja | `{ "lat": ..., "lon": ... }` of `null` |
| `dates` | | ja | Datums uit de bron die bij het `contentType` passen, of `null` |
| `facts` | | ja | De gefilterde gegevens uit de bronnen, klaar om te tonen: label, waarde, bron. Welke gegevens dat zijn, staat in [pipeline.md](pipeline.md#filteren) |

Velden die er niet zijn, staan er wel in met `null` (of een lege lijst). Zo hoeft de frontend nooit te raden of een sleutel bestaat.

## Ids
Het id is een slug van de bestandsnaam: kleine letters, accenten weg, alles wat geen letter of cijfer is wordt `-`. `Hr.Ms. Siboga` wordt `hr-ms-siboga`. Twee bestanden van dezelfde soort met hetzelfde id geven een waarschuwing en krijgen `-2`, `-3` erachter.

## Links in bodyHtml
De pipeline zet markdown om in HTML, zodat de frontend geen markdown-parser nodig heeft.
- Een interne link naar een bestaand item wordt `<a href="/records/anna-weber" data-ref="records/anna-weber">label</a>`. De frontend vangt klikken op links met `data-ref` af en laat de router de pagina tonen, zonder de hele site opnieuw te laden.
- Een interne link naar iets dat niet bestaat, wordt `<span data-missing-link>label</span>` en geeft een waarschuwing.
- Een embed van een plaatje wordt `<img src="data/media/...">`; het bestand staat in `media/`.
- Externe links (`[tekst](https://...)`) blijven gewone links.

## Wijzigen
Elke wijziging aan dit formaat gaat in drie stappen in dezelfde commit: dit document, de Pydantic-modellen in `pipeline/src/siboga/build/models.py`, en `frontend/fixtures/siboga.example.json`. Breekt de wijziging de frontend, dan gaat `schemaVersion` omhoog.

## Zie ook
- [pipeline.md](pipeline.md): hoe dit bestand gemaakt wordt
- [frontend.md](frontend.md): hoe dit bestand gelezen wordt, en de routes die bij de URL-structuur horen
- [content-repo.md](content-repo.md): waar de chapters, records en links vandaan komen
