# Content-repo
[Documentatie](README.md) › Content-repo

[hay/siboga-content](https://github.com/hay/siboga-content) is een Obsidian-kluis en de *source of truth*. Redacteuren synchroniseren hem met GitHub via de Obsidian-plugin Fit. De [pipeline](pipeline.md) leest een lokale kloon in `content/` en schrijft er nooit in.

## Types
| `type`    | Wat                                         | Hoe                                                                       | Staat nu in |
| --------- | ------------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| `chapter` | Een verhaal                                 | Vooral tekst, met links naar records, andere chapters en externe pagina's | `chapters/` |
| `record`  | Een persoon, voorwerp, plek, foto, artikel  | Vooral frontmatter met één bron, hooguit wat tekst                        | `records/`  |
| `page`    | Een vaste pagina, zoals welkom of over ons  | `title` in de frontmatter, de inhoud als gewone markdown                  | `pages/`    |
| `plugin`  | Een interactief onderdeel, zoals een IIIF-viewer | Alleen frontmatter; de code staat in de frontend                     | `plugins/`  |
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
- `contenttype`: nu `person`, `item`, `media`, `location`, `publication`, `expedition` of `specimen`. Het contenttype bepaalt welke velden het record op de site toont, niet de bron: een Wikidata-item over een persoon toont geboortedatum en beroep, een Wikidata-item over een soort de wetenschappelijke naam en familie. Welke velden bij welk contenttype horen, staat in [pipeline/fields.toml](../pipeline/fields.toml).

```yaml
---
type: chapter
chapter: "1"
location: -6.12, 106.81
---
```

- `chapter`: volgnummer.
- `location`: verplicht, de plek van de boot op de kaart als `breedtegraad, lengtegraad`. Dat is de volgorde waarin Google Maps en OpenStreetMap coördinaten kopiëren (rechtsklik op de kaart). Alleen voor de kaart; de volgorde van de hoofdstukken komt uit `chapter`. Ligt de plek buiten de kaart, dan waarschuwt de pipeline; vaak zijn de twee getallen dan omgedraaid. Zonder bruikbare `location` ligt de boot bij Soerabaja.

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

## Plugins
```yaml
---
type: plugin
id: deepdive
description_nl: Bekijk waar en welke specimen de Siboga vond
show_in_explore: "true"
---
```

- `id`: verplicht, de naam van de plugin in de frontend (`frontend/src/plugins/index.js`). Ook het id in de URL: `/plugins/deepdive`.
- `title`: optioneel; zonder `title` is de bestandsnaam de titel.
- `description_nl`: optioneel, de beschrijving onder de titel.
- `show_in_explore`: `true` (ook `"true"`) zet de plugin als knop in de ontdekmodus. Standaard `false`.

Een plugin gebruik je in de tekst met een wikilink naar het bestand. Alles na de `#` is het argument voor de plugin:

```markdown
[[IIIF#https://iiif.mcz.harvard.edu/iiif/3/3898457/full/max/0/default.jpg]]
```

Staat zo'n link in een eigen alinea, dan toont de site de plugin in de tekst, met een knop om hem schermvullend te tonen. Midden in een zin is het een gewone link naar de plugin, die dan schermvullend opent.

| Plugin | Argument                                                         |
| ------ | ---------------------------------------------------------------- |
| `iiif` | Een IIIF Image API-URL, een `info.json` of een manifest (`…/manifest.json`); anders een gewoon plaatje. Bij een manifest met meer pagina's kun je bladeren |

Een manifest kan ook zonder `[[IIIF#...]]`: een alinea met alleen de URL van een IIIF-manifest wordt vanzelf de IIIF-viewer.

## Obsidian-markdown
De pipeline moet in elk geval dit herkennen:
- wikilinks: `[[Anna Weber]]`, `[[Weberolegra weberi|vlinder]]`, `[[Anna Weber#Kop]]`;
- embeds: `![[foto.jpg]]`;
- commentaar: `%%...%%`, dat weggelaten wordt.

Een wikilink verwijst naar een bestandsnaam, niet naar een pad. Wat de pipeline ermee doet, staat in [frontend-data.md](frontend-data.md#tekst-en-links).

## Plaatjes, bijschriften en galerijen
Een bijschrift is een regel helemaal in cursief, **direct** onder het plaatje (zonder lege regel ertussen). De tekst tussen `[` en `]` blijft de alt-tekst voor schermlezers; het bijschrift is wat iedereen onder het plaatje ziet. Een bron of licentie hoort in het bijschrift.

```markdown
![Siboga voor anker](siboga.jpg)
*Hr.Ms. Siboga, 1898. [Bron](https://...)*
```

Dat werkt ook met een embed: `![[siboga.jpg]]` met de cursieve regel eronder.

### Licentie
Bij elk plaatje op de site staan de maker en de licentie. Die komen uit het record waar het bijschrift naar linkt: maak voor het plaatje een record (bijvoorbeeld met de Commons-pagina als `uri`) en link er in het bijschrift naar. De site zet de maker en licentie van dat record dan onder het bijschrift, ook in een galerij en schermvullend.

```markdown
![De Siboga in dok](https://commons.wikimedia.org/wiki/Special:FilePath/....jpg?width=1200)
*[[Foto van de Siboga in dok|De Siboga ligt in dok (1899-1900)]]*
```

- De eerste link naar een record in het bijschrift telt. Dat record moet zelf een plaatje met licentie hebben.
- Een plaatje zonder bijschrift, of met een bijschrift zonder link naar zo'n record, geeft een waarschuwing in de pipeline: `image without license`.

Meer plaatjes in een galerij (een carrousel om doorheen te bladeren) zet je tussen `::: gallery` en `:::`. Elk plaatje met zijn bijschrift is een eigen alinea, dus met een lege regel ertussen:

```markdown
::: gallery
![Siboga voor anker](siboga.jpg)
*Hr.Ms. Siboga, 1898. [Bron](https://...)*

![Bemanning aan dek](bemanning.jpg)
*De bemanning, 1899. [Bron](https://...)*
:::
```

- Zet `::: gallery` en `:::` aan het begin van de regel, niet ingesprongen: ingesprongen regels zijn in markdown een codeblok.
- Obsidian kent `:::` niet en toont die regels als gewone tekst, met de plaatjes ertussen. Op de site wordt het een galerij.
- Zonder afsluitende `:::` waarschuwt de pipeline en toont de site de plaatjes los.

## Inklapblokken
Tekst die niet iedereen hoeft te lezen, zoals een lange lijst bronnen, zet je in een inklapblok: tussen `:::details` met het kopje erachter, en `:::`. Op de site staat dan alleen het kopje; klik je erop, dan klapt de rest open.

```markdown
:::details Bekijk alle bronnen
- G.M.W. Acda, [[Op de deining van de wetenschap]] (2019), blz. 149-158.
- [Expeditie Online van Naturalis](https://expeditieonline.naturalis.nl/nl/expeditie/siboga-expeditie).
:::
```

- In een inklapblok werkt alle gewone markdown: lijsten, links, wikilinks, plaatjes.
- Een galerij in een inklapblok mag, maar wordt daar een rij losse plaatjes met bijschrift, geen carrousel. Een plugin wordt er een gewone link.
- Net als bij een galerij: `:::details` en `:::` aan het begin van de regel, en zonder afsluitende `:::` waarschuwt de pipeline en toont de site het als gewone tekst. Obsidian toont de regels met `:::` als gewone tekst.
- Zonder kopje (alleen `:::details`) toont de browser zijn eigen woord, zoals "Details".

## Onaffe content
Er staan nu al lege bestanden, `uri`'s die geen URL zijn (`wikidata`), en links naar bestanden die niet bestaan. De pipeline slaat zoiets over, logt een waarschuwing met de bestandsnaam en gaat door.
