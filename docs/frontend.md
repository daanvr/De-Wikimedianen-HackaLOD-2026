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
│   └── map/             ← kaartlagen: diepte, land, route, stations (wel in git)
├── scripts/
│   └── prepare_map.py   ← maakt public/map/ uit de bronbestanden
└── src/
    ├── main.js
    ├── app.vue          ← laadt de data, houdt de kaart vast, toont de view
    ├── store.js         ← Pinia-store met de frontend data en de kaartstand
    ├── router.js
    ├── components/      ← el-*.vue
    ├── views/           ← vw-*.vue
    ├── services/        ← data laden, kaartlagen, markdown, standaardteksten
    └── scss/
```

Herkomst en licenties van de kaartlagen staan in [frontend/README.md](../frontend/README.md).

## Routes
| URL             | View              | Wat                                                          |
| --------------- | ----------------- | ------------------------------------------------------------ |
| `/`             | `vw-home.vue`     | Welkom (`pages/welcome`), knop naar het eerste hoofdstuk     |
| `/chapters`     | `vw-chapters.vue` | Lijst van hoofdstukken, met gelezen en huidig                |
| `/chapters/:id` | `vw-chapter.vue`  | Verhaalmodus: kaart met boot en tekstvel                     |
| `/records/:id`  | `vw-record.vue`   | Record met plaatje, velden, bron en "Genoemd in"             |
| `/pages/:id`    | `vw-page.vue`     | Vaste pagina, zoals `/pages/about`                           |
| `/library`      | `vw-library.vue`  | Bibliotheek: zoeken en filteren op contenttype en stations   |
| `/map`          | `vw-map.vue`      | Ontdekmodus: alle stations; `?station=117` opent een station |

Volledige paden, geen hashes. Links in de tekst die met `/` beginnen, gaan via de router. Op de server is daarvoor één regel nginx nodig ([ontwikkelen.md](ontwikkelen.md#server)).

## Kaart
Eén kaart (`el-map.vue`) blijft staan onder alle views, zodat de boot van hoofdstuk naar hoofdstuk kan varen. Views zetten de kaartstand in de store (`store.setMap()`); `app.vue` geeft die als props door. De kaart gebruikt geen kaarttegels: de stijl is eigen werk, met vlakke dieptebanden uit `public/map/`. Alles staat dus lokaal. Zeenamen zijn HTML-labels, zodat er geen glyph-server nodig is.

De boot staat op de coördinaten van het record in `location` van een hoofdstuk. Heeft dat record geen coördinaten, dan ligt de boot bij Soerabaja, waar de reis begon.

## Data en store
- `app.vue` laadt `data/siboga.json` één keer en controleert `meta.schemaVersion`.
- De store wordt met `provide('store', store)` doorgegeven; componenten doen `inject('store')`.
- Views halen data uit de store, componenten krijgen hun data via props.

## Teksten (i18n)
Geen losse tekst in de HTML. Alle tekst die de site zelf toont, zoals knoppen, menu's en de namen van velden, komt uit `messages` in `siboga.json`, via één functie (bijvoorbeeld `t('start_bn')`) die via `provide`/`inject` beschikbaar is. Zolang een bericht nog niet in de content-repo staat, komt het uit de standaardteksten in `src/services/messages.js`; berichten uit de content-repo gaan altijd voor. Staat een sleutel ook daar niet, dan toont de functie de sleutel. De berichten staan in de content-repo ([content-repo.md](content-repo.md#frontmatter)).

## Velden van een record
Een record heeft een lijst `fields`, al in de goede volgorde voor zijn contenttype. De frontend toont ze zoals ze komen: de naam via `t('field_' + key)`, en de waarden; bij `type: "date"` opgemaakt als datum.

## Live bronnen
Elke live bron, zoals de kaarttegels, is één module in `services/`. Valt hij uit, dan werkt de rest van de site door. Welke live bronnen er naast de kaarttegels komen, is nog niet bepaald.
