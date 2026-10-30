# Content-repo
[Documentatie](README.md) › Content-repo

[hay/siboga-content](https://github.com/hay/siboga-content) is een Obsidian-kluis en de *source of truth*. Redacteuren synchroniseren hem met GitHub via de Obsidian-plugin Fit. De [pipeline](pipeline.md) leest een lokale kloon in `content/` en schrijft er nooit in.

## Types
| `type`    | Wat                                         | Hoe                                                                       | Staat nu in |
| --------- | ------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| `chapter` | Een verhaal                                 | Vooral tekst, met links naar records, andere chapters en externe pagina's | `chapters/` |
| `record`  | Een persoon, voorwerp, plek, foto, artikel  | Vooral frontmatter met één bron, hooguit wat tekst                        | `records/`  |
| `page`    | Een vaste pagina, zoals welkom of over ons  | `title` in de frontmatter, de inhoud als gewone markdown                  | `pages/`    |
| `i18n`    | De teksten van de site zelf (knoppen, menu) | Elke sleutel in de frontmatter is een bericht                             | `etc/`      |

De pipeline kijkt naar `type` in de frontmatter, niet naar de map. Bestanden zonder `type` (zoals `README.md`) slaat hij over. De titel van een chapter of record is de bestandsnaam zonder `.md`; een page heeft een eigen `title`.

## Frontmatter
```yaml
---
type: record
uri: https://www.wikidata.org/wiki/Q1940785
description_nl: Nederlands wierendeskundige
contenttype: person
---
```

- `uri`: precies één bron. Er is geen veld voor overige bronnen: die zetten we op Wikidata, of als gewone externe link in de lopende tekst. Een paar identifiers op Wikidata volgt de pipeline wel, zoals het NTA-ID (P1006) van een persoon; zie [gekoppelde bronnen](pipeline.md#gekoppelde-bronnen-via-wikidata). Wil je bij een persoon ook de naamvarianten en werken uit de NTA, voeg dan op Wikidata P1006 toe. Aan de markdown verandert niets.
- `description_nl`: optioneel; gaat voor de beschrijving uit de bron. De site is voorlopig alleen Nederlands, dus de pipeline leest alleen `_nl`-velden.
- `contenttype`: nu `person`, `item`, `media`, `location`, `article`, `expedition` of `specimen`. Het contenttype bepaalt welke velden het record op de site toont, niet de bron: een Wikidata-item over een persoon toont geboortedatum en beroep, een Wikidata-item over een soort de wetenschappelijke naam en familie. Welke velden bij welk contenttype horen, staat in [pipeline/fields.toml](../pipeline/fields.toml).

```yaml
---
type: chapter
chapter: "1"
location: "[[Haven Jakarta]]"
---
```

- `chapter`: volgnummer.
- `location`: verplicht, een wikilink naar een record. Alleen voor de plek op de kaart; de volgorde komt uit `chapter`.

```yaml
---
type: page
title: Over deze website
---
Deze prachtige website is gebouwd door ...
```

- `title`: de titel op de site. Het id en de URL komen wel uit de bestandsnaam (`about.md` wordt `/pages/about`).

```yaml
---
type: i18n
start_bn: START EXPEDITIE
about_site: Over deze site
field_birth_date: Geboren
---
```

- Alle tekst die de site zelf toont, zoals knoppen en menu's, komt uit deze berichten; de frontend zet geen losse tekst in de HTML. Ook al is de site voorlopig alleen Nederlands.
- De namen van velden heten `field_<veld>`, bijvoorbeeld `field_birth_date`. De pipeline waarschuwt welke daarvan nog ontbreken.

## Obsidian-markdown
De pipeline moet in elk geval dit herkennen:
- wikilinks: `[[Anna Weber]]`, `[[Weberolegra weberi|vlinder]]`, `[[Anna Weber#Kop]]`;
- embeds: `![[foto.jpg]]`;
- commentaar: `%%...%%`, dat weggelaten wordt.

Een wikilink verwijst naar een bestandsnaam, niet naar een pad. Wat de pipeline ermee doet, staat in [frontend-data.md](frontend-data.md#tekst-en-links).

## Onaffe content
Er staan nu al lege bestanden, `uri`'s die geen URL zijn (`wikidata`), en links naar bestanden die niet bestaan. De pipeline slaat zoiets over, logt een waarschuwing met de bestandsnaam en gaat door.
