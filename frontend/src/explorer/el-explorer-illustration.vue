<script setup>
    import { onBeforeUnmount, onMounted } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElExplorerLikeness from './el-explorer-likeness.vue';

    // The window that opens from an illustration: the photo large, and how close it is to the specimen
    const emit = defineEmits(['close']);

    defineProps({
        illustration : {
            type : Object,
            required : true
        },
        specimenName : {
            type : String,
            required : true
        }
    });

    function onKey(event) {
        if (event.key === 'Escape') {
            emit('close');
        }
    }

    onMounted(() => window.addEventListener('keydown', onKey));

    onBeforeUnmount(() => window.removeEventListener('keydown', onKey));
</script>

<template>
    <div
        class="el-explorer-illustration"
        role="dialog"
        aria-modal="true"
        v-bind:aria-label="illustration.title"
        v-on:click.self="emit('close')">
        <article class="window">
            <div class="visual">
                <img
                    class="visual__image"
                    v-bind:src="illustration.src"
                    v-bind:alt="illustration.depicted">
                <el-explorer-likeness
                    class="visual__likeness"
                    large
                    v-bind:illustration="illustration" />
                <button
                    type="button"
                    class="close"
                    aria-label="Sluiten"
                    v-on:click="emit('close')">
                    <el-icon
                        name="close"
                        v-bind:size="20" />
                </button>
            </div>

            <div class="body">
                <p class="kicker">Bij {{ specimenName }}</p>
                <h3 class="title">{{ illustration.title }}</h3>
                <p class="depicted">Op de foto: <em>{{ illustration.depicted }}</em></p>
                <p class="text">{{ illustration.explanation }}</p>
                <p
                    v-if="illustration.note"
                    class="note">{{ illustration.note }}</p>

                <details
                    v-if="illustration.reasoning"
                    class="reasoning">
                    <summary>Hoe we deze foto gekozen hebben</summary>
                    <p>{{ illustration.reasoning }}</p>
                </details>

                <p class="credit">
                    Foto: {{ illustration.maker }}<template v-if="illustration.place">, {{ illustration.place }}</template><template v-if="illustration.date">, {{ illustration.date }}</template> ·
                    <a
                        target="_blank"
                        rel="noopener"
                        v-bind:href="illustration.licenseUrl">{{ illustration.license }}</a> ·
                    <a
                        target="_blank"
                        rel="noopener"
                        v-bind:href="illustration.sourceUrl">bekijk op {{ illustration.source }}</a>
                </p>
            </div>
        </article>
    </div>
</template>

<style lang="scss" scoped>
    .el-explorer-illustration {
        position: fixed;
        inset: 0;
        z-index: 50;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.6rem;
        background: var(--c-scrim);
        animation: fade 0.25s ease backwards;
    }

    .window {
        width: min(72rem, 100%);
        max-height: 100%;
        display: flex;
        flex-direction: column;
        border-radius: 12px;
        background: var(--c-paper);
        box-shadow: var(--shadow-card);
        overflow-y: auto;
        overscroll-behavior: contain;
    }

    .visual {
        position: relative;
        flex: none;
        background: #0B1A28;
    }

    .visual__image {
        display: block;
        width: 100%;
        max-height: 60vh;
        object-fit: contain;
    }

    .visual__likeness {
        position: absolute;
        left: 1.2rem;
        bottom: 1.2rem;
    }

    .close {
        position: absolute;
        top: 1.2rem;
        right: 1.2rem;
        width: 4.4rem;
        height: 4.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 0;
        border-radius: 50%;
        background: var(--c-paper);
        color: var(--c-marine);
        box-shadow: var(--shadow-float);
        cursor: pointer;
    }

    .body {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1.8rem 2rem 2.2rem;
    }

    .kicker {
        margin: 0;
        font-family: var(--font-header);
        font-size: var(--fs-kicker);
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--c-ink-soft);
    }

    .title {
        margin: 0;
        font-family: var(--font-header);
        font-weight: 400;
        font-size: 2.4rem;
        line-height: 1.15;
    }

    .depicted,
    .text {
        margin: 0;
        font-size: 1.7rem;
    }

    .note {
        margin: 0;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        background: var(--c-terracotta-soft);
        font-size: 1.5rem;
    }

    .reasoning {
        font-size: 1.4rem;
        color: var(--c-ink-soft);

        summary {
            cursor: pointer;
            color: var(--c-link);
        }

        p {
            margin: 0.6rem 0 0;
        }
    }

    .credit {
        margin: 0;
        font-size: 1.3rem;
        color: var(--c-ink-soft);

        a {
            color: var(--c-link);
        }
    }

    @keyframes fade {
        from {
            opacity: 0;
        }
    }
</style>
