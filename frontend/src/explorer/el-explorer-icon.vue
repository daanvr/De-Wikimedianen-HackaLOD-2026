<script setup>
    import { computed } from 'vue';
    import { groupIcon } from './groups.js';

    const props = defineProps({
        group : {
            type : String,
            required : true
        },
        size : {
            type : Number,
            default : 20
        }
    });

    const path = computed(() => groupIcon(props.group));
</script>

<template>
    <svg
        class="el-explorer-icon"
        viewBox="0 0 24 24"
        v-bind:width="size"
        v-bind:height="size"
        aria-hidden="true">
        <path v-bind:d="path" />
    </svg>
</template>

<style lang="scss" scoped>
    .el-explorer-icon {
        flex: none;
        fill: none;
        stroke: currentColor;
        stroke-width: 1.5;
        stroke-linecap: round;
        stroke-linejoin: round;
    }
</style>
