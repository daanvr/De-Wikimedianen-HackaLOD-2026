import { defineStore } from 'pinia';
import { markRaw } from 'vue';
import { loadFrontendData } from '@/services/data.js';
import { loadMapLayers } from '@/services/map-layers.js';
import { DEFAULT_MESSAGES } from '@/services/messages.js';

// Off Surabaya, where the Siboga set out on 7 March 1899. Used when a
// chapter's location has no coordinates (yet).
export const EXPEDITION_START = {
    lon : 112.82,
    lat : -7.1
};

const READ_KEY = 'siboga-read-chapters';

function loadReadChapters() {
    try {
        return JSON.parse(localStorage.getItem(READ_KEY)) || [];
    } catch (error) {
        return [];
    }
}

export const useStore = defineStore('data', {
    state : () => {
        return {
            data : null,
            error : null,
            // Where the library was left, so the back button returns to the same spot
            library : {
                query : '',
                scrollTop : 0
            },
            loading : true,
            map : {
                mode : 'home',
                chapterId : null,
                focus : null,
                travelling : false
            },
            mapLayers : null,
            readChapters : loadReadChapters()
        };
    },

    getters : {
        chapters : (state) => state.data?.chapters ?? [],

        contentTypes() {
            const types = new Set(this.recordList.map((record) => record.contentType || 'other'));

            return [...types].sort();
        },

        messages : (state) => {
            return {
                ...DEFAULT_MESSAGES,
                ...(state.data?.messages ?? {})
            };
        },

        meta : (state) => state.data?.meta ?? null,

        explorePlugins() {
            return Object.values(this.plugins).filter((plugin) => plugin.showInExplore);
        },

        pages : (state) => state.data?.pages ?? {},

        plugins : (state) => state.data?.plugins ?? {},

        recordList : (state) => Object.values(state.data?.records ?? {}),

        records : (state) => state.data?.records ?? {}
    },

    actions : {
        chapterById(id) {
            return this.chapters.find((chapter) => chapter.id === id) ?? null;
        },

        chapterPosition(chapter) {
            const record = chapter?.location ? this.itemByRef(chapter.location) : null;

            if (record?.coordinates) {
                return {
                    lon : record.coordinates.lon,
                    lat : record.coordinates.lat
                };
            }

            return EXPEDITION_START;
        },

        itemByRef(ref) {
            if (!ref) {
                return null;
            }

            const [kind, id] = ref.replace(/^\//, '').split('/');

            if (kind === 'records') {
                return this.records[id] ?? null;
            }

            if (kind === 'chapters') {
                return this.chapterById(id);
            }

            if (kind === 'pages') {
                return this.pages[id] ?? null;
            }

            if (kind === 'plugins') {
                return this.plugins[id] ?? null;
            }

            return null;
        },

        kindForHref(href) {
            const [kind, id] = href.replace(/^\//, '').split('/');

            if (kind === 'records') {
                return this.records[id]?.contentType ?? 'record';
            }

            if (kind === 'plugins') {
                return 'plugin';
            }

            return kind === 'chapters' ? 'chapter' : 'internal';
        },

        async load() {
            this.loading = true;

            try {
                const [data, mapLayers] = await Promise.all([
                    loadFrontendData(),
                    loadMapLayers()
                ]);

                this.data = data;
                // Large GeoJSON goes to the map worker as is; Vue proxies cannot be cloned
                this.mapLayers = markRaw(mapLayers);
            } catch (error) {
                console.error(error);
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        },

        markChapterRead(id) {
            if (this.readChapters.includes(id)) {
                return;
            }

            this.readChapters = [...this.readChapters, id];

            try {
                localStorage.setItem(READ_KEY, JSON.stringify(this.readChapters));
            } catch (error) {
                console.warn('Could not store read chapters');
            }
        },

        setMap(settings) {
            this.map = {
                ...this.map,
                ...settings
            };
        },

        t(key) {
            return this.messages[key] ?? key;
        }
    }
});
