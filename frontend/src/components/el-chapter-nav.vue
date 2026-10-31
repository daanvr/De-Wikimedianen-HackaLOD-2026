<script setup>
    import { inject } from 'vue';
    import ElIcon from '@/components/el-icon.vue';

    const t = inject('t');

    defineProps({
        previous : {
            type : Object,
            default : null
        },
        next : {
            type : Object,
            default : null
        }
    });
</script>

<template>
    <nav class="el-chapter-nav">
        <router-link
            v-if="previous"
            class="back-link link link--previous"
            v-bind:to="`/chapters/${previous.id}`">
            <el-icon
                name="arrowLeft"
                v-bind:size="18" />
            {{ t('chapter_nav_previous') }}
        </router-link>
        <span v-else></span>

        <router-link
            class="back-link link link--all"
            to="/chapters">
            <el-icon
                name="list"
                v-bind:size="18" />
            {{ t('chapters') }}
        </router-link>

        <router-link
            v-if="next"
            class="back-link link link--next"
            v-bind:to="`/chapters/${next.id}`">
            {{ t('chapter_nav_next') }}
            <el-icon
                name="arrowRight"
                v-bind:size="18" />
        </router-link>

        <!-- After the last chapter the story goes on in the data -->
        <router-link
            v-else
            class="back-link link link--next"
            to="/map">
            {{ t('data_visualisation') }}
            <el-icon
                name="explore"
                v-bind:size="18" />
        </router-link>
    </nav>
</template>

<style lang="scss" scoped>
    .el-chapter-nav {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 1.2rem;
    }

    .link {
        font-size: 1.5rem;
        line-height: 1.2;
    }

    .link--all {
        justify-self: center;
    }

    .link--next {
        justify-self: end;
        text-align: right;
    }
</style>
