<script setup>
    import { inject, onBeforeUnmount, onMounted } from 'vue';
    import ElIcon from '@/components/el-icon.vue';

    const t = inject('t');

    const emit = defineEmits(['close']);

    const props = defineProps({
        // Closes on any click, for an image; an interactive plugin needs its clicks
        closeOnClick : {
            type : Boolean,
            default : false
        },
        // The content fills the whole screen instead of being centered
        fill : {
            type : Boolean,
            default : false
        }
    });

    function close() {
        emit('close');
    }

    function onClick() {
        if (props.closeOnClick) {
            close();
        }
    }

    function onKeydown(event) {
        if (event.key === 'Escape') {
            close();
        }
    }

    onMounted(() => {
        window.addEventListener('keydown', onKeydown);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKeydown);
    });
</script>

<template>
    <!-- In body, so the lightbox lies above the menu and not in the stacking context of the sheet -->
    <teleport to="body">
        <div
            class="el-lightbox"
            v-bind:is-fill="fill ? '' : null"
            v-on:click="onClick()">
            <slot />

            <button
                type="button"
                class="close"
                v-bind:aria-label="t('close')"
                v-on:click.stop="close()">
                <el-icon name="close" />
            </button>
        </div>
    </teleport>
</template>

<style lang="scss" scoped>
    .el-lightbox {
        position: fixed;
        inset: 0;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(10, 20, 32, 0.92);

        &[is-fill] {
            display: block;
            padding: 0;
        }

        :slotted(img) {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
    }

    .close {
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
