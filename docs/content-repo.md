# Content-repo
[Documentatie](README.md) › Content-repo

[hay/siboga-content](https://github.com/hay/siboga-content) is een Obsidian-kluis en de *source of truth*. Redacteuren synchroniseren hem met GitHub via de Obsidian-plugin Fit. De [pipeline](pipeline.md) leest een lokale kloon in `content/` en schrijft er nooit in.

## Chapters en records
| Soort   | Wat                                        | Hoe                                                                       |
| ------- | ------------------------------------------ | ------------------------------------------------------------------------- |
| Chapter | Een verhaal                                | Vooral tekst, met links naar records, andere chapters en externe pagina's |
| Record  | Een persoon, voorwerp, plek, foto, artikel | Vooral frontmatter met één bron, hooguit wat tekst                        |

De pipeline kijkt naar `type` in de frontmatter, niet naar de map. Bestanden zonder `type` (zoals `README.md`) slaat hij over. De titel is de bestandsnaam zonder `.md`.

## Frontmatter
```yaml
---
type: record
uri: https://www.wikidata.org/wiki/Q1940785
description_nl: Nederlands wierendeskundige
contenttype: person
---
```

- `uri`: precies één bron. Overige bronnen komen evt in de lopende tekst als externe link maar we doen daar verder niks mee.
- `description_nl`: optioneel; gaat voor de beschrijving uit de bron.
- `contenttype`: nu `person`, `item`, `media`, `location`, `article`, `expedition` of `specimen`.

```yaml
---
type: chapter
chapter: "1"
location: "[[Haven Jakarta]]"
---
```

- `chapter`: volgnummer.
- `location`: REQUIRED: optioneel, een wikilink naar een record.

## Obsidian-markdown
De pipeline moet in elk geval dit herkennen:
- wikilinks: `[[Anna Weber]]`, `[[Weberolegra weberi|vlinder]]`, `[[Anna Weber#Kop]]`;
- embeds: `![[foto.jpg]]`;
- commentaar: `%%...%%`, dat weggelaten wordt.

Een wikilink verwijst naar een bestandsnaam, niet naar een pad. Wat de pipeline ermee doet, staat in [frontend-data.md](frontend-data.md#tekst-en-links).

## Onaffe content
Er staan nu al lege bestanden, `uri`'s die geen URL zijn (`wikidata`), en links naar bestanden die niet bestaan. De pipeline slaat zoiets over, logt een waarschuwing met de bestandsnaam en gaat door.
