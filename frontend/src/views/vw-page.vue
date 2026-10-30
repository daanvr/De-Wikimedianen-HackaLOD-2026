<script setup>
    import { computed, inject, onMounted } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElIcon from '@/components/el-icon.vue';
    import ElMarkdown from '@/components/el-markdown.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { fillBuildInfo } from '@/services/build-info.js';

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const page = computed(() => store.pages[route.params.id] ?? null);
    const mention = computed(() => route.query.mention ? `/${route.query.mention}` : null);
    const body = computed(() => fillBuildInfo(page.value?.body, store.meta, t));

    function goBack() {
        if (window.history.state?.back) {
            router.back();
        } else {
            router.push('/');
        }
    }

    onMounted(() => {
        if (!page.value) {
            router.replace('/');
            return;
        }

        store.setMap({
            sheet : 'full'
        });
    });
</script>

<template>
    <div
        v-if="page"
        class="vw-page">
        <el-sheet
            state="full"
            v-bind:states="['full']">
            <div class="bar">
                <button
                    type="button"
                    class="back-link"
                    v-on:click="goBack()">
                    <el-icon
                        name="arrowLeft"
                        v-bind:size="18" />
                    {{ t('back') }}
                </button>
            </div>

            <h1 class="title">{{ page.title }}</h1>

            <el-markdown
                v-bind:body="body"
                v-bind:lookup-kind="store.kindForHref"
                v-bind:highlight="mention" />
        </el-sheet>
    </div>
</template>

<style lang="scss" scoped>
    .vw-page {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    // Leaves room for the menu button in the top right corner (see app.vue)
    .bar {
        display: flex;
        align-items: center;
        min-height: 4.8rem;
    }

    .title {
        margin: 0.8rem 0 1.6rem;
        padding-top: 1.2rem;
        border-top: 1px solid var(--c-ink);
        font-weight: 700;
        font-size: 3.2rem;
        line-height: 1.06;
    }
</style>
