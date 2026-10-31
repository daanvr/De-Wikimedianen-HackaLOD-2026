<script setup>
    import { computed, inject, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElFields from '@/components/el-fields.vue';
    import ElAudio from '@/components/el-audio.vue';
    import ElFigure from '@/components/el-figure.vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElMarkdown from '@/components/el-markdown.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { chapterHeading, toRoman } from '@/services/format.js';

    const TYPE_ICONS = {
        person : 'person',
        specimen : 'specimen',
        media : 'image',
        location : 'location',
        item : 'item',
        publication : 'book',
        expedition : 'anchor'
    };

    const SOURCE_NAMES = {
        wikidata : 'Wikidata',
        commons : 'Wikimedia Commons',
        gbif : 'GBIF',
        archief_amsterdam : 'Stadsarchief Amsterdam',
        nta : 'Nederlandse Thesaurus van Auteursnamen'
    };

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const record = computed(() => store.records[route.params.id] ?? null);
    const mention = computed(() => route.query.mention ? `/${route.query.mention}` : null);
    const type = computed(() => record.value?.contentType ?? 'other');
    const name = computed(() => record.value?.label || record.value?.title || '');
    const sourceName = computed(() => SOURCE_NAMES[record.value?.source] ?? record.value?.source ?? '');

    // Every source the record takes data from; the first one is always uri itself
    const sources = computed(() => {
        const list = record.value?.sources?.length
            ? record.value.sources
            : [{
                name : record.value?.source ?? null,
                uri : record.value?.uri ?? null
            }];

        return list.filter((source) => source.uri).map((source) => ({
            uri : source.uri,
            name : SOURCE_NAMES[source.name] ?? source.name ?? '',
            display : source.uri.replace(/^https?:\/\//, '').replace(/\/$/, '')
        }));
    });

    const mentions = computed(() => (record.value?.backlinks ?? []).map((ref) => {
        const item = store.itemByRef(ref);

        if (!item) {
            return null;
        }

        const isChapter = ref.startsWith('chapters/');

        return {
            ref,
            // The page opens at the first place where it names this record
            to : {
                path : '/' + ref,
                query : {
                    mention : record.value.ref
                }
            },
            kicker : isChapter ? `${t('chapter')} ${toRoman(item.number)}` : t('content_type_single_' + (item.contentType ?? 'other')),
            title : isChapter ? chapterHeading(item) : (item.label || item.title)
        };
    }).filter(Boolean));

    // Without history (a shared link) there is nowhere to go back to
    const hasHistory = Boolean(window.history.state?.back);

    function goBack() {
        router.back();
    }

    // Through the history if we came from the library, so it returns to the same spot
    function openLibrary() {
        if (window.history.state?.back?.startsWith('/library')) {
            router.back();
        } else {
            router.push('/library');
        }
    }

    function enterRecord() {
        if (!record.value) {
            router.replace('/library');
            return;
        }

        const coordinates = record.value.coordinates;

        store.setMap({
            mode : store.map.mode === 'explore' ? 'explore' : 'story',
            sheet : 'full',
            focus : coordinates
                ? {
                    lon : coordinates.lon,
                    lat : coordinates.lat,
                    zoom : 7
                }
                : store.map.focus
        });
    }

    watch(() => route.params.id, enterRecord, {
        immediate : true
    });
</script>

<template>
    <div
        v-if="record"
        class="vw-record">
        <el-sheet
            state="screen">
            <div class="bar">
                <button
                    v-if="hasHistory"
                    type="button"
                    class="back-link"
                    v-on:click="goBack()">
                    <el-icon
                        name="arrowLeft"
                        v-bind:size="18" />
                    {{ t('back') }}
                </button>

                <button
                    type="button"
                    class="back-link bar__library"
                    v-on:click="openLibrary()">
                    <el-icon
                        name="book"
                        v-bind:size="18" />
                    {{ t('library') }}
                </button>
            </div>

            <div class="type-row">
                <router-link
                    class="type"
                    v-bind:to="{ path : '/library', query : { type } }">
                    <el-icon
                        v-bind:name="TYPE_ICONS[type] ?? 'info'"
                        v-bind:size="15"
                        v-bind:stroke-width="1.8" />
                    {{ t('content_type_single_' + type) }}
                </router-link>
            </div>

            <h1
                class="title"
                v-bind:is-specimen="type === 'specimen' ? '' : null">{{ name }}</h1>

            <p
                v-if="record.description"
                class="description">
                {{ record.description }}
            </p>

            <el-figure
                v-if="record.image"
                v-bind:image="record.image"
                v-bind:alt="name" />

            <el-audio
                v-if="record.audio"
                v-bind:audio="record.audio" />

            <el-markdown
                v-if="record.body"
                v-bind:body="record.body"
                v-bind:lookup-kind="store.kindForHref"
                v-bind:lookup-image="store.imageForHref"
                v-bind:lookup-term="store.termForHref"
                v-bind:highlight="mention" />

            <el-fields v-bind:fields="record.fields" />

            <a
                v-if="record.uri"
                class="source"
                v-bind:href="record.uri"
                target="_blank"
                rel="noopener">
                {{ t('record_source') }}<template v-if="sourceName">: {{ sourceName }}</template>
                <el-icon
                    name="external"
                    v-bind:size="14"
                    v-bind:stroke-width="1.8" />
            </a>

            <template v-if="sources.length">
                <h2 class="section-title">{{ t('record_sources') }}</h2>

                <ul class="sources">
                    <li
                        v-for="source in sources"
                        v-bind:key="source.uri"
                        class="sources__item">
                        <span
                            v-if="source.name"
                            class="sources__name">{{ source.name }}</span>
                        <a
                            class="sources__link"
                            v-bind:href="source.uri"
                            target="_blank"
                            rel="noopener">{{ source.display }}</a>
                    </li>
                </ul>
            </template>

            <template v-if="mentions.length">
                <h2 class="section-title">{{ t('mentioned_in') }}</h2>

                <router-link
                    v-for="mention in mentions"
                    v-bind:key="mention.ref"
                    class="mention"
                    v-bind:to="mention.to">
                    <span class="mention__text">
                        <span class="mention__kicker">{{ mention.kicker }}</span>
                        <span class="mention__title">{{ mention.title }}</span>
                    </span>
                    <el-icon
                        name="chevronRight"
                        v-bind:size="18" />
                </router-link>
            </template>
        </el-sheet>
    </div>
</template>

<style lang="scss" scoped>
    @use "../../node_modules/valenski/mixins";

    .vw-record {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    // Leaves room for the menu button in the top right corner (see app.vue)
    .bar {
        display: flex;
        align-items: center;
        gap: 1.6rem;
        min-height: 4.8rem;

        // Fullscreen on mobile: leaves room for the menu button (see app.vue)
        @include mixins.respond-until(900px) {
            padding-right: 6.4rem;
        }
    }

    .bar__library {
        margin-left: auto;
    }

    .type-row {
        border-top: 1px solid var(--c-ink);
        margin-top: 0.6rem;
        padding-top: 1.4rem;
    }

    .type {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        min-height: 3.2rem;
        padding: 0 1.2rem;
        border: 1px solid var(--c-marine);
        border-radius: 999px;
        color: var(--c-marine);
        text-decoration: none;
        font-family: var(--font-header);
        font-size: 1.3rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .title {
        margin: 1rem 0 0.4rem;
        font-weight: 700;
        font-size: 3.2rem;
        line-height: 1.06;

        &[is-specimen] {
            font-style: italic;
        }
    }

    .description {
        font-style: italic;
        font-size: 1.7rem;
        color: var(--c-ink-soft);
        margin-bottom: 1.6rem;
    }

    .source {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        min-height: 3.6rem;
        font-size: 1.5rem;
        margin-bottom: 1.6rem;
    }

    .section-title {
        margin: 1.2rem 0 0.6rem;
        font-weight: 400;
        font-size: 1.3rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #3A4254;
    }

    .sources {
        list-style: none;
        margin-bottom: 1.6rem;
    }

    .sources__item {
        display: flex;
        flex-direction: column;
        padding: 0.8rem 0;
        border-bottom: 1px solid var(--c-rule);
    }

    .sources__name {
        font-size: 1.6rem;
        color: var(--c-ink);
    }

    .sources__link {
        font-size: 1.4rem;
        overflow-wrap: anywhere;
    }

    .mention {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;
        min-height: 5.6rem;
        border-bottom: 1px solid var(--c-rule);
        text-decoration: none;
        color: var(--c-ink);

        &:hover {
            color: var(--c-ink);
            background: var(--c-plate);
        }

        .el-icon {
            color: var(--c-link);
        }
    }

    .mention__text {
        display: flex;
        flex-direction: column;
    }

    .mention__kicker {
        font-family: var(--font-header);
        font-size: 1.2rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--c-terracotta);
    }

    .mention__title {
        font-size: 1.7rem;
    }
</style>
