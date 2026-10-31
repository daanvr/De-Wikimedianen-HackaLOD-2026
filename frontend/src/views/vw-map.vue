<script setup>
    import { inject, onMounted } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElLayerButton from '@/components/el-layer-button.vue';

    const store = inject('store');

    function setLayer(layer) {
        store.setMap({
            base : layer
        });
    }

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
        <div
            v-if="store.explorePlugins.length"
            class="top">
            <router-link
                v-for="plugin in store.explorePlugins"
                v-bind:key="plugin.id"
                class="dataset"
                v-bind:to="`/plugins/${plugin.id}`">
                <el-icon
                    class="dataset__icon"
                    name="explore"
                    v-bind:size="20" />
                <span class="dataset__text">
                    <span class="dataset__label">{{ plugin.title }}</span>
                    <span
                        v-if="plugin.description"
                        class="dataset__description">{{ plugin.description }}</span>
                </span>
            </router-link>
        </div>

        <el-layer-button
            class="layers"
            v-bind:layer="store.map.base"
            v-on:change="setLayer($event)" />
    </div>
</template>

<style lang="scss" scoped>
    @use "../../node_modules/valenski/mixins";

    .vw-map {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    .layers {
        position: absolute;
        right: 1.6rem;
        bottom: 2.4rem;
        z-index: 30;
    }

    .top {
        position: absolute;
        top: 1.6rem;
        left: 1.6rem;
        // Leaves room for the menu button (see app.vue)
        right: 7.4rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        z-index: 30;

        @include mixins.respond-from(900px) {
            left: auto;
            width: 34.2rem;
        }
    }

    .dataset {
        pointer-events: auto;
        min-height: 4.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.8rem 1.2rem;
        background: var(--c-paper);
        color: var(--c-ink);
        text-decoration: none;
        border: 1px solid var(--c-marine);
        border-radius: 4px;
        box-shadow: inset 0 0 0 3px var(--c-paper), inset 0 0 0 4px #D8CFBB, var(--shadow-float);

        &:hover {
            color: var(--c-ink);
        }
    }

    .dataset__icon {
        color: var(--c-terracotta);
    }

    .dataset__label {
        font-family: var(--font-header);
        font-size: 1.7rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .dataset__text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
    }

    .dataset__description {
        font-size: 1.4rem;
        line-height: 1.3;
        font-style: italic;
        color: var(--c-ink-soft);
    }
</style>
