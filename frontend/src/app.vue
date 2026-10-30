<script setup>
    import { computed, onBeforeUnmount, onMounted, provide, ref } from 'vue';
    import { useRoute } from 'vue-router';
    import ElMap from '@/components/el-map.vue';
    import ElMenu from '@/components/el-menu.vue';
    import { useStore } from '@/store.js';

    const store = useStore();
    const route = useRoute();
    const t = (key) => store.t(key);

    provide('store', store);
    provide('t', t);

    const viewport = ref({
        width : window.innerWidth,
        height : window.innerHeight
    });

    // The home screen has its own buttons; every other view shows the menu in the same place
    const showMenu = computed(() => !store.loading && !store.error && route.name !== 'home');

    // Keep the focus point of the map in the part of the screen not covered by panels
    const mapPadding = computed(() => {
        const { width, height } = viewport.value;
        const sheet = store.map.sheet ?? 'none';
        const padding = {
            top : 80,
            right : 24,
            bottom : 24,
            left : 24
        };

        if (sheet === 'none') {
            return padding;
        }

        if (width >= 900) {
            padding.left = 460 + 32;
            return padding;
        }

        const covered = {
            peek : 140,
            half : height * 0.52,
            full : height * 0.52
        };

        padding.bottom = Math.round(covered[sheet] ?? 0);

        return padding;
    });

    function onResize() {
        viewport.value = {
            width : window.innerWidth,
            height : window.innerHeight
        };
    }

    onMounted(() => {
        store.load();
        window.addEventListener('resize', onResize);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('resize', onResize);
    });
</script>

<template>
    <main class="app__main">
        <el-map
            v-bind:layers="store.mapLayers"
            v-bind:mode="store.map.mode"
            v-bind:focus="store.map.focus"
            v-bind:boat="store.map.boat"
            v-bind:padding="mapPadding" />

        <div
            v-if="store.loading"
            class="app__status">
            {{ t('loading') }}
        </div>

        <div
            v-else-if="store.error"
            class="app__status"
            is-error>
            <strong>{{ t('load_error') }}</strong>
            <span>{{ store.error }}</span>
        </div>

        <router-view
            v-else
            v-slot="{ Component }">
            <component v-bind:is="Component" />
        </router-view>

        <div
            v-if="showMenu"
            class="app__menu">
            <el-menu />
        </div>
    </main>
</template>

<style lang="scss" src="./scss/style.scss"></style>

<style lang="scss" scoped>
    .app__main {
        position: absolute;
        inset: 0;
        overflow: hidden;
    }

    .app__menu {
        position: absolute;
        top: 1.6rem;
        right: 1.6rem;
        z-index: 50;
    }

    .app__status {
        position: absolute;
        left: 50%;
        bottom: 4rem;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        padding: 1.2rem 2rem;
        background: var(--c-paper);
        border-radius: 8px;
        box-shadow: var(--shadow-card);
        font-style: italic;
        z-index: 40;

        &[is-error] {
            font-style: normal;
            color: var(--c-terracotta-dark);
        }
    }
</style>
