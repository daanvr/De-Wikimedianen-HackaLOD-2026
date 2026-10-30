<script setup>
    import { computed, inject, ref } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import { mediaUrl } from '@/services/data.js';

    const t = inject('t');

    const props = defineProps({
        image : {
            type : Object,
            required : true
        },
        alt : {
            type : String,
            default : ''
        }
    });

    const isFullscreen = ref(false);
    const src = computed(() => mediaUrl(props.image.src));
</script>

<template>
    <figure class="el-figure">
        <div class="frame">
            <img
                class="image"
                v-bind:src="src"
                v-bind:alt="alt"
                loading="lazy">

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
            {{ image.credit }} ·
            <a
                v-if="image.licenseUrl"
                v-bind:href="image.licenseUrl"
                target="_blank"
                rel="noopener">{{ image.license }}</a>
            <template v-else>{{ image.license }}</template>
            <template v-if="image.sourceUrl">
                ·
                <a
                    v-bind:href="image.sourceUrl"
                    target="_blank"
                    rel="noopener">{{ t('image_source') }}</a>
            </template>
        </figcaption>

        <div
            v-if="isFullscreen"
            class="lightbox"
            v-on:click="isFullscreen = false">
            <img
                v-bind:src="src"
                v-bind:alt="alt">
            <button
                type="button"
                class="lightbox__close"
                v-bind:aria-label="t('close')"
                v-on:click="isFullscreen = false">
                <el-icon name="close" />
            </button>
        </div>
    </figure>
</template>

<style lang="scss" scoped>
    .el-figure {
        margin: 0 0 1.8rem;
        padding: 0.8rem;
        border: 1px solid var(--c-frame);
        background: var(--c-plate);
    }

    .frame {
        position: relative;
        display: flex;
        justify-content: center;
        background: #EAE3D3;
    }

    .image {
        display: block;
        max-width: 100%;
        max-height: 36rem;
        object-fit: contain;
    }

    .fullscreen {
        position: absolute;
        right: 0.8rem;
        bottom: 0.8rem;
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

    .caption {
        margin-top: 0.8rem;
        font-size: 1.4rem;
        line-height: 1.4;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .lightbox {
        position: fixed;
        inset: 0;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(10, 20, 32, 0.92);

        img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
    }

    .lightbox__close {
        position: absolute;
        top: 1.6rem;
        right: 1.6rem;
        width: 4.8rem;
        height: 4.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--c-paper);
        color: var(--c-marine);
        border-radius: 4px;
    }
</style>
