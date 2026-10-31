<script setup>
    import { defineAsyncComponent, inject, onMounted } from 'vue';

    // The explore mode is the explorer itself, full screen; it has its own map on top of the main one
    const ElExplorer = defineAsyncComponent(() => import('@/explorer/el-explorer.vue'));

    const store = inject('store');

    onMounted(() => {
        const settings = {
            mode : 'explore',
            sheet : 'none',
            boat : null
        };

        if (store.map.mode !== 'explore') {
            settings.focus = null;
        }

        store.setMap(settings);
    });
</script>

<template>
    <div class="vw-map">
        <el-explorer v-bind:fullscreen="true" />
    </div>
</template>

<style lang="scss" scoped>
    // Below the menu button of the app (z-index 50)
    .vw-map {
        position: absolute;
        inset: 0;
        z-index: 30;
    }
</style>
