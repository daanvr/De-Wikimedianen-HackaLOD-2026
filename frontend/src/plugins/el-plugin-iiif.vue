<script setup>
    import { inject, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import OpenSeadragon from 'openseadragon';
    import { iiifTileSource } from '@/services/iiif.js';

    const t = inject('t');

    const props = defineProps({
        argument : {
            type : String,
            default : null
        },
        fullscreen : {
            type : Boolean,
            default : false
        }
    });

    const container = ref(null);
    const hasError = ref(false);

    let viewer = null;

    function close() {
        if (viewer) {
            viewer.destroy();
            viewer = null;
        }
    }

    function open() {
        close();
        hasError.value = !props.argument;

        if (!props.argument) {
            return;
        }

        viewer = OpenSeadragon({
            element : container.value,
            tileSources : iiifTileSource(props.argument),
            showNavigationControl : false,
            crossOriginPolicy : 'Anonymous',
            visibilityRatio : 1,
            gestureSettingsMouse : {
                // Inline, the mouse wheel scrolls the text; only fullscreen it zooms
                scrollToZoom : props.fullscreen
            }
        });

        viewer.addHandler('open-failed', () => {
            hasError.value = true;
        });
    }

    watch(() => props.argument, open);

    onMounted(open);

    onBeforeUnmount(close);
</script>

<template>
    <div
        class="el-plugin-iiif"
        v-bind:is-fullscreen="fullscreen ? '' : null">
        <div
            ref="container"
            class="viewer"></div>

        <div
            v-if="hasError"
            class="error">
            <p>{{ t('plugin_unavailable') }}</p>
            <a
                v-if="argument"
                v-bind:href="argument"
                target="_blank"
                rel="noopener">{{ t('plugin_source') }}</a>
        </div>
    </div>
</template>

<style lang="scss" scoped>
    .el-plugin-iiif {
        position: relative;
        height: 36rem;
        background: #EAE3D3;

        &[is-fullscreen] {
            height: 100%;
            background: transparent;
        }
    }

    .viewer {
        width: 100%;
        height: 100%;
    }

    .error {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        padding: 2rem;
        text-align: center;
        font-style: italic;
        color: var(--c-ink-soft);

        p {
            margin: 0;
        }

        [is-fullscreen] & {
            color: var(--c-paper);
        }

        [is-fullscreen] & a {
            color: var(--c-terracotta-light);
        }
    }
</style>
