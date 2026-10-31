# Frontend data
[Documentatie](README.md) › Frontend data

Het contract tussen [pipeline](pipeline.md) en [frontend](frontend.md): de pipeline schrijft het, de frontend leest het.

```
frontend/public/data/      ← niet in git
├── siboga.json
└── media/                 ← alle plaatjes, ook die van Wikimedia Commons
```

Een met de hand gemaakte versie komt in `frontend/fixtures/siboga.example.json`, zodat je zonder pipeline aan de frontend kunt werken. Die is er nog niet.

## URL's
Elke page, chapter en record krijgt een eigen URL. Het id is een slug van de bestandsnaam.

| Content-repo                                        | Ref                                                     | URL                         |
| --------------------------------------------------- | ------------------------------------------------------- | --------------------------- |
| `pages/about.md`                                    | `pages/about`                                           | `/pages/about`              |
| `Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam.md` | `chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam` | `/chapters/hoofdstuk-1-...` |
| `Anna Weber.md`                                     | `records/anna-weber`                                    | `/records/anna-weber`       |
| `plugins/IIIF.md` met `id: iiif`                    | `plugins/iiif`                                          | `/plugins/iiif`             |

## siboga.json
Sleutels in camelCase.

```json
{
    "meta": {
        "schemaVersion": 3,
        "generatedAt": "2026-10-30T14:31:28+00:00",
        "contentCommit": "c48b2e9",
        "warnings": 6
    },
    "messages": {
        "about_site": "Over deze site",
        "start_bn": "START EXPEDITIE"
    },
    "pages": {
        "about": {
            "ref": "pages/about",
            "id": "about",
            "title": "Over deze website",
            "body": "Deze prachtige website is gebouwd door ...",
            "links": [],
            "backlinks": []
        }
    },
    "plugins": {
        "iiif": {
            "ref": "plugins/iiif",
            "id": "iiif",
            "title": "IIIF",
            "description": null,
            "showInExplore": false,
            "body": null,
            "links": [],
            "backlinks": ["records/ophioplinthaca-pulchra-koehler-1904"]
        }
    },
    "chapters": [
        {
            "ref": "chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "id": "hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "title": "Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam",
            "number": 1,
            "coordinates": {
                "lat": -6.12,
                "lon": 106.81
            },
            "body": "[Anna Weber](/records/anna-weber) was aan boord van de Siboga. ...",
            "links": ["records/anna-weber", "records/weberolegra-weberi"],
            "backlinks": []
        }
    ],
    "records": {
        "anna-weber": {
            "ref": "records/anna-weber",
            "id": "anna-weber",
            "title": "Anna Weber",
            "contentType": "person",
            "label": "Anna Weber-van Bosse",
            "labelSource": "wikidata",
            "description": "Nederlandse algoloog (1852-1942)",
            "descriptionSource": "wikidata",
            "uri": "https://www.wikidata.org/wiki/Q1940785",
            "source": "wikidata",
            "sources": [
                {
                    "name": "wikidata",
                    "uri": "https://www.wikidata.org/wiki/Q1940785"
                },
                {
                    "name": "nta",
                    "uri": "http://data.bibliotheken.nl/id/thes/p072591218"
                }
            ],
            "body": null,
            "image": {
                "src": "media/anna-weber.jpg",
                "credit": "University of Amsterdam, Artis Library",
                "license": "Public domain",
                "licenseUrl": null,
                "sourceUrl": "https://commons.wikimedia.org/wiki/File:Anna_Antoinette_Weber-van_Bosse.jpg",
                "source": "wikidata"
            },
            "coordinates": null,
            "coordinatesSource": null,
            "fields": [
                {
                    "key": "birth_date",
                    "type": "date",
                    "values": ["1852-03-27"],
                    "source": "wikidata"
                },
                {
                    "key": "birth_place",
                    "type": "text",
                    "values": ["Amsterdam"],
                    "source": "wikidata"
                },
                {
                    "key": "death_date",
                    "type": "date",
                    "values": ["1942-10-29"],
                    "source": "wikidata"
                },
                {
                    "key": "occupation",
                    "type": "text",
                    "values": ["bioloog", "botanicus", "algenkundige"],
                    "source": "wikidata"
                },
                {
                    "key": "work",
                    "type": "text",
                    "values": ["Een jaar aan boord H.M. Siboga", "Liste des algues du Siboga"],
                    "source": "nta"
                }
            ],
            "links": [],
            "backlinks": ["chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam"]
        }
    }
}
```

