# Frontend
[Documentatie](README.md) › Frontend

Een statische Vue 3-app in `frontend/` die de [frontend data](frontend-data.md) toont. Aanvullende instructies komen nog in [CLAUDE.md](../CLAUDE.md).

## Stack
Vertrekpunt is Hays template [vue3-pinia](https://github.com/hay/templates/tree/master/vue3-pinia): Vue 3 met `<script setup>`, Vite, Pinia, SCSS met `valenski`, JavaScript zonder TypeScript. Daarbij komen `vue-router`, `marked` voor de markdown en [MapLibre GL JS](https://maplibre.org/) voor de kaart. De lettertypen (Old Standard TT en Newsreader) komen via `@fontsource` mee in de build, zodat ook die lokaal staan.

Let op: in de template heet het bestand `App.vue`, maar `main.js` importeert `@/app.vue`. Op macOS gaat dat goed, maar op Linux maakt het bestandssysteem onderscheid tussen hoofdletters en kleine letters, en vindt de import het bestand niet. Hernoem het bij het overnemen van de template daarom naar `app.vue`. Dat past ook bij de kebab-case van de andere bestanden. Gebruik in bestandsnamen en imports altijd kleine letters, zodat de build op elk systeem werkt.

## Structuur
```
frontend/
├── public/
│   ├── data/            ← frontend data van de pipeline (niet in git)
│   └── map-layers/      ← kaartlagen: diepte, land, route (wel in git)
├── scripts/
│   └── prepare_map.py   ← maakt public/map-layers/ uit de bronbestanden
└── src/
    ├── main.js
    ├── app.vue          ← laadt de data, houdt de kaart vast, toont de view
    ├── store.js         ← Pinia-store met de frontend data en de kaartstand
    ├── router.js
    ├── components/      ← el-*.vue
    ├── views/           ← vw-*.vue
    ├── plugins/         ← één component per plugin, plus index.js
    ├── services/        ← data laden, kaartlagen, markdown, standaardteksten
    └── scss/
```

Herkomst en licenties van de kaartlagen staan in [frontend/README.md](../frontend/README.md).

## Routes
| URL             | View              | Wat                                                          |
| --------------- | ----------------- | ------------------------------------------------------------ |
| `/`             | `vw-home.vue`     | Welkom (`pages/welcome`), met twee keuzes: het verhaal (eerste hoofdstuk) of de datavisualisatie (`/map`) |
| `/chapters`     | `vw-chapters.vue` | Lijst van hoofdstukken, met gelezen en huidig                |
| `/chapters/:id` | `vw-chapter.vue`  | Verhaalmodus: kaart met markers en tekstvel                  |
| `/records/:id`  | `vw-record.vue`   | Record met plaatje, velden, bron en "Genoemd in"             |
| `/pages/:id`    | `vw-page.vue`     | Vaste pagina, zoals `/pages/about`                           |
| `/plugins/:id`  | `vw-plugin.vue`   | Plugin schermvullend; `?argument=` gaat naar de plugin       |
| `/library`      | `vw-library.vue`  | Bibliotheek: zoeken en filteren op contenttype               |
| `/map`          | `vw-map.vue`      | Datavisualisatie (de ontdekmodus) schermvullend, zie [ontdekmodus.md](ontdekmodus.md); ook de knop na het laatste hoofdstuk gaat hierheen |
| `/spel`         | `vw-game.vue`     | Het spel: zelf varen en specimens verzamelen, zie [spelmodus.md](spelmodus.md); in het menu onder de streep |

Onder elk hoofdstuk staat een knop naar het volgende (`el-chapter-end.vue`). Na het laatste hoofdstuk zijn dat twee knoppen: naar de datavisualisatie (`/map`) en naar de bibliotheek.

Volledige paden, geen hashes. Links in de tekst die met `/` beginnen, gaan via de router. Op de server is daarvoor één regel nginx nodig ([ontwikkelen.md](ontwikkelen.md#server)).

De paginatitel (`document.title`) is de kop van de view met de naam van de site erachter, zoals "Het schip Hr.Ms. Siboga · De Siboga-Expeditie". Het startscherm, en een item dat niet bestaat, krijgt alleen de naam van de site: het bericht `site_title`. `app.vue` houdt de titel bij met `pageTitle()` uit `src/services/page-title.js`, ook als de data pas na de eerste route binnenkomt.

De tags voor het delen op sociale media (Open Graph en Twitter: titel, beschrijving en `public/social.jpg` van 1200 × 630) staan vast in `index.html`. Scrapers zoals die van Facebook voeren geen JavaScript uit, dus ze moeten in de HTML zelf staan. Daardoor heeft elke pagina dezelfde preview. De URL's zijn absoluut, met `https://siboga.nl`.

## Kaart
Eén kaart (`el-map.vue`) blijft staan onder alle views. Views zetten de kaartstand in de store (`store.setMap()`); `app.vue` geeft die als props door. De onderlaag is eigen werk, met vlakke dieptebanden uit `public/map-layers/`, die lokaal staan. Daarop ligt als hoofdlaag de "Kaart van den Trek v. H.M. Siboga 1899-1900" (Stadsarchief Amsterdam), gegeorefereerd met [Allmaps](https://allmaps.org) en live geladen als rastertegels van `allmaps.xyz`. Valt Allmaps uit, dan blijft de eigen onderlaag zichtbaar. De kaart zit niet vast aan de archipel: je kunt over de hele wereld schuiven. Buiten het onderzoeksgebied liggen grove wereldlagen (`world-land.geojson`, `world-bathymetry.geojson`), die MapLibre zelf op de achtergrond laadt, zodat de site er niet op wacht. Daar kun je hooguit tot ongeveer provincieniveau inzoomen (zoom 6); hoe verder je buiten het gebied komt, hoe lager de grens (`limitZoom()` in `el-map.vue`). De route (`public/map-layers/route.geojson`) is één doorlopende lijn van station naar station, met een klein puntje per station; de puntjes zijn niet klikbaar. Zee- en landnamen zijn HTML-labels, zodat er geen glyph-server nodig is; op de historische kaart staan ze niet, want die heeft zijn eigen namen.

Rechts zit een knop voor de kaartlaag (`el-layer-button.vue`), in een hoofdstuk en in de ontdekmodus. Elke tik gaat naar de volgende stand: oude kaart, oude kaart half doorzichtig boven de satellietfoto, zeekaart (alleen de eigen onderlaag) en satelliet. De stand staat in de store als `map.base` en blijft staan als je van view wisselt. De satellietfoto is [Esri World Imagery](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9), live geladen; ook daaronder blijft de eigen onderlaag als vangnet.

Een hoofdstuk met `markers` (uit `geojson` in de content-repo) toont die als HTML-markers met hun naam (`map.markers`). Een marker met een `ref` is klikbaar en opent die pagina; `el-map.vue` meldt de klik met `open` en `app.vue` gaat erheen. De kaart zoomt in op de markers; zonder markers toont hij de hele route. Bij het verlaten van het hoofdstuk verdwijnen de markers. Er vaart geen boot over de kaart: de route ligt er als vaste lijn.

## Data en store
- `app.vue` laadt `data/siboga.json` één keer en controleert `meta.schemaVersion`.
- De store wordt met `provide('store', store)` doorgegeven; componenten doen `inject('store')`.
- Views halen data uit de store, componenten krijgen hun data via props.

## Teksten (i18n)
Geen losse tekst in de HTML. Alle tekst die de site zelf toont, zoals knoppen, menu's en de namen van velden, komt uit `messages` in `siboga.json`, via één functie (bijvoorbeeld `t('start_bn')`) die via `provide`/`inject` beschikbaar is. Zolang een bericht nog niet in de content-repo staat, komt het uit de standaardteksten in `src/services/messages.js`; berichten uit de content-repo gaan altijd voor. Staat een sleutel ook daar niet, dan toont de functie de sleutel. De berichten staan in de content-repo ([content-repo.md](content-repo.md#frontmatter)).

## Velden van een record
Een record heeft een lijst `fields`, al in de goede volgorde voor zijn contenttype. De frontend toont ze zoals ze komen: de naam via `t('field_' + key)`, en de waarden; bij `type: "date"` opgemaakt als datum.

## Begrippen
Een link naar een record met `contentType: "term"` ([begrippen](content-repo.md#begrippen)) gaat niet naar de recordpagina. `el-markdown.vue` vraagt met `lookupTerm` (`store.termForHref`) of een link een begrip is, en toont dan `el-term.vue`: een kaartje bij het woord, met de uitleg (de `body`) en, als er een `uri` is, "Lees meer". Het kaartje gaat open met een klik, op desktop en mobiel hetzelfde, niet bij hover. Het sluit met nog een klik op het woord, een klik ernaast, Escape of scrollen. Het woord krijgt `aria-expanded`, en het kaartje `role="dialog"` en de focus. Met Cmd- of Ctrl-klik open je de recordpagina zelf. Begrippen staan niet in de bibliotheek (`HIDDEN_TYPES` in `vw-library.vue`).

## Plugins
Een plugin uit de content-repo ([type `plugin`](content-repo.md#plugins)) is één component in `src/plugins/`, geregistreerd onder zijn `id` in `src/plugins/index.js`. Een component krijgt twee props: `argument` (de tekst na de `#`, of `null`) en `fullscreen`. `components/el-plugin.vue` zet hem in de tekst, in een kader met een knop die hem schermvullend toont, en `vw-plugin.vue` toont hem schermvullend. Een plugin zonder component toont zijn titel en beschrijving met de melding dat er nog aan gewerkt wordt.

Een nieuwe plugin: maak `src/plugins/el-plugin-<id>.vue` en voeg één regel toe aan `PLUGINS` in `src/plugins/index.js`.

De IIIF-plugin (`el-plugin-iiif.vue`) gebruikt [OpenSeadragon](https://openseadragon.github.io/) en laadt de tegels live van de IIIF-server (`services/iiif.js`). Dat is een bewuste uitzondering op "alles lokaal": lukt het laden niet, dan toont de plugin een melding met een link naar de bron.

De plugin `deepdive` is de ontdekmodus zelf (`src/explorer/el-explorer.vue`), zodat die ook in een hoofdstuk kan staan; zie [ontdekmodus.md](ontdekmodus.md).

## Live bronnen
Elke live bron is één module in `services/`. Valt hij uit, dan werkt de rest van de site door. Er zijn nu drie live bronnen: `services/iiif.js`, voor de [IIIF-plugin](#plugins), en de Allmaps-tegels van de historische [kaart](#kaart) en de satelliettegels van Esri. Die laatste twee staan als URL in `el-map.vue`, omdat MapLibre ze zelf ophaalt.
