<script setup>
    // A piece of text with a tooltip that says where it comes from: the field of the record
    // (term) and a short explanation. Shows on hover, and on focus so a tap works on a phone.
    import { useId } from 'vue';

    defineProps({
        term : {
            type : String,
            default : null
        },

        text : {
            type : String,
            required : true
        }
    });

    const id = useId();
</script>

<template>
    <span
        class="el-explorer-term"
        tabindex="0"
        v-bind:aria-describedby="id">
        <slot />
        <span
            v-bind:id="id"
            class="tip"
            role="tooltip">
            <code
                v-if="term"
                class="tip__term">{{ term }}</code>
            <span class="tip__text">{{ text }}</span>
        </span>
    </span>
</template>

<style lang="scss" scoped>
    .el-explorer-term {
        position: relative;
        align-self: flex-start;
        text-decoration: underline dotted var(--c-frame);
        text-underline-offset: 0.3em;
        cursor: help;
        outline: none;

        &:hover,
        &:focus-visible,
        &:focus {
            text-decoration-color: var(--c-ink-soft);
        }
    }

    .tip {
        position: absolute;
        left: 0;
        top: calc(100% + 0.6rem);
        z-index: 2;
        display: none;
        flex-direction: column;
        gap: 0.4rem;
        width: max-content;
        max-width: min(30rem, 70vw);
        padding: 0.8rem 1rem;
        border-radius: 6px;
        background: var(--c-marine);
        box-shadow: var(--shadow-float);
        color: var(--c-paper);
        font-family: var(--font-text);
        font-size: 1.3rem;
        line-height: 1.4;
        letter-spacing: normal;
        text-transform: none;
        white-space: normal;

        .el-explorer-term:hover > &,
        .el-explorer-term:focus > & {
            display: flex;
        }
    }

    .tip__term {
        font-size: 1.2rem;
        opacity: 0.8;
    }
</style>