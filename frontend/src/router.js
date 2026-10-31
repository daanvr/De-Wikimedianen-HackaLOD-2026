import { createRouter, createWebHistory } from 'vue-router';
import VwChapter from '@/views/vw-chapter.vue';
import VwChapters from '@/views/vw-chapters.vue';
import VwGame from '@/views/vw-game.vue';
import VwHome from '@/views/vw-home.vue';
import VwLibrary from '@/views/vw-library.vue';
import VwMap from '@/views/vw-map.vue';
import VwPage from '@/views/vw-page.vue';
import VwPlugin from '@/views/vw-plugin.vue';
import VwRecord from '@/views/vw-record.vue';

export const router = createRouter({
    history : createWebHistory(),
    routes : [
        {
            path : '/',
            name : 'home',
            component : VwHome
        },
        {
            path : '/chapters',
            name : 'chapters',
            component : VwChapters
        },
        {
            path : '/chapters/:id',
            name : 'chapter',
            component : VwChapter
        },
        {
            path : '/records/:id',
            name : 'record',
            component : VwRecord
        },
        {
            path : '/pages/:id',
            name : 'page',
            component : VwPage
        },
        {
            path : '/plugins/:id',
            name : 'plugin',
            component : VwPlugin
        },
        {
            path : '/library',
            name : 'library',
            component : VwLibrary
        },
        {
            path : '/map',
            name : 'map',
            component : VwMap
        },
        {
            path : '/spel',
            name : 'game',
            component : VwGame
        },
        {
            path : '/:pathMatch(.*)*',
            redirect : '/'
        }
    ],
    scrollBehavior() {
        return {
            top : 0
        };
    }
});
