<script setup>
    defineProps({
        src : {
            type : String,
            required : true
        },
        alt : {
            type : String,
            default : ''
        },
        // HTML, from the markdown of the body
        caption : {
            type : String,
            default : null
        }
    });
</script>

<template>
    <figure class="el-zoomed-image">
        <img
            class="image"
            v-bind:src="src"
            v-bind:alt="alt">

        <figcaption
            v-if="caption"
            class="caption"
            v-on:click.stop
            v-html="caption"></figcaption>
    </figure>
</template>

<style lang="scss" scoped>
    .el-zoomed-image {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1.2rem;
        width: 100%;
        height: 100%;
        margin: 0;
    }

    .image {
        min-height: 0;
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .caption {
        max-width: 60rem;
        font-size: 1.6rem;
        line-height: 1.4;
        font-style: italic;
        text-align: center;
        color: var(--c-paper);

        :deep(a) {
            color: var(--c-terracotta-light);
        }
    }
</style>
