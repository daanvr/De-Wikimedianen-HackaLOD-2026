<script setup>
    // Marks a specimen on which a species was described: alone (holotype and the like)
    // or together with others (syntype). Small on tiles, with a text on the specimen page.
    defineProps({
        size : {
            type : Number,
            default : 18
        }
    });
</script>

<template>
    <span
        class="el-explorer-badge"
        role="img"
        aria-label="Naamdrager: op dit exemplaar is de soort beschreven"
        v-bind:style="{ width : `${size}px`, height : `${size}px` }">
        <svg
            viewBox="0 0 24 24"
            aria-hidden="true">
            <path
                class="seal"
                d="M12 1.5l2.3 1.7 2.8-.2 1 2.6 2.6 1-.2 2.8 1.7 2.3-1.7 2.3.2 2.8-2.6 1-1 2.6-2.8-.2L12 22.5l-2.3-1.7-2.8.2-1-2.6-2.6-1 .2-2.8L1.8 12l1.7-2.3-.2-2.8 2.6-1 1-2.6 2.8.2z" />
            <path
                class="star"
                d="M12 6.8l1.6 3.3 3.6.5-2.6 2.5.6 3.6L12 15l-3.2 1.7.6-3.6-2.6-2.5 3.6-.5z" />
        </svg>
    </span>
</template>

<style lang="scss" scoped>
    .el-explorer-badge {
        display: inline-flex;
        flex: none;
        filter: drop-shadow(0 1px 1.5px rgba(8, 26, 44, 0.4));

        svg {
            width: 100%;
            height: 100%;
        }
    }

    .seal {
        fill: #B8862E;
        stroke: #FBF8F1;
        stroke-width: 1.2;
    }

    .star {
        fill: #FBF8F1;
    }
</style>
