<script setup>
    import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import OpenSeadragon from 'openseadragon';
    import ElIcon from '@/components/el-icon.vue';
    import { iiifTileSources } from '@/services/iiif.js';

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
    const page = ref(0);
    const pageCount = ref(0);
    const hasPages = computed(() => pageCount.value > 1);

    let viewer = null;
    // Counts the opens, so a manifest that arrives late does not open over a newer one
    let openCount = 0;

    function close() {
        openCount += 1;

        if (viewer) {
            viewer.destroy();
            viewer = null;
        }
    }

    function goToPage(index) {
        if (!viewer || !hasPages.value) {
            return;
        }

        viewer.goToPage((index + pageCount.value) % pageCount.value);
    }

    async function open() {
        close();
        hasError.value = !props.argument;
        page.value = 0;
        pageCount.value = 0;

        if (!props.argument) {
            return;
        }

        const current = openCount;
        let tileSources = null;

        try {
            tileSources = await iiifTileSources(props.argument);
        } catch (error) {
            console.warn(error.message);
            hasError.value = true;
            return;
        }

        if (current !== openCount || !container.value) {
            return;
        }

        pageCount.value = tileSources.length;
        viewer = OpenSeadragon({
            element : container.value,
            tileSources,
            // One page at a time; the buttons below go through them
            sequenceMode : tileSources.length > 1,
            showNavigationControl : false,
            showSequenceControl : false,
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

        viewer.addHandler('open', () => {
            hasError.value = false;
        });

        viewer.addHandler('page', (event) => {
            page.value = event.page;
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
            v-if="hasPages && !hasError"
            class="pager"
            v-on:click.stop>
            <button
                type="button"
                class="pager__button"
                v-bind:aria-label="t('gallery_previous')"
                v-on:click="goToPage(page - 1)">
                <el-icon
                    name="arrowLeft"
                    v-bind:size="18" />
            </button>

            <span class="pager__count">{{ page + 1 }} / {{ pageCount }}</span>

            <button
                type="button"
                class="pager__button"
                v-bind:aria-label="t('gallery_next')"
                v-on:click="goToPage(page + 1)">
                <el-icon
                    name="arrowRight"
                    v-bind:size="18" />
            </button>
        </div>

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

    .pager {
        position: absolute;
        left: 50%;
        bottom: 0.8rem;
        transform: translateX(-50%);
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.2rem;
        background: rgba(251, 248, 241, 0.92);
        border: 1px solid var(--c-marine);
        border-radius: 4px;
        z-index: 1;

        [is-fullscreen] > & {
            bottom: 2.4rem;
        }
    }

    .pager__button {
        width: 4rem;
        height: 4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--c-marine);
    }

    .pager__count {
        min-width: 5rem;
        font-family: var(--font-header);
        font-size: 1.4rem;
        letter-spacing: 0.1em;
        text-align: center;
        color: var(--c-ink);
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
