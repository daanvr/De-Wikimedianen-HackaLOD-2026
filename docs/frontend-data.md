# Frontend data
[Documentatie](README.md) › Frontend data

Het contract tussen [pipeline](pipeline.md) en [frontend](frontend.md): de pipeline schrijft het, de frontend leest het.

```
frontend/public/data/      ← niet in git
├── siboga.json
└── media/                 ← alle plaatjes, ook die van Wikimedia Commons
```

Een met de hand gemaakte versie staat in `frontend/fixtures/siboga.example.json`, zodat je zonder pipeline aan de frontend kunt werken.

## URL's
Elke chapter en elk record krijgt een eigen URL. Het id is een slug van de bestandsnaam.

| Content-repo                                        | Ref                                                     | URL                         |
| --------------------------------------------------- | ------------------------------------------------------- | --------------------------- |
| `Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam.md` | `chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam` | `/chapters/hoofdstuk-1-...` |
| `Anna Weber.md`                                     | `records/anna-weber`                                    | `/records/anna-weber`       |

## siboga.json
Sleutels in camelCase.

```json
{
    "meta": {
        "schemaVersion": 1,
        "generatedAt": "2026-10-30T14:00:00Z"
    },
    "chapters": [
        {
            "ref": "chapters/hoofdstuk-1-de-siboga-vertrekt-uit-amsterdam",
            "title": "Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam",
            "number": 1,
            "location": "records/haven-jakarta",
            "body": "[Anna Weber](/records/anna-weber) was aan boord van de Siboga. ..."
        }
    ],
    "records": {
        "anna-weber": {
            "ref": "records/anna-weber",
            "title": "Anna Weber",
            "contentType": "person",
            "description": "Nederlands wierendeskundige",
            "uri": "https://www.wikidata.org/wiki/Q1940785",
            "body": null,
            "image": {
                "src": "media/anna-weber.jpg",
                "credit": "...",
                "license": "..."
            },
            "coordinates": null,
            "dates": null
        }
    }
}
```

- Chapters staan in een lijst, gesorteerd op `number` (niet op `location`). Records staan in een object met het id als sleutel.
- Teksten zijn Nederlands; er zijn nog geen velden per taal.
- Velden zonder waarde staan er met `null`, zodat de frontend nooit hoeft te raden.
- `image.credit` en `image.license` zijn verplicht als er een plaatje is.

## Tekst en links
`body` is markdown; de frontend zet die om in HTML. Wel zet de pipeline de Obsidian-schrijfwijzen om in gewone markdown, zodat elke markdown-parser ermee overweg kan:
- `[[Anna Weber]]` wordt `[Anna Weber](/records/anna-weber)`;
- `![[foto.jpg]]` wordt `![](media/foto.jpg)`;
- een link naar iets wat niet bestaat wordt gewone tekst, met een waarschuwing.

## Wijzigen
Pas bij een wijziging dit document, de Pydantic-modellen in de pipeline en de voorbeeld-JSON samen aan. Breekt het de frontend, dan gaat `schemaVersion` omhoog.
