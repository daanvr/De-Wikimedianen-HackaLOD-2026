# Frontend
[Documentatie](README.md) › Frontend

De frontend is een statische Vue 3-app in `frontend/`. Hij leest de [frontend data](frontend-data.md) en toont de verhalen, de records en de interactieve kaart.

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
| Routing | `vue-router` met gewone URL's (`createWebHistory`), volgens de [URL-structuur](frontend-data.md#url-structuur) |
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
│   ├── data/                 ← frontend data uit de pipeline (niet in git)
│   └── basemap/              ← terugval-ondergrond voor de kaart (in git)
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

## Routes
De routes volgen de [URL-structuur](frontend-data.md#url-structuur). Daardoor is elke chapter en elk record een eigen pagina, met een URL die je kunt delen.

| URL | View |
|---|---|
| `/` | `vw-home.vue` |
| `/chapters/:id` | `vw-chapter.vue` |
| `/records/:id` | `vw-record.vue` |
| `/map` | `vw-map.vue` |
| alles anders | `vw-not-found.vue` |

Interne links in `bodyHtml` zijn gewone `<a href="/records/...">` met een `data-ref`. `el-text.vue` vangt klikken daarop af en geeft ze aan de router, zodat de pagina niet opnieuw laadt. Een link naar een id dat niet bestaat, toont `vw-not-found.vue`.

Voor gewone URL's moet de server elke onbekende URL naar `index.html` sturen. Dat is één regel in nginx; zie [ontwikkelen.md](ontwikkelen.md#server).

## Data en store
- `services/data.js` haalt `data/siboga.json` op (relatief aan `import.meta.env.BASE_URL`) en controleert `meta.schemaVersion`.
- De Pinia-store bewaart de chapters en records en biedt getters als `chapterById`, `recordById` en `itemByRef`.
- `app.vue` laadt de data één keer bij het opstarten en toont een laadscherm tot die er is.
- De store wordt in `app.vue` opgehaald en met `provide('store', store)` doorgegeven. Componenten doen `inject('store')` in plaats van zelf `useStore()` te importeren. Zo staat het in de conventies.
- Zonder pipeline: `just fixture` zet de voorbeelddata klaar (zie [ontwikkelen.md](ontwikkelen.md#eerste-keer)).

## Views en componenten
Een eerste aanzet; dit wordt per taak uitgewerkt.

| Bestand | Wat |
|---|---|
| `vw-home.vue` | Startpagina met de chapters |
| `vw-chapter.vue` | Eén chapter: de tekst, de records erin, de plek op de kaart, en wat ernaar verwijst |
| `vw-record.vue` | Eén record: titel, beschrijving, afbeelding, facts, bronnen, en de chapters en records die ernaar verwijzen |
| `vw-map.vue` | De interactieve kaart met de route en de plekken |
| `vw-not-found.vue` | Pagina bestaat niet |
| `el-text.vue` | Toont `bodyHtml` en geeft klikken op interne links aan de router |
| `el-record-card.vue` | Een record als kaartje |
| `el-map.vue` | Leaflet-kaart, gevoed via props |
| `el-image.vue` | Afbeelding met bronvermelding en licentie |
| `el-facts.vue` | De facts van een record als lijst |

Views halen data uit de store. Componenten krijgen hun data zoveel mogelijk via props, zodat ze los te gebruiken en te testen zijn.

## Live bronnen
Live bronnen haalt de browser zelf op terwijl de site draait. De eerste zijn de kaarttegels voor de interactieve kaart. Er komen er later meer bij.
- Elke live bron is één module in `services/live/`. Componenten halen nooit zelf iets van buiten op.
- **Elke live bron heeft een terugvaloptie.** Valt de dienst uit, dan werkt de site door zonder dat onderdeel, of met een lokale vervanging. Voor de kaart is dat een eenvoudige ondergrond van land en zee als GeoJSON in `public/basemap/` (Natural Earth, zoals in het kaartprototype). De route, de plekken en de historische kaart staan toch al lokaal.
- Wat vooraf opgehaald kan worden, hoort in de [pipeline](pipeline.md) en niet hier. Zie de [principes](architectuur.md#principes).

## Styling
- Design tokens (kleuren, lettertypes, afstanden) als CSS custom properties in `scss/_values.scss`. Alleen breakpoints zijn SCSS-variabelen.
- Elk component heeft `<style lang="scss" scoped>` met als rootklasse de naam van het component (`.el-record-card`).
- Toestanden via attributen: `v-bind:is-current="isCurrent ? '' : null"` en in SCSS `&[is-current]`.

## Bouwen
`npm run build` maakt `frontend/dist/`. Dat is een map met statische bestanden die naar de server kan, of die je lokaal kunt tonen zonder internet. Zie [ontwikkelen.md](ontwikkelen.md).

## Zie ook
- [frontend-data.md](frontend-data.md): het formaat van de data die de frontend leest
- [architectuur.md](architectuur.md): waar de frontend in het geheel past
- [ontwikkelen.md](ontwikkelen.md): de frontend draaien, bouwen en uitrollen
