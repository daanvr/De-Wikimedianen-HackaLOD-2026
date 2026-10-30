<script setup>
    import { computed, inject, onBeforeUnmount, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElChapterNav from '@/components/el-chapter-nav.vue';
    import ElMapButton from '@/components/el-map-button.vue';
    import ElMarkdown from '@/components/el-markdown.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { chapterHeading, toRoman } from '@/services/format.js';

    const TRAVEL_MS = 2600;
    const CHAPTER_ZOOM = 6.2;

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const sheet = ref(null);
    const sheetState = ref('half');
    const isTravelling = ref(false);

    let travelTimer = null;

    const chapter = computed(() => store.chapterById(route.params.id));
    const index = computed(() => store.chapters.findIndex((item) => item.id === route.params.id));
    const nextChapter = computed(() => store.chapters[index.value + 1] ?? null);
    const previousChapter = computed(() => index.value > 0 ? store.chapters[index.value - 1] : null);
    const numeral = computed(() => toRoman(chapter.value?.number ?? index.value + 1));
    const heading = computed(() => chapter.value ? chapterHeading(chapter.value) : '');
    const kicker = computed(() => chapter.value?.kicker ?? null);
    const mention = computed(() => route.query.mention ? `/${route.query.mention}` : null);

    function enterChapter() {
        if (!chapter.value) {
            router.replace('/chapters');
            return;
        }

        const position = store.chapterPosition(chapter.value);
        const previous = store.map.boat;
        const moves = previous && store.map.mode === 'story'
            && (previous.lon !== position.lon || previous.lat !== position.lat);

        // On mobile the sheet folds in while the boat sails, so the voyage can be seen;
        // not when it opens at a mention, which then has to stay in view
        const nextSheet = moves && !mention.value ? 'peek' : 'half';

        clearTimeout(travelTimer);
        sheet.value?.scrollToTop();

        store.setMap({
            mode : 'story',
            boat : position,
            focus : {
                ...position,
                zoom : CHAPTER_ZOOM,
                fly : moves
            },
            sheet : nextSheet
        });

        sheetState.value = nextSheet;
        isTravelling.value = Boolean(moves);

        if (moves) {
            travelTimer = setTimeout(() => {
                isTravelling.value = false;
                sheetState.value = 'half';
            }, TRAVEL_MS + 200);
        }

        store.markChapterRead(chapter.value.id);
    }

    function recenter() {
        if (!chapter.value) {
            return;
        }

        store.setMap({
            focus : {
                ...store.chapterPosition(chapter.value),
                zoom : CHAPTER_ZOOM,
                at : Date.now()
            }
        });
    }

    watch(() => [route.params.id, route.query.mention], enterChapter, {
        immediate : true
    });

    watch(sheetState, (state) => {
        store.setMap({
            sheet : state
        });
    });

    onBeforeUnmount(() => {
        clearTimeout(travelTimer);
    });
</script>

<template>
    <div
        v-if="chapter"
        class="vw-chapter"
        v-bind:sheet="sheetState">
        <p
            v-if="isTravelling"
            class="travel-note">
            {{ t('on_the_way') }}
        </p>

        <el-map-button
            class="to-boat"
            icon="anchor"
            v-bind:label="t('to_boat')"
            v-on:click="recenter()" />

        <el-sheet
            ref="sheet"
            v-bind:state="sheetState">
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

                <div
                    v-if="isTravelling"
                    class="progress"
                    role="progressbar"
                    aria-valuemin="0"
                    aria-valuemax="100">
                    <span class="progress__bar"></span>
                </div>

                <div
                    v-else
                    class="double-rule"></div>
            </header>

            <el-markdown
                v-bind:body="chapter.body"
                v-bind:lookup-kind="store.kindForHref"
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

    .travel-note {
        position: absolute;
        top: 8rem;
        left: 50%;
        transform: translateX(-50%);
        padding: 0.6rem 1.2rem;
        border-radius: 3px;
        background: rgba(22, 58, 92, 0.88);
        color: var(--c-paper);
        font-family: var(--font-header);
        font-style: italic;
        font-size: 1.4rem;
        white-space: nowrap;
        z-index: 10;
    }

    .to-boat {
        position: absolute;
        right: 1.6rem;
        top: calc(48% - 6.4rem);
        transition: top 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
        z-index: 15;

        @include mixins.respond-from(900px) {
            top: auto;
            bottom: 2.4rem;
        }
    }

    .vw-chapter[sheet="peek"] .to-boat {
        top: calc(100% - 14rem - 6.4rem);

        @include mixins.respond-from(900px) {
            top: auto;
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

    .progress {
        height: 3px;
        background: #E6DFCF;
        border-radius: 2px;
        overflow: hidden;
        margin-bottom: 1.4rem;
    }

    .progress__bar {
        display: block;
        height: 100%;
        width: 100%;
        background: var(--c-terracotta);
        transform-origin: left;
        animation: travel 2.6s cubic-bezier(0.45, 0, 0.55, 1) forwards;
    }

    @keyframes travel {
        from {
            transform: scaleX(0);
        }
    }
</style>
