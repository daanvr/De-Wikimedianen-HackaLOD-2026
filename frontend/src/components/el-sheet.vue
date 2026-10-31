<script setup>
    import { ref } from 'vue';

    defineProps({
        // peek: folded in (mobile, while the boat sails), half: the lower half (mobile),
        // screen: the whole screen on mobile. On desktop, every state is the same
        // panel on the left, so the library lies where the chapter was.
        state : {
            type : String,
            default : 'half'
        }
    });

    const body = ref(null);

    defineExpose({
        scrollPosition : () => body.value?.scrollTop ?? 0,
        scrollTo : (top) => body.value?.scrollTo({
            top
        }),
        scrollToTop : () => body.value?.scrollTo({
            top : 0
        })
    });
</script>

<template>
    <section
        class="el-sheet"
        v-bind:state="state">
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
        // Clips the scrolling body, whose scrollbar would otherwise cover the rounded corners
        overflow: hidden;
        pointer-events: auto;
        transition: top 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
        z-index: 20;

        &[state="peek"] {
            top: calc(100% - 14rem);
        }

        @include mixins.respond-from(900px) {
            top: 1.6rem;
            bottom: 1.6rem;
            left: 1.6rem;
            right: auto;
            width: var(--sheet-width);
            border-radius: 12px;
            box-shadow: var(--shadow-card);

            &[state="peek"] {
                top: 1.6rem;
            }
        }

        @include mixins.respond-until(900px) {
            &[state="screen"] {
                inset: 0;
                border-radius: 0;
                box-shadow: none;
                transition: none;
            }
        }
    }

    .el-sheet__body {
        flex: 1;
        overflow-y: auto;
        overscroll-behavior: contain;
        padding: 1.6rem var(--gutter) 4rem;

        @include mixins.respond-from(900px) {
            padding-top: 2rem;
        }

        @include mixins.respond-until(900px) {
            [state="peek"] > & {
                overflow: hidden;
            }
        }
    }
</style>
