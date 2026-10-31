<script setup>
    import { computed, inject, onMounted } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElMarkdown from '@/components/el-markdown.vue';

    const store = inject('store');
    const t = inject('t');

    const welcome = computed(() => store.pages.welcome ?? null);
    const firstChapter = computed(() => store.chapters[0] ?? null);
    const startTarget = computed(() => firstChapter.value ? `/chapters/${firstChapter.value.id}` : '/map');

    onMounted(() => {
        store.setMap({
            mode : 'home',
            focus : null,
            sheet : 'half',
            boat : firstChapter.value ? store.chapterPosition(firstChapter.value) : null
        });
    });
</script>

<template>
    <div class="vw-home">
        <article class="card">
            <header class="heading">
                <h1 class="title">{{ welcome?.title ?? 'De Siboga-Expeditie' }}</h1>

                <p class="tagline">{{ t('tagline') }}</p>
            </header>

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
        --pad-top: 2.6rem;
        --pad-x: 2.4rem;
        background: var(--c-paper);
        border-radius: 18px;
        padding: var(--pad-top) var(--pad-x) 1.8rem;
        box-shadow: var(--shadow-card);
        display: flex;
        flex-direction: column;
        gap: 1.6rem;
        animation: rise 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);

        @include mixins.respond-from(900px) {
            --pad-top: 3.2rem;
            --pad-x: 3.2rem;
            width: var(--sheet-width);
            padding-bottom: 2.2rem;
        }

        // Photo of the Siboga bleeding to the card edges and fading into the paper,
        // the negative bottom margin lets the title sit on the faded water
        &::before {
            content: "";
            flex-shrink: 0;
            margin: calc(var(--pad-top) * -1) calc(var(--pad-x) * -1) -14%;
            aspect-ratio: 1709 / 897;
            background:
                linear-gradient(to bottom, transparent 40%, var(--c-paper) 100%),
                url("../media/boat.jpg") center / cover no-repeat;
        }
    }

    // Title and tagline belong together, closer than the gap between the parts of the card
    .heading {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
    }

    .tagline {
        margin: 0;
        font-size: 1.7rem;
        font-style: italic;
        line-height: 1.3;
        color: var(--c-ink-soft);
        text-align: center;
    }

    .title {
        font-weight: 700;
        font-size: 3.2rem;
        line-height: 1.02;
        color: var(--c-marine);
        text-align: center;
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
