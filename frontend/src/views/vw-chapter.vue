<script setup>
    import { computed, inject, onBeforeUnmount, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElChapterNav from '@/components/el-chapter-nav.vue';
    import ElLayerButton from '@/components/el-layer-button.vue';
    import ElMarkdown from '@/components/el-markdown.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { chapterHeading, toRoman } from '@/services/format.js';
    import { boundsOf } from '@/services/geo.js';

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const sheet = ref(null);

    const chapter = computed(() => store.chapterById(route.params.id));
    const index = computed(() => store.chapters.findIndex((item) => item.id === route.params.id));
    const nextChapter = computed(() => store.chapters[index.value + 1] ?? null);
    const previousChapter = computed(() => index.value > 0 ? store.chapters[index.value - 1] : null);
    const numeral = computed(() => toRoman(chapter.value?.number ?? index.value + 1));
    const heading = computed(() => chapter.value ? chapterHeading(chapter.value) : '');
    const kicker = computed(() => chapter.value?.kicker ?? null);
    const mention = computed(() => route.query.mention ? `/${route.query.mention}` : null);

    // The markers of the chapter, or the whole route if it has none
    function chapterFocus() {
        const markers = chapter.value.markers ?? [];

        return {
            bounds : markers.length ? boundsOf(markers.map((marker) => [marker.lon, marker.lat])) : null
        };
    }

    function enterChapter() {
        if (!chapter.value) {
            router.replace('/chapters');
            return;
        }

        sheet.value?.scrollToTop();

        store.setMap({
            mode : 'story',
            markers : chapter.value.markers ?? [],
            focus : chapterFocus(),
            sheet : 'half'
        });

        store.markChapterRead(chapter.value.id);
    }

    function setLayer(layer) {
        store.setMap({
            base : layer
        });
    }

    watch(() => [route.params.id, route.query.mention], enterChapter, {
        immediate : true
    });

    // The markers belong to the chapter
    onBeforeUnmount(() => {
        store.setMap({
            markers : []
        });
    });
</script>

<template>
    <div
        v-if="chapter"
        class="vw-chapter">
        <el-layer-button
            class="layer-button"
            v-bind:layer="store.map.base"
            v-on:change="setLayer($event)" />

        <el-sheet
            ref="sheet"
            state="half">
            <el-chapter-nav
                class="top-nav"
                v-bind:previous="previousChapter"
                v-bind:next="nextChapter" />

            <header class="header">
                <div class="kicker kicker-row">
                    <span>{{ t('chapter') }} {{ numeral }}</span>
                    <span v-if="kicker">{{ kicker }}</span>
                </div>

                <h1 class="title">{{ heading }}</h1>

                <div class="double-rule"></div>
            </header>

            <el-markdown
                v-bind:body="chapter.body"
                v-bind:lookup-kind="store.kindForHref"
                v-bind:lookup-image="store.imageForHref"
                v-bind:highlight="mention"
                drop-cap />

            <div
                class="ornament"
                aria-hidden="true">
                <svg
                    width="10"
                    height="10"
                    viewBox="0 0 10 10">
                    <path
                        d="M5 0L6.2 3.8L10 5L6.2 6.2L5 10L3.8 6.2L0 5L3.8 3.8Z"
                        fill="#A9512F" />
                </svg>
            </div>

            <el-chapter-nav
                v-bind:previous="previousChapter"
                v-bind:next="nextChapter" />
        </el-sheet>
    </div>
</template>

<style lang="scss" scoped>
    @use "../../node_modules/valenski/mixins";

    .vw-chapter {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    // Just above the sheet on mobile
    .layer-button {
        position: absolute;
        right: 1.6rem;
        top: calc(48% - 6.4rem);
        z-index: 15;

        @include mixins.respond-from(900px) {
            top: auto;
            bottom: 2.4rem;
        }
    }

    .top-nav {
        margin-bottom: 1.2rem;
    }

    .header {
        padding-top: 0.2rem;
    }

    .kicker-row {
        display: flex;
        justify-content: space-between;
        gap: 1.2rem;
        border-top: 1px solid var(--c-ink);
        border-bottom: 1px solid var(--c-ink);
        padding: 0.5rem 0 0.4rem;
        color: #3A4254;
    }

    .title {
        margin: 1.4rem 0 1.2rem;
        font-weight: 700;
        font-size: 3rem;
        line-height: 1.08;
        color: var(--c-ink);
    }

    .double-rule {
        border-top: 3px double var(--c-ink);
        margin-bottom: 1.4rem;
    }
</style>
