# Frontend
[Documentatie](README.md) › Frontend

Een statische Vue 3-app in `frontend/` die de [frontend data](frontend-data.md) toont. Aanvullende instructies komen nog in [CLAUDE.md](../CLAUDE.md).

## Stack
Vertrekpunt is Hays template [vue3-pinia](https://github.com/hay/templates/tree/master/vue3-pinia): Vue 3 met `<script setup>`, Vite, Pinia, SCSS met `valenski`, JavaScript zonder TypeScript. Daarbij komen `vue-router`, een markdown-parser en Leaflet voor de kaart.

Let op: in de template heet het bestand `App.vue`, maar `main.js` importeert `@/app.vue`. Op macOS gaat dat goed, maar op Linux maakt het bestandssysteem onderscheid tussen hoofdletters en kleine letters, en vindt de import het bestand niet. Hernoem het bij het overnemen van de template daarom naar `app.vue`. Dat past ook bij de kebab-case van de andere bestanden. Gebruik in bestandsnamen en imports altijd kleine letters, zodat de build op elk systeem werkt.

## Structuur
```
frontend/src/
├── main.js
├── app.vue          ← laadt de data, toont de view
├── store.js         ← Pinia-store met de frontend data
├── router.js
├── components/      ← el-*.vue
├── views/           ← vw-*.vue
├── services/        ← data laden, live bronnen
└── scss/
```

## Routes
| URL             | View             |
| --------------- | ---------------- |
| `/`             | `vw-home.vue`    |
| `/chapters/:id` | `vw-chapter.vue` |
| `/records/:id`  | `vw-record.vue`  |
| `/map`          | `vw-map.vue`     |

Volledige paden, geen hashes. Links in de tekst die met `/` beginnen, gaan via de router. Op de server is daarvoor één regel nginx nodig ([ontwikkelen.md](ontwikkelen.md#server)).

## Data en store
- `app.vue` laadt `data/siboga.json` één keer en controleert `meta.schemaVersion`.
- De store wordt met `provide('store', store)` doorgegeven; componenten doen `inject('store')`.
- Views halen data uit de store, componenten krijgen hun data via props.

## Live bronnen
Elke live bron, zoals de kaarttegels, is één module in `services/`. Valt hij uit, dan werkt de rest van de site door. Welke live bronnen er naast de kaarttegels komen, is nog niet bepaald.
