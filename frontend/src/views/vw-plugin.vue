<script setup>
    import { computed, inject, onMounted } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElIcon from '@/components/el-icon.vue';
    import ElPlugin from '@/components/el-plugin.vue';

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const plugin = computed(() => store.plugins[route.params.id] ?? null);
    const argument = computed(() => route.query.argument ? String(route.query.argument) : null);

    function goBack() {
        if (window.history.state?.back) {
            router.back();
        } else {
            router.push('/map');
        }
    }

    onMounted(() => {
        if (!plugin.value) {
            router.replace('/map');
            return;
        }

        store.setMap({
            sheet : 'none'
        });
    });
</script>

<template>
    <div
        v-if="plugin"
        class="vw-plugin">
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

            <h1 class="title">{{ plugin.title }}</h1>
        </div>

        <div class="content">
            <el-plugin
                v-bind:id="plugin.id"
                v-bind:argument="argument"
                v-bind:fullscreen="true" />
        </div>
    </div>
</template>

<style lang="scss" scoped>
    .vw-plugin {
        position: absolute;
        inset: 0;
        z-index: 40;
        display: flex;
        flex-direction: column;
        background: rgba(10, 20, 32, 0.92);
    }

    // Leaves room for the menu button in the top right corner (see app.vue)
    .bar {
        display: flex;
        align-items: center;
        gap: 1.6rem;
        min-height: 8rem;
        padding: 0 7.4rem 0 1.6rem;
        color: var(--c-paper);

        .back-link {
            color: var(--c-paper);
        }
    }

    .title {
        margin: 0;
        font-weight: 400;
        font-size: 2.4rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .content {
        flex: 1;
        min-height: 0;
    }
</style>