- `messages` zijn de teksten van de site zelf, uit `type: i18n` in de content-repo. De frontend gebruikt ze voor alle tekst in de HTML.
- Pages, plugins en records staan in een object met het id als sleutel. Het id van een plugin komt uit `id` in de frontmatter, niet uit de bestandsnaam. Chapters staan in een lijst, gesorteerd op `number`. `coordinates` van een chapter komt uit `location` in de frontmatter, en is `null` als die ontbreekt of niet klopt.
- `title` is bij chapters en records de bestandsnaam, bij pages het veld `title`. `label` is de naam volgens de bron. `description` komt uit `description_nl`, anders uit de bron. `source` is de naam van de adapter van `uri`.
- **Elke waarde zegt waar hij vandaan komt.** `sources` zijn alle bronnen waar het record data uit haalt, met naam en URI; de eerste is altijd `uri` zelf, daarna komen [gekoppelde bronnen](pipeline.md#gekoppelde-bronnen-via-wikidata) zoals de NTA. `labelSource`, `descriptionSource`, `coordinatesSource`, `image.source` en `source` bij elk veld noemen de bron van die ene waarde, met een `name` uit `sources`. `descriptionSource` is `content` als de beschrijving uit `description_nl` komt. Zonder waarde is de bron `null`. Een record waarvan de bron niets opleverde, heeft een lege `sources`.
- `links` zijn de refs waar de tekst naar verwijst, `backlinks` de items die naar dit item verwijzen.
- Teksten zijn Nederlands; er zijn nog geen velden per taal.
- Velden zonder waarde staan er met `null` (of een lege lijst), zodat de frontend nooit hoeft te raden.
- `audio` is een geluidsopname, nu alleen van Wikimedia Commons: `src`, `mimeType`, en net als een plaatje `credit`, `license`, `licenseUrl`, `sourceUrl` en `source`. Zonder geluid is het `null`. De frontend toont er een speler voor.
- Een plaatje heeft altijd `credit` en `license`; zonder die twee laat de pipeline het weg. Dat geldt ook voor geluid. Voor een geluidsbestand zonder voorbeeld geeft Commons een algemeen icoon; dat neemt de pipeline niet over als plaatje. Paden in `src` en in de markdown zijn relatief aan de map met `siboga.json`.

## Velden per contenttype
`fields` hangt af van het `contentType` van het record, niet van de bron. Welke velden bij welk contenttype horen en in welke volgorde, staat in [pipeline/fields.toml](../pipeline/fields.toml). Alleen velden met een waarde komen in de lijst.

- `key`: de naam van het veld, bijvoorbeeld `birth_date` of `scientific_name`. Het label op de site is het bericht `field_<key>` uit `messages`.
- `type`: `date` (altijd `YYYY`, `YYYY-MM` of `YYYY-MM-DD`) of `text`.
- `values`: altijd een lijst, ook bij één waarde; een persoon kan meer beroepen hebben.
- `source`: de naam van de bron van dit veld, uit `sources` van het record. Alle waarden van één veld komen uit dezelfde bron: een gekoppelde bron vult alleen velden aan die nog leeg zijn.

## Tekst en links
`body` is markdown; de frontend zet die om in HTML. Wel zet de pipeline de Obsidian-schrijfwijzen om in gewone markdown, zodat elke markdown-parser ermee overweg kan:
- `[[Anna Weber]]` wordt `[Anna Weber](/records/anna-weber)`;
- `![[foto.jpg]]` wordt `![](media/foto.jpg)`;
- `[[IIIF#https://…/default.jpg]]` wordt `[IIIF](/plugins/iiif?argument=https%3A%2F%2F…)`: het argument komt URL-gecodeerd in `argument`. Een alinea met alleen zo'n link toont de frontend als de plugin zelf;
- een link naar iets wat niet bestaat wordt gewone tekst, met een waarschuwing.

Drie schrijfwijzen gaan ongewijzigd door; de frontend maakt ze op ([content-repo.md](content-repo.md#plaatjes-bijschriften-en-galerijen)):
- een plaatje met direct eronder een regel helemaal in cursief wordt een plaatje met bijschrift;
- `::: gallery` ... `:::` wordt een galerij. Dat is geen standaard-markdown: een andere parser toont de twee regels als tekst, met de plaatjes ertussen;
- `:::details Tekst` ... `:::` wordt een inklapblok (`<details>`) met `Tekst` als kopje. Ook dat is geen standaard-markdown.

## Wijzigen
Pas bij een wijziging dit document, de Pydantic-modellen in `pipeline/src/siboga/build.py` en de voorbeeld-JSON samen aan. `uv run siboga check` controleert de uitvoer tegen die modellen. Breekt het de frontend, dan gaat `schemaVersion` omhoog; dat is nu 3, omdat `location` van een chapter (een ref) vervangen is door `coordinates`.
