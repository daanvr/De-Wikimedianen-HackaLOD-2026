<script setup>
    import { inject } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import { chapterHeading } from '@/services/format.js';

    const t = inject('t');

    defineProps({
        // The next chapter; without one this is the end of the story
        next : {
            type : Object,
            default : null
        }
    });
</script>

<template>
    <nav class="el-chapter-end">
        <template v-if="next">
            <p class="kicker up-next">{{ t('chapter_end_up_next') }}: {{ chapterHeading(next) }}</p>

            <router-link
                class="button-link"
                v-bind:to="`/chapters/${next.id}`">
                {{ t('chapter_end_next') }}
                <el-icon
                    name="arrowRight"
                    v-bind:size="20"
                    v-bind:stroke-width="1.9" />
            </router-link>
        </template>

        <!-- After the last chapter the story goes on in the data and the library -->
        <template v-else>
            <router-link
                class="button-link"
                to="/map">
                {{ t('start_data_visualisation') }}
                <el-icon
                    name="explore"
                    v-bind:size="20"
                    v-bind:stroke-width="1.9" />
            </router-link>

            <router-link
                class="button-link button-link--outline"
                to="/library">
                {{ t('chapter_end_library') }}
                <el-icon
                    name="book"
                    v-bind:size="20"
                    v-bind:stroke-width="1.9" />
            </router-link>
        </template>
    </nav>
</template>

<style lang="scss" scoped>
    // The same buttons as on the home screen
    .el-chapter-end {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin: 3.2rem 0 2.4rem;
    }

    .up-next {
        margin: 0;
        color: var(--c-ink-soft);
    }

    .button-link {
        min-height: 5.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: 0 1.6rem;
        background: var(--c-terracotta);
        color: var(--c-paper);
        text-decoration: none;
        text-align: center;
        font-weight: 600;
        font-size: 1.9rem;
        border-radius: 12px;
        transition: background 0.15s ease;

        &:hover {
            background: var(--c-terracotta-dark);
            color: var(--c-paper);
        }
    }

    .button-link--outline {
        background: transparent;
        color: var(--c-marine);
        box-shadow: inset 0 0 0 2px var(--c-marine);

        &:hover {
            background: var(--c-marine);
            color: var(--c-paper);
        }
    }
</style>
