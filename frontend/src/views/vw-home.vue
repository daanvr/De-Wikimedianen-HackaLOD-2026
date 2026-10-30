<script setup>
    import { computed, inject, onMounted } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElMarkdown from '@/components/el-markdown.vue';
    import ElSeal from '@/components/el-seal.vue';

    const store = inject('store');
    const t = inject('t');

    const welcome = computed(() => store.pages.welcome ?? null);
    const firstChapter = computed(() => store.chapters[0] ?? null);
    const startTarget = computed(() => firstChapter.value ? `/chapters/${firstChapter.value.id}` : '/map');

    onMounted(() => {
        store.setMap({
            mode : 'home',
            focus : null,
            stationId : null,
            sheet : 'half',
            boat : firstChapter.value ? store.chapterPosition(firstChapter.value) : null
        });
    });
</script>

<template>
    <div class="vw-home">
        <article class="card">
            <div class="intro">
                <el-seal v-bind:size="60" />
                <p class="tagline">{{ t('tagline') }}</p>
            </div>

            <h1 class="title">{{ welcome?.title ?? 'De Siboga-Expeditie' }}</h1>

            <el-markdown
                class="text"
                v-bind:body="welcome?.body" />

            <router-link
                class="start"
                v-bind:to="startTarget">
                {{ t('start_bn') }}
                <el-icon
                    name="arrowRight"
                    v-bind:size="20"
                    v-bind:stroke-width="1.9" />
            </router-link>

            <router-link
                class="about"
                to="/pages/about">
                {{ t('about_site') }}
            </router-link>
        </article>
    </div>
</template>

<style lang="scss" scoped>
    @use "../../node_modules/valenski/mixins";

    .vw-home {
        position: absolute;
        inset: 0;
        pointer-events: none;
        display: flex;
        align-items: flex-end;
        padding: 1.6rem 1.6rem 2.4rem;

        @include mixins.respond-from(900px) {
            align-items: center;
            padding: 3.2rem;
        }
    }

    .card {
        pointer-events: auto;
        width: 100%;
        max-height: 100%;
        overflow-y: auto;
        background: var(--c-paper);
        border-radius: 18px;
        padding: 2.6rem 2.4rem 1.8rem;
        box-shadow: var(--shadow-card);
        display: flex;
        flex-direction: column;
        gap: 1.6rem;
        animation: rise 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);

        @include mixins.respond-from(900px) {
            width: var(--sheet-width);
            padding: 3.2rem 3.2rem 2.2rem;
        }
    }

    .intro {
        display: flex;
        align-items: center;
        gap: 1.4rem;
    }

    .tagline {
        font-size: 1.7rem;
        font-style: italic;
        line-height: 1.3;
        color: var(--c-ink-soft);
    }

    .title {
        font-weight: 700;
        font-size: 3.8rem;
        line-height: 1.02;
        color: var(--c-marine);
    }

    .text {
        line-height: 1.5;

        :deep(p:last-child) {
            margin-bottom: 0;
        }
    }

    // Deliberately not newspaper style: rounded, sentence case
    .start {
        margin-top: 0.4rem;
        min-height: 5.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        background: var(--c-terracotta);
        color: var(--c-paper);
        text-decoration: none;
        font-weight: 600;
        font-size: 1.9rem;
        border-radius: 12px;
        transition: background 0.15s ease;

        &:hover {
            background: var(--c-terracotta-dark);
            color: var(--c-paper);
        }
    }

    .about {
        align-self: center;
        min-height: 4.4rem;
        display: inline-flex;
        align-items: center;
        font-size: 1.6rem;
        text-underline-offset: 3px;
    }

    @keyframes rise {
        from {
            opacity: 0;
            transform: translateY(2rem);
        }
    }
</style>
