<script setup>
    // Says how close an illustration is to the specimen. On a small round photo only a related
    // species gets a mark ("verwant"); large, it always shows that the photo is an illustration.
    defineProps({
        illustration : {
            type : Object,
            required : true
        },
        large : {
            type : Boolean,
            default : false
        }
    });
</script>

<template>
    <span
        v-if="large || illustration.isRelated"
        class="el-explorer-likeness"
        v-bind:level="illustration.level"
        v-bind:is-large="large ? '' : null">
        <template v-if="large">Illustratie · {{ illustration.badge }}</template>
        <template v-else>verwant</template>
    </span>
</template>

<style lang="scss" scoped>
    .el-explorer-likeness {
        display: inline-block;
        padding: 0.1rem 0.6rem;
        border-radius: 999px;
        background: var(--c-paper);
        color: var(--c-ink);
        box-shadow: 0 1px 3px rgba(10, 30, 50, 0.35);
        font-family: var(--font-header);
        font-size: 1.05rem;
        letter-spacing: 0.06em;
        line-height: 1.5;
        white-space: nowrap;

        &[level="verwante-soort"] {
            background: var(--c-terracotta);
            color: var(--c-paper);
        }

        &[is-large] {
            padding: 0.3rem 1rem;
            font-size: 1.3rem;
            letter-spacing: 0.08em;
        }
    }
</style>
