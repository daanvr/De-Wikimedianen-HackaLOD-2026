<script setup>
    import { defineAsyncComponent, inject, onMounted } from 'vue';
    import { usePreventZoom } from '@/services/no-zoom.js';

    // The game is separate from the explore mode; it has its own map on top of the main one
    const ElGame = defineAsyncComponent(() => import('@/game/el-game.vue'));

    const store = inject('store');

    // Full screen the controls must stay in view, so the browser may not zoom the page
    usePreventZoom();

    onMounted(() => {
        store.setMap({
            mode : 'explore',
            sheet : 'none',
            focus : null
        });
    });
</script>

<template>
    <div class="vw-game">
        <el-game />
    </div>
</template>

<style lang="scss" scoped>
    // Below the menu button of the app (z-index 50)
    .vw-game {
        position: absolute;
        inset: 0;
        z-index: 30;
    }
</style>
