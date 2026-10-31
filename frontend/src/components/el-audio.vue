<script setup>
    import { computed, inject } from 'vue';
    import { mediaUrl } from '@/services/data.js';

    const t = inject('t');

    const props = defineProps({
        audio : {
            type : Object,
            required : true
        }
    });

    const src = computed(() => mediaUrl(props.audio.src));
</script>

<template>
    <figure class="el-audio">
        <audio
            class="player"
            controls
            preload="metadata">
            <source
                v-bind:src="src"
                v-bind:type="audio.mimeType" />
        </audio>

        <figcaption class="caption">
            {{ audio.credit }} ·
            <a
                v-if="audio.licenseUrl"
                v-bind:href="audio.licenseUrl"
                target="_blank"
                rel="noopener">{{ audio.license }}</a>
            <template v-else>{{ audio.license }}</template>
            <template v-if="audio.sourceUrl">
                ·
                <a
                    v-bind:href="audio.sourceUrl"
                    target="_blank"
                    rel="noopener">{{ t('image_source') }}</a>
            </template>
        </figcaption>
    </figure>
</template>

<style lang="scss" scoped>
    .el-audio {
        margin: 0 0 1.8rem;
        padding: 0.8rem;
        border: 1px solid var(--c-frame);
        background: var(--c-plate);
    }

    .player {
        display: block;
        width: 100%;
    }

    .caption {
        margin-top: 0.8rem;
        font-size: 1.4rem;
        line-height: 1.4;
        font-style: italic;
        color: var(--c-ink-soft);
    }
</style>
