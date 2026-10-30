# Frontend
De frontend is een statische Vue 3-app in `frontend/`. Hij leest de frontend data en toont het verhaal, de records en de kaart.

Aanvullende instructies over de frontend komen nog in [CLAUDE.md](../CLAUDE.md) onder "Frontend: aanvullende instructies".

## Stack
We beginnen vanaf Hays template [vue3-pinia](https://github.com/hay/templates/tree/master/vue3-pinia). Dat is hoe we graag werken.

| Wat | Keuze |
|---|---|
| Framework | Vue 3, Composition API met `<script setup>` |
| Build | Vite, met het alias `@` voor `src/` en `vite-plugin-remove-console` |
| Taal | JavaScript (ES modules), geen TypeScript |
| Store | Pinia, één store in `src/store.js` |
| Styling | SCSS met `sass`, en Hays SCSS-bibliotheek `valenski` |
| Routing | `vue-router` met hash-history (`#/record/anna-weber`), zodat de server geen extra regels nodig heeft |
| Kaart | Leaflet, net als in het eerdere kaartprototype |

Codeconventies (naamgeving `el-*` en `vw-*`, `v-bind:` en `v-on:` voluit, `ref()` en `computed()`, attribuut-hooks voor CSS) staan in [CLAUDE.md](../CLAUDE.md).

## Structuur
```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── fixtures/
│   └── siboga.example.json   ← voorbeeld-frontend data
├── public/
│   └── data/                 ← frontend data uit de pipeline (niet in git)
└── src/
    ├── main.js               ← maakt de app, Pinia en de router
    ├── app.vue               ← laadt de data, toont de huidige view
    ├── store.js              ← Pinia-store met de frontend data
    ├── router.js
    ├── components/           ← el-*.vue
    ├── views/                ← vw-*.vue
    ├── services/
    │   ├── data.js           ← siboga.json laden en controleren
    │   └── live/             ← één module per live bron
    └── scss/
        ├── style.scss        ← @use van alles hieronder
        ├── _values.scss      ← design tokens als CSS custom properties
        ├── _fonts.scss
        ├── _base.scss
        └── _app.scss
```

Let op: in de template heet het bestand `App.vue`, maar `main.js` importeert `@/app.vue`. Op macOS werkt dat, op Linux (de server) niet. Gebruik overal `app.vue`.

## Data en store
- `services/data.js` haalt `data/siboga.json` op (relatief aan `import.meta.env.BASE_URL`) en controleert `meta.schemaVersion`.
- De Pinia-store bewaart de chapters en records en biedt getters als `chapterById`, `recordById` en `recordsForChapter`.
- `app.vue` laadt de data één keer bij het opstarten en toont een laadscherm tot die er is.
- De store wordt in `app.vue` opgehaald en met `provide('store', store)` doorgegeven. Componenten doen `inject('store')` in plaats van zelf `useStore()` te importeren. Zo staat het in de conventies.
- Zonder pipeline: kopieer `fixtures/siboga.example.json` naar `public/data/siboga.json`.

## Views en componenten
Een eerste aanzet; dit wordt per taak uitgewerkt.

| Bestand | Wat |
|---|---|
| `vw-home.vue` | Startpagina met de hoofdstukken |
| `vw-chapter.vue` | Eén hoofdstuk: de tekst, de records erin, de plek op de kaart |
| `vw-record.vue` | Eén record: titel, beschrijving, afbeelding, bronnen, de hoofdstukken waarin het voorkomt |
| `vw-map.vue` | De kaart met de route en de plekken |
| `el-chapter-text.vue` | Toont `bodyHtml` en vangt klikken op links met `data-record` af |
| `el-record-card.vue` | Een record als kaartje |
| `el-map.vue` | Leaflet-kaart, gevoed via props |
| `el-image.vue` | Afbeelding met bronvermelding en licentie |

Views halen data uit de store. Componenten krijgen hun data zoveel mogelijk via props, zodat ze los te gebruiken en te testen zijn.

## Live bronnen
Live bronnen haalt de browser zelf op terwijl de site draait. De eerste zijn de kaarttegels voor de interactieve kaart. Er komen er later meer bij.
- Elke live bron is één module in `services/live/`. Componenten halen nooit zelf iets van buiten op.
- Een live bron mag uitvallen. De site blijft dan werken, alleen zonder dat onderdeel.
- Wat vooraf opgehaald kan worden, hoort in de pipeline en niet hier.

## Styling
- Design tokens (kleuren, lettertypes, afstanden) als CSS custom properties in `scss/_values.scss`. Alleen breakpoints zijn SCSS-variabelen.
- Elk component heeft `<style lang="scss" scoped>` met als rootklasse de naam van het component (`.el-record-card`).
- Toestanden via attributen: `v-bind:is-current="isCurrent ? '' : null"` en in SCSS `&[is-current]`.

## Bouwen
`npm run build` maakt `frontend/dist/`. Dat is een map met statische bestanden die naar de server kan. Zie [ontwikkelen.md](ontwikkelen.md).
