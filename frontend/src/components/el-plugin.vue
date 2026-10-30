<script setup>
    import { computed, inject, onBeforeUnmount, ref, watch } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import { pluginComponent } from '@/plugins/index.js';

    const store = inject('store');
    const t = inject('t');

    const props = defineProps({
        id : {
            type : String,
            required : true
        },
        argument : {
            type : String,
            default : null
        },
        fullscreen : {
            type : Boolean,
            default : false
        }
    });

    const isLightboxOpen = ref(false);
    const plugin = computed(() => store.plugins[props.id] ?? null);
    const component = computed(() => pluginComponent(props.id));

    function closeLightbox() {
        isLightboxOpen.value = false;
    }

    function onKeydown(event) {
        if (event.key === 'Escape') {
            closeLightbox();
        }
    }

    watch(isLightboxOpen, (open) => {
        if (open) {
            window.addEventListener('keydown', onKeydown);
        } else {
            window.removeEventListener('keydown', onKeydown);
        }
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKeydown);
    });
</script>

<template>
    <div
        class="el-plugin"
        v-bind:is-fullscreen="fullscreen ? '' : null">
        <div class="frame">
            <component
                v-if="component"
                v-bind:is="component"
                v-bind:argument="argument"
                v-bind:fullscreen="fullscreen" />

            <div
                v-else
                class="placeholder">
                <strong class="placeholder__title">{{ plugin?.title ?? id }}</strong>
                <p
                    v-if="plugin?.description"
                    class="placeholder__text">{{ plugin.description }}</p>
                <p class="placeholder__text">{{ t('plugin_not_ready') }}</p>
            </div>

            <button
                v-if="!fullscreen && component"
                type="button"
                class="fullscreen"
                v-bind:aria-label="t('plugin_fullscreen')"
                v-on:click="isLightboxOpen = true">
                <el-icon
                    name="fullscreen"
                    v-bind:size="20" />
            </button>
        </div>

        <teleport to="body">
            <div
                v-if="isLightboxOpen"
                class="lightbox">
                <component
                    v-bind:is="component"
                    v-bind:argument="argument"
                    v-bind:fullscreen="true" />

                <button
                    type="button"
                    class="lightbox__close"
                    v-bind:aria-label="t('close')"
                    v-on:click="closeLightbox()">
                    <el-icon name="close" />
                </button>
            </div>
        </teleport>
    </div>
</template>

<style lang="scss" scoped>
    .el-plugin {
        margin: 0 0 1.8rem;
        padding: 0.8rem;
        border: 1px solid var(--c-frame);
        background: var(--c-plate);

        &[is-fullscreen] {
            height: 100%;
            margin: 0;
            padding: 0;
            border: 0;
            background: transparent;
        }
    }

    .frame {
        position: relative;

        [is-fullscreen] > & {
            height: 100%;
        }
    }

    .placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        min-height: 20rem;
        height: 100%;
        padding: 2rem;
        text-align: center;

        [is-fullscreen] > .frame > & {
            color: var(--c-paper);
        }
    }

    .placeholder__title {
        font-family: var(--font-header);
        font-size: 2.4rem;
        font-weight: 400;
    }

    .placeholder__text {
        margin: 0;
        font-style: italic;
        color: var(--c-ink-soft);

        [is-fullscreen] & {
            color: var(--c-rule);
        }
    }

    .fullscreen {
        position: absolute;
        right: 0.8rem;
        bottom: 0.8rem;
        width: 4.4rem;
        height: 4.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(251, 248, 241, 0.92);
        color: var(--c-marine);
        border: 1px solid var(--c-marine);
        border-radius: 4px;
        z-index: 1;
    }

    .lightbox {
        position: fixed;
        inset: 0;
        z-index: 100;
        background: rgba(10, 20, 32, 0.92);
    }

    .lightbox__close {
        position: absolute;
        top: 1.6rem;
        right: 1.6rem;
        width: 4.8rem;
        height: 4.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--c-paper);
        color: var(--c-marine);
        border-radius: 4px;
        z-index: 1;
    }
</style>
