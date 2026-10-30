<script setup>
    import { computed, inject, onBeforeUnmount, ref, watch } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElLightbox from '@/components/el-lightbox.vue';
    import ElZoomedImage from '@/components/el-zoomed-image.vue';

    const t = inject('t');

    const props = defineProps({
        // [{ src, alt, caption }], caption as HTML or null
        images : {
            type : Array,
            required : true
        }
    });

    const current = ref(0);
    const isFullscreen = ref(false);
    const track = ref(null);
    const image = computed(() => props.images[current.value] ?? props.images[0]);
    const hasNavigation = computed(() => props.images.length > 1);

    function go(index) {
        const count = props.images.length;

        current.value = (index + count) % count;
        // Scrolls only the track, not the sheet around it
        track.value?.scrollTo({
            left : current.value * track.value.clientWidth,
            behavior : 'smooth'
        });
    }

    function onKeydown(event) {
        if (event.key === 'ArrowLeft') {
            go(current.value - 1);
        } else if (event.key === 'ArrowRight') {
            go(current.value + 1);
        }
    }

    // Swiping scrolls the track; the image that snaps into place is the current one
    function onScroll() {
        if (track.value?.clientWidth) {
            current.value = Math.round(track.value.scrollLeft / track.value.clientWidth);
        }
    }

    watch(isFullscreen, (open) => {
        if (open) {
            window.addEventListener('keydown', onKeydown);
        } else {
            window.removeEventListener('keydown', onKeydown);
        }
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKeydown);
    });
</script>

<template>
    <figure class="el-gallery">
        <div class="frame">
            <div
                ref="track"
                class="track"
                v-on:scroll.passive="onScroll">
                <div
                    v-for="(item, index) in images"
                    v-bind:key="index"
                    class="slide">
                    <img
                        class="image"
                        v-bind:src="item.src"
                        v-bind:alt="item.alt"
                        loading="lazy">
                </div>
            </div>

            <template v-if="hasNavigation">
                <button
                    type="button"
                    class="nav nav--previous"
                    v-bind:aria-label="t('gallery_previous')"
                    v-on:click="go(current - 1)">
                    <el-icon
                        name="arrowLeft"
                        v-bind:size="20" />
                </button>

                <button
                    type="button"
                    class="nav nav--next"
                    v-bind:aria-label="t('gallery_next')"
                    v-on:click="go(current + 1)">
                    <el-icon
                        name="arrowRight"
                        v-bind:size="20" />
                </button>
            </template>

            <button
                type="button"
                class="fullscreen"
                v-bind:aria-label="t('image_fullscreen')"
                v-on:click="isFullscreen = true">
                <el-icon
                    name="fullscreen"
                    v-bind:size="20" />
            </button>
        </div>

        <figcaption class="caption">
            <span
                v-if="hasNavigation"
                class="counter">{{ current + 1 }} / {{ images.length }}</span>
            <span
                v-if="image.caption"
                v-html="image.caption"></span>
        </figcaption>

        <el-lightbox
            v-if="isFullscreen"
            close-on-click
            v-on:close="isFullscreen = false">
            <el-zoomed-image
                v-bind:src="image.src"
                v-bind:alt="image.alt"
                v-bind:caption="image.caption" />

            <template v-if="hasNavigation">
                <button
                    type="button"
                    class="nav nav--previous"
                    is-fullscreen
                    v-bind:aria-label="t('gallery_previous')"
                    v-on:click.stop="go(current - 1)">
                    <el-icon name="arrowLeft" />
                </button>

                <button
                    type="button"
                    class="nav nav--next"
                    is-fullscreen
                    v-bind:aria-label="t('gallery_next')"
                    v-on:click.stop="go(current + 1)">
                    <el-icon name="arrowRight" />
                </button>
            </template>
        </el-lightbox>
    </figure>
</template>

<style lang="scss" scoped>
    .el-gallery {
        margin: 1.6rem 0;
        padding: 0.8rem;
        border: 1px solid var(--c-frame);
        background: var(--c-plate);
    }

    .frame {
        position: relative;
    }

    .track {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        scrollbar-width: none;
        background: #EAE3D3;

        &::-webkit-scrollbar {
            display: none;
        }
    }

    .slide {
        flex: 0 0 100%;
        height: 36rem;
        display: flex;
        align-items: center;
        justify-content: center;
        scroll-snap-align: start;
    }

    .image {
        display: block;
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .nav,
    .fullscreen {
        position: absolute;
        width: 4.4rem;
        height: 4.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(251, 248, 241, 0.92);
        color: var(--c-marine);
        border: 1px solid var(--c-marine);
        border-radius: 4px;
    }

    .nav {
        top: 50%;
        transform: translateY(-50%);

        &[is-fullscreen] {
            width: 4.8rem;
            height: 4.8rem;
            background: var(--c-paper);
            border: 0;
            z-index: 1;
        }
    }

    .nav--previous {
        left: 0.8rem;

        &[is-fullscreen] {
            left: 1.6rem;
        }
    }

    .nav--next {
        right: 0.8rem;

        &[is-fullscreen] {
            right: 1.6rem;
        }
    }

    .fullscreen {
        right: 0.8rem;
        bottom: 0.8rem;
    }

    .caption {
        margin-top: 0.8rem;
        font-size: 1.4rem;
        line-height: 1.4;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .counter {
        margin-right: 0.8rem;
        font-family: var(--font-header);
        font-style: normal;
        letter-spacing: 0.1em;
        color: var(--c-terracotta);
    }
</style>
