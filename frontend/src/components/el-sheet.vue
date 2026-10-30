<script setup>
    import { inject, ref, watch } from 'vue';

    const t = inject('t');

    const props = defineProps({
        state : {
            type : String,
            default : 'half'
        },
        states : {
            type : Array,
            default : () => ['peek', 'half', 'full']
        }
    });

    const emit = defineEmits(['update:state']);

    const body = ref(null);
    const dragOffset = ref(0);
    const isDragging = ref(false);

    let dragStart = null;

    function cycle() {
        const index = props.states.indexOf(props.state);
        const next = index < props.states.length - 1 ? props.states[index + 1] : props.states[0];

        emit('update:state', next);
    }

    function move(direction) {
        const index = props.states.indexOf(props.state);
        const next = props.states[Math.max(0, Math.min(props.states.length - 1, index + direction))];

        if (next !== props.state) {
            emit('update:state', next);
        }
    }

    function onPointerDown(event) {
        dragStart = event.clientY;
        isDragging.value = true;
        event.currentTarget.setPointerCapture(event.pointerId);
    }

    function onPointerMove(event) {
        if (dragStart === null) {
            return;
        }

        dragOffset.value = event.clientY - dragStart;
    }

    function onPointerUp() {
        if (dragStart === null) {
            return;
        }

        const offset = dragOffset.value;

        dragStart = null;
        isDragging.value = false;
        dragOffset.value = 0;

        if (Math.abs(offset) < 8) {
            cycle();
        } else if (offset < -40) {
            move(1);
        } else if (offset > 40) {
            move(-1);
        }
    }

    watch(() => props.state, () => {
        if (props.state !== 'full' && body.value) {
            body.value.scrollTop = 0;
        }
    });

    defineExpose({
        scrollToTop : () => body.value?.scrollTo({
            top : 0
        })
    });
</script>

<template>
    <section
        class="el-sheet"
        v-bind:state="state"
        v-bind:is-dragging="isDragging ? '' : null"
        v-bind:style="isDragging ? { transform : `translateY(${dragOffset}px)` } : null">
        <button
            type="button"
            class="el-sheet__handle"
            v-bind:aria-label="state === 'full' ? t('collapse') : t('expand')"
            v-on:pointerdown="onPointerDown"
            v-on:pointermove="onPointerMove"
            v-on:pointerup="onPointerUp"
            v-on:pointercancel="onPointerUp">
            <span class="el-sheet__grip"></span>
        </button>

        <div
            ref="body"
            class="el-sheet__body">
            <slot />
        </div>
    </section>
</template>

<style lang="scss" scoped>
    @use "../../node_modules/valenski/mixins";

    .el-sheet {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        top: 48%;
        display: flex;
        flex-direction: column;
        background: var(--c-paper);
        border-radius: 16px 16px 0 0;
        box-shadow: var(--shadow-sheet);
        pointer-events: auto;
        transition: top 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
        z-index: 20;

        &[state="full"] {
            top: 4rem;
        }

        &[state="peek"] {
            top: calc(100% - 14rem);
        }

        &[is-dragging] {
            transition: none;
        }

        @include mixins.respond-from(900px) {
            top: 1.6rem;
            bottom: 1.6rem;
            left: 1.6rem;
            right: auto;
            width: var(--sheet-width);
            border-radius: 12px;
            box-shadow: var(--shadow-card);

            &[state="full"],
            &[state="half"] {
                top: 1.6rem;
            }

            &[state="peek"] {
                top: auto;
                height: 14rem;
            }

            &[is-dragging] {
                transform: none !important;
            }
        }
    }

    .el-sheet__handle {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 3.2rem;
        padding-top: 0.6rem;
        width: 100%;
        flex-shrink: 0;
        touch-action: none;
        cursor: grab;

        @include mixins.respond-from(900px) {
            display: none;
        }
    }

    .el-sheet__grip {
        width: 4.8rem;
        height: 4px;
        border-radius: 2px;
        background: var(--c-handle);
    }

    .el-sheet__body {
        flex: 1;
        overflow-y: auto;
        overscroll-behavior: contain;
        padding: 0 var(--gutter) 4rem;

        @include mixins.respond-from(900px) {
            padding-top: 2rem;
        }
    }

    .el-sheet[state="peek"] .el-sheet__body {
        overflow: hidden;
    }
</style>
