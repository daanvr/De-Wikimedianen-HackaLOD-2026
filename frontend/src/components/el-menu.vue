<script setup>
    import { computed, inject, onBeforeUnmount, ref, watch } from 'vue';
    import { useRoute } from 'vue-router';
    import ElIcon from '@/components/el-icon.vue';
    import ElMapButton from '@/components/el-map-button.vue';
    import ElShare from '@/components/el-share.vue';

    const t = inject('t');
    const route = useRoute();

    const isOpen = ref(false);
    const isShareOpen = ref(false);
    const shareUrl = computed(() => window.location.origin + route.fullPath);

    const items = computed(() => {
        return [
            {
                to : '/',
                icon : 'home',
                label : t('menu_home')
            },
            {
                to : '/chapters',
                icon : 'list',
                label : t('chapters')
            },
            {
                to : '/library',
                icon : 'book',
                label : t('library')
            },
            {
                to : '/map',
                icon : 'explore',
                label : t('explore_mode')
            }
        ];
    });

    function close() {
        isOpen.value = false;
    }

    function onKeydown(event) {
        if (event.key === 'Escape') {
            close();
        }
    }

    function share() {
        close();
        isShareOpen.value = true;
    }

    function toggle() {
        isOpen.value = !isOpen.value;
    }

    watch(isOpen, (open) => {
        if (open) {
            window.addEventListener('keydown', onKeydown);
        } else {
            window.removeEventListener('keydown', onKeydown);
        }
    });

    watch(() => route.fullPath, close);

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKeydown);
    });
</script>

<template>
    <div
        class="el-menu"
        v-bind:is-open="isOpen ? '' : null">
        <div
            v-if="isOpen"
            class="el-menu__scrim"
            v-on:click="close()"></div>

        <el-map-button
            v-bind:icon="isOpen ? 'close' : 'menu'"
            v-bind:label="isOpen ? t('menu_close') : t('menu_open')"
            v-bind:aria-expanded="isOpen ? 'true' : 'false'"
            variant="terracotta"
            v-on:click="toggle()" />

        <nav
            v-if="isOpen"
            class="el-menu__panel"
            v-bind:aria-label="t('menu_open')">
            <router-link
                v-for="item in items"
                v-bind:key="item.to"
                class="el-menu__item"
                v-bind:to="item.to">
                <span class="el-menu__tile">
                    <el-icon
                        v-bind:name="item.icon"
                        v-bind:size="22" />
                </span>
                {{ item.label }}
            </router-link>

            <div class="el-menu__rule"></div>

            <router-link
                class="el-menu__item"
                to="/pages/about">
                <span class="el-menu__tile">
                    <el-icon
                        name="info"
                        v-bind:size="22" />
                </span>
                {{ t('about_site') }}
            </router-link>

            <button
                type="button"
                class="el-menu__item"
                v-on:click="share()">
                <span class="el-menu__tile">
                    <el-icon
                        name="share"
                        v-bind:size="22" />
                </span>
                {{ t('share') }}
            </button>
        </nav>

        <el-share
            v-if="isShareOpen"
            v-bind:url="shareUrl"
            v-on:close="isShareOpen = false" />
    </div>
</template>

<style lang="scss" scoped>
    .el-menu {
        position: relative;
        pointer-events: auto;
        z-index: 30;

        &[is-open] {
            z-index: 60;
        }

        :deep(.el-map-button) {
            position: relative;
        }
    }

    .el-menu__scrim {
        position: fixed;
        inset: 0;
        background: var(--c-scrim);
        animation: fade-in 0.15s ease;
    }

    .el-menu__panel {
        position: absolute;
        top: calc(100% + 1.2rem);
        right: 0;
        width: 27rem;
        background: var(--c-paper);
        border-radius: 10px;
        padding: 0.8rem 0;
        box-shadow: var(--shadow-card);
        animation: drop-in 0.18s ease;
    }

    .el-menu__item {
        display: flex;
        align-items: center;
        gap: 1.4rem;
        width: 100%;
        min-height: 5.8rem;
        padding: 0 1.8rem;
        border: 0;
        background: none;
        text-align: left;
        text-decoration: none;
        cursor: pointer;
        color: var(--c-ink);
        font-family: inherit;
        font-size: 1.9rem;

        &:hover {
            background: var(--c-plate);
            color: var(--c-ink);
        }

        &.router-link-active {
            font-weight: 600;
        }
    }

    .el-menu__tile {
        width: 4rem;
        height: 4rem;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        background: var(--c-plate);
        color: var(--c-marine);
    }

    .el-menu__rule {
        height: 1px;
        margin: 0.6rem 1.8rem;
        background: var(--c-rule);
    }

    @keyframes fade-in {
        from {
            opacity: 0;
        }
    }

    @keyframes drop-in {
        from {
            opacity: 0;
            transform: translateY(-0.6rem);
        }
    }
</style>
