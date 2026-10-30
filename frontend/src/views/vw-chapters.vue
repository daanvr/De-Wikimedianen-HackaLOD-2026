<script setup>
    import { computed, inject, onMounted } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElMenu from '@/components/el-menu.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { chapterHeading, toRoman } from '@/services/format.js';

    const store = inject('store');
    const t = inject('t');

    const lastRead = computed(() => store.readChapters.at(-1) ?? null);

    const items = computed(() => store.chapters.map((chapter, index) => {
        let state = 'next';

        if (chapter.id === lastRead.value) {
            state = 'current';
        } else if (store.readChapters.includes(chapter.id)) {
            state = 'read';
        }

        return {
            id : chapter.id,
            numeral : toRoman(chapter.number ?? index + 1),
            heading : chapterHeading(chapter),
            kicker : chapter.kicker ?? null,
            state
        };
    }));

    onMounted(() => {
        store.setMap({
            mode : 'story',
            stationId : null,
            focus : null,
            sheet : 'full'
        });
    });
</script>

<template>
    <div class="vw-chapters">
        <el-sheet
            state="full"
            v-bind:states="['full']">
            <div class="bar">
                <router-link
                    class="back-link"
                    v-bind:to="lastRead ? `/chapters/${lastRead}` : '/'">
                    <el-icon
                        name="arrowLeft"
                        v-bind:size="18" />
                    {{ t('back_to_map') }}
                </router-link>

                <el-menu
                    mode="story"
                    v-bind:floating="false" />
            </div>

            <h1 class="title">{{ t('chapters') }}</h1>
            <p class="intro">{{ t('chapters_intro') }}</p>

            <ol class="list">
                <li
                    v-for="item in items"
                    v-bind:key="item.id">
                    <router-link
                        class="item"
                        v-bind:to="`/chapters/${item.id}`"
                        v-bind:state="item.state">
                        <span class="badge">{{ item.numeral }}</span>
                        <span class="text">
                            <span class="heading">{{ item.heading }}</span>
                            <span
                                v-if="item.kicker || item.state !== 'next'"
                                class="meta">
                                {{ item.kicker }}
                                <template v-if="item.kicker && item.state !== 'next'"> · </template>
                                <template v-if="item.state === 'current'">{{ t('chapter_current') }}</template>
                                <template v-if="item.state === 'read'">{{ t('chapter_read') }}</template>
                            </span>
                        </span>
                        <el-icon
                            class="chevron"
                            name="chevronRight"
                            v-bind:size="18" />
                    </router-link>
                </li>
            </ol>
        </el-sheet>
    </div>
</template>

<style lang="scss" scoped>
    .vw-chapters {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    .bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;
    }

    .title {
        margin: 0.8rem 0 0.4rem;
        padding-top: 1.2rem;
        border-top: 1px solid var(--c-ink);
        font-weight: 700;
        font-size: 3.2rem;
        line-height: 1.06;
    }

    .intro {
        font-style: italic;
        font-size: 1.7rem;
        color: var(--c-ink-soft);
        margin-bottom: 1.4rem;
    }

    .list {
        list-style: none;
        border-top: 1px solid var(--c-ink);
    }

    .item {
        display: flex;
        align-items: center;
        gap: 1.4rem;
        min-height: 6.8rem;
        padding: 0.8rem 0;
        border-bottom: 1px solid var(--c-rule);
        text-decoration: none;
        color: var(--c-ink);

        &:hover {
            color: var(--c-ink);
            background: var(--c-plate);
        }

        &[state="current"] .badge {
            background: var(--c-terracotta);
            color: var(--c-paper);
            border-color: var(--c-terracotta);
        }

        &[state="read"] .badge {
            background: var(--c-terracotta-soft);
            color: var(--c-terracotta-dark);
            border-color: var(--c-terracotta-soft);
        }
    }

    .badge {
        width: 4rem;
        height: 4rem;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        border: 1px solid var(--c-marine);
        color: var(--c-marine);
        font-family: var(--font-header);
        font-weight: 700;
        font-size: 1.5rem;
    }

    .text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }

    .heading {
        font-size: 1.8rem;
        line-height: 1.25;
    }

    .meta {
        font-size: 1.4rem;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .chevron {
        color: var(--c-link);
    }
</style>
