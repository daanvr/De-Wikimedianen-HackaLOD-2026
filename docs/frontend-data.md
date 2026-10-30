# Frontend data
[Documentatie](README.md) › Frontend data

Het contract tussen [pipeline](pipeline.md) en [frontend](frontend.md): de pipeline schrijft het, de frontend leest het.

```
frontend/public/data/      ← niet in git
├── siboga.json
└── media/                 ← alle plaatjes, ook die van Wikimedia Commons
```

Een met de hand gemaakte versie komt in `frontend/fixtures/siboga.example.json`, zodat je zonder pipeline aan de frontend kunt werken. Die is er nog niet, net als de frontend zelf.

## URL's
Elke page, chapter en record krijgt een eigen URL. Het id is een slug van de bestandsnaam.

| Content-repo                                        | Ref                                                     | URL                         |
| --------------------------------------------------- | ------------------------------------------------------- | --------------------------- |
| `pages/about.md`                                    | `pages/about`                                           | `/pages/about`              |
| `Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam.md` | `chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam` | `/chapters/hoofdstuk-1-...` |
| `Anna Weber.md`                                     | `records/anna-weber`                                    | `/records/anna-weber`       |

## siboga.json
Sleutels in camelCase.

```json
{
    "meta": {
        "schemaVersion": 2,
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
    "chapters": [
        {
            "ref": "chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "id": "hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "title": "Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam",
            "number": 1,
            "location": "records/haven-jakarta",
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
            "description": "Nederlandse algoloog (1852-1942)",
            "uri": "https://www.wikidata.org/wiki/Q1940785",
            "source": "wikidata",
            "body": null,
            "image": {
                "src": "media/anna-weber.jpg",
                "credit": "University of Amsterdam, Artis Library",
                "license": "Public domain",
                "licenseUrl": null,
                "sourceUrl": "https://commons.wikimedia.org/wiki/File:Anna_Antoinette_Weber-van_Bosse.jpg"
            },
            "coordinates": null,
            "fields": [
                {
                    "key": "birth_date",
                    "type": "date",
                    "values": ["1852-03-27"]
                },
                {
                    "key": "birth_place",
                    "type": "text",
                    "values": ["Amsterdam"]
                },
                {
                    "key": "death_date",
                    "type": "date",
                    "values": ["1942-10-29"]
                },
                {
                    "key": "occupation",
                    "type": "text",
                    "values": ["bioloog", "botanicus", "algenkundige"]
                }
            ],
            "links": [],
            "backlinks": ["chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam"]
        }
    }
}
```

- `messages` zijn de teksten van de site zelf, uit `type: i18n` in de content-repo. De frontend gebruikt ze voor alle tekst in de HTML.
- Pages en records staan in een object met het id als sleutel. Chapters staan in een lijst, gesorteerd op `number` (niet op `location`).
- `title` is bij chapters en records de bestandsnaam, bij pages het veld `title`. `label` is de naam volgens de bron. `description` komt uit `description_nl`, anders uit de bron. `source` is de naam van de adapter.
- `links` zijn de refs waar de tekst naar verwijst, `backlinks` de items die naar dit item verwijzen.
- Teksten zijn Nederlands; er zijn nog geen velden per taal.
- Velden zonder waarde staan er met `null` (of een lege lijst), zodat de frontend nooit hoeft te raden.
- Een plaatje heeft altijd `credit` en `license`; zonder die twee laat de pipeline het weg. Paden in `src` en in de markdown zijn relatief aan de map met `siboga.json`.

## Velden per contenttype
`fields` hangt af van het `contentType` van het record, niet van de bron. Welke velden bij welk contenttype horen en in welke volgorde, staat in [pipeline/fields.toml](../pipeline/fields.toml). Alleen velden met een waarde komen in de lijst.

- `key`: de naam van het veld, bijvoorbeeld `birth_date` of `scientific_name`. Het label op de site is het bericht `field_<key>` uit `messages`.
- `type`: `date` (altijd `YYYY`, `YYYY-MM` of `YYYY-MM-DD`) of `text`.
- `values`: altijd een lijst, ook bij één waarde; een persoon kan meer beroepen hebben.

## Tekst en links
`body` is markdown; de frontend zet die om in HTML. Wel zet de pipeline de Obsidian-schrijfwijzen om in gewone markdown, zodat elke markdown-parser ermee overweg kan:
- `[[Anna Weber]]` wordt `[Anna Weber](/records/anna-weber)`;
- `![[foto.jpg]]` wordt `![](media/foto.jpg)`;
- een link naar iets wat niet bestaat wordt gewone tekst, met een waarschuwing.

## Wijzigen
Pas bij een wijziging dit document, de Pydantic-modellen in `pipeline/src/siboga/build.py` en de voorbeeld-JSON samen aan. `uv run siboga check` controleert de uitvoer tegen die modellen. Breekt het de frontend, dan gaat `schemaVersion` omhoog; dat is nu 2, omdat `dates` vervangen is door `fields` en `messages` en `pages` erbij kwamen.
