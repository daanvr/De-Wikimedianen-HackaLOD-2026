# Soortbeelden
[Documentatie](README.md) › Soortbeelden

Illustratieve foto's bij de 183 specimens met een station uit de [gouden dataset](gouden-dataset.md), voor de [ontdekmodus](ontdekmodus.md). Het zijn **waarnemingen van levende dieren en algen in de natuur**, met een open licentie. Het zijn **nooit foto's van de Siboga-specimens zelf**.

```
frontend/public/datasets/
├── soortbeelden.json          ← in git, op de site als /datasets/soortbeelden.json
└── soortbeelden/              ← de foto's (onveranderd) en thumbs/ (480 px)
```

Het bestand staat los van de [frontend data](frontend-data.md): de pipeline maakt het niet en raakt het niet aan. Het wordt als geheel vervangen door een nieuwe versie, samen met de map `soortbeelden/`.

## Voorwaarden voor gebruik
We mogen deze foto's alleen tonen als duidelijk is hoe ver ze van het specimen afstaan:

1. **Elk beeld krijgt een zichtbaar label** met `overeenkomst[…].badge`. Bij een verwante soort is dat altijd **"Verwante soort"**, goed leesbaar op of direct bij de foto.
2. **Een klik op de foto of op het label opent een venster** met:
   - de foto groot (`src`);
   - de titel en uitleg van het niveau (`overeenkomst[…].titel` en `.uitleg`);
   - wat er op de foto staat (`label`);
   - de `kanttekening` van het specimen als die er is;
   - de onderbouwing (`toelichting` bij het taxon);
   - de bronvermelding met link naar de waarneming en de licentie.
3. **De bronvermelding staat altijd bij de foto**, ook bij CC0: `bronvermelding`, of maker, licentie en een link naar `pagina`.
4. **Bij `geen-beeld` tonen we geen foto van iets anders.** Hooguit de uitleg uit `overeenkomst["geen-beeld"]`.

