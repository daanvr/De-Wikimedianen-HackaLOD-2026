import "regenerator-runtime/runtime";
import '@fontsource-variable/newsreader';
import '@fontsource-variable/newsreader/wght-italic.css';
import '@fontsource/old-standard-tt/400.css';
import '@fontsource/old-standard-tt/400-italic.css';
import '@fontsource/old-standard-tt/700.css';
import 'maplibre-gl/dist/maplibre-gl.css';
import { createPinia } from 'pinia';
import { createApp } from 'vue';
import App from '@/app.vue';
import { router } from '@/router.js';

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount('#app');