In de ontdekmodus is dit zo gebouwd: zie *Specimen* en *Duik* in [ontdekmodus.md](ontdekmodus.md#wat-je-ziet). Zonder `soortbeelden.json` werkt de ontdekmodus ook; dan zie je alleen de eigen foto's van de musea.

## In het kort
| | |
| --- | --- |
| Versie | 1.0 (31 oktober 2026) |
| Specimens met een foto | 157 van 183 |
| zelfde soort (`zelfde-soort`) | 28 |
| alleen tot geslacht bekend, foto van een soort uit dat geslacht (`geslacht`) | 6 |
| verwante soort uit hetzelfde geslacht (`verwante-soort`) | 123 |
| geen foto (`geen-beeld`) | 26 |
| Foto op het meest specifieke niveau van het specimen (`meest_specifiek`) | 32 |
| Foto's | 80, samen 35 MB, plus thumbs |
| Licenties | CC0, CC BY (2.0 en 4.0) en CC BY-SA 4.0; nooit NC of ND |
| Bronnen | iNaturalist (research grade) en Wikimedia Commons |

Taxa uit hetzelfde geslacht delen vaak hetzelfde beeld. Dat is bewust zo: een ander beeld van hetzelfde niveau is niet nauwkeuriger. Een specifieker beeld gaat altijd voor.

## Hoe de beelden gekozen zijn
- **Alleen waarnemingen.** Geen museumexemplaren, herbariumvellen, vitrines, typemateriaal, wetenschappelijke platen of figuren uit artikelen. Die tonen een bepaald ander exemplaar, dat zomaar voor het Siboga-specimen kan worden aangezien.
- **Iedere foto is met de hand bekeken.** Dode vissen, hengelfoto's, onscherpe beelden en beelden waarop het organisme niet het onderwerp is, vielen af.
- **iNaturalist: alleen research grade.** De determinatie is dan door de gemeenschap bevestigd: minstens twee personen, twee derde eens. Dat is geen controle door een deskundige.
- **Naam en geslacht via de GBIF-backbone.** Een iNaturalist-taxon telt alleen mee als het in dezelfde stam zit. Zo vielen naamgenoten af: *Mastophora* is op iNaturalist ook een spinnengeslacht, *Thalia* ook een plantengeslacht.
- **Synoniemen tellen als dezelfde soort.** Bijvoorbeeld *Roseolithon crispatum* voor *Lithothamnion crispatum*. De naam op de foto staat altijd in `afgebeeld_taxon`.
- **De meest specifieke naam komt van het museum.** Soms gaat die dieper dan de dataset: tien specimens zijn tot een vorm gedetermineerd (bijvoorbeeld *Lithothamnion australe f. minutulum*), en bij drie mosdiertjes kent het museum de soort waar GBIF alleen het geslacht kent. Dat staat in `naam_specifiekst` en in de `kanttekening`.

## Formaat
```json
{
  "dataset": { "titel": "…", "versie": "1.0", "gebouwd": "…", "uitleg": "…" },
  "overeenkomst": {
    "verwante-soort": { "badge": "Verwante soort", "titel": "…", "uitleg": "…" }
  },
  "beelden": {
    "inat-600789024": {
      "src": "/datasets/soortbeelden/inat-600789024.jpg",
      "thumb": "/datasets/soortbeelden/thumbs/inat-600789024.jpg",
      "afgebeeld_taxon": "Lithothamnion corallioides", "afgebeeld_rang": "soort",
      "maker": "…", "licentie": "CC-BY-4.0", "licentie_url": "…",
      "bron": "iNaturalist", "pagina": "https://www.inaturalist.org/observations/…",
      "bronvermelding": "Foto: …, CC-BY-4.0, via iNaturalist, https://…",
      "datum": "2025-12-16", "plaats": "Las Palmas, España"
    }
  },
  "taxa": {
    "Lithothamnion australe": [
      { "beeld": "inat-600789024", "rol": "hoofdbeeld", "overeenkomst": "verwante-soort", "label": "…", "toelichting": "…" }
    ]
  },
  "specimens": {
    "1041884638": {
      "taxon": "Lithothamnion australe", "naam_specifiekst": "Lithothamnion australe f. minutulum",
      "beeld": "inat-600789024", "overeenkomst": "verwante-soort",
      "label": "Op de foto: …", "kanttekening": "…", "meest_specifiek": false
    }
  }
}
```

- `specimens` heeft als sleutel het GBIF-id, net als `gbif` in de gouden dataset. Een specimen zonder foto heeft `beeld: null` en `overeenkomst: "geen-beeld"`.
- `taxa` geeft per taxon het hoofdbeeld en hooguit twee reservebeelden (`rol`), elk met een eigen `toelichting`. Daarin staat hoe de naam is vastgesteld, op welk niveau het beeld overeenkomt, de licentie en wat er bij de visuele controle te zien was.
- Bij `overeenkomst` horen vier sleutels: `zelfde-soort`, `geslacht`, `verwante-soort` en `geen-beeld`.

## Voorbeeld (JavaScript)
```js
const sb = await fetch('/datasets/soortbeelden.json').then((r) => r.json());

function illustration(gbif) {
    const spec = sb.specimens[gbif];

    if (!spec?.beeld) {
        return null;
    }

    const level = sb.overeenkomst[spec.overeenkomst];
    const extra = sb.taxa[spec.taxon].find((entry) => entry.beeld === spec.beeld);

    return {
        ...sb.beelden[spec.beeld],
        badge : level.badge,
        title : level.titel,
        explanation : level.uitleg,
        label : spec.label,
        note : spec.kanttekening,
        reasoning : extra?.toelichting
    };
}
```

## Let op
- **Veel foto's komen uit andere zeeën** (Atlantische Oceaan, Middellandse Zee, Caribisch gebied) dan de Indonesische wateren van de Siboga. De plaats staat in `plaats`.
- **CC BY-SA** vraagt dat een bewerking, zoals een uitsnede, onder dezelfde licentie gedeeld wordt.
- **Determinaties zijn niet door ons gecontroleerd.** Ze komen van de waarneming of van de maker op Commons.
