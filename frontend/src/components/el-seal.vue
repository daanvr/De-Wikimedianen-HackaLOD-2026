<script setup>
    const props = defineProps({
        size : {
            type : Number,
            default : 60
        }
    });
</script>

<template>
    <!-- Placeholder logo: the final seal is drawn by the team -->
    <svg
        class="el-seal"
        v-bind:width="size"
        v-bind:height="size"
        viewBox="0 0 76 76"
        role="img"
        aria-label="Logo van de Siboga-Expeditie">
        <defs>
            <path
                id="seal-arc"
                d="M38,38 m-27,0 a27,27 0 1,1 54,0 a27,27 0 1,1 -54,0" />
        </defs>
        <circle
            cx="38"
            cy="38"
            r="36"
            fill="none"
            stroke="#163A5C"
            stroke-width="1.6" />
        <circle
            cx="38"
            cy="38"
            r="21"
            fill="#F2DCCD"
            stroke="#163A5C"
            stroke-width="1" />
        <text
            class="el-seal__text"
            font-size="7.4"
            letter-spacing="1.6"
            fill="#163A5C">
            <textPath href="#seal-arc">SIBOGA · NEDERLANDS-INDIË · 1899–1900 ·</textPath>
        </text>
        <g
            transform="translate(26,26)"
            fill="none"
            stroke="#A9512F"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round">
            <circle
                cx="12"
                cy="5"
                r="2" />
            <path d="M12 7v13M8.5 10h7M5 13.5a7 7 0 0 0 14 0M5 13.5l-1.5 1.5M5 13.5l1.8 1M19 13.5l1.5 1.5M19 13.5l-1.8 1" />
        </g>
    </svg>
</template>

<style lang="scss" scoped>
    .el-seal {
        flex-shrink: 0;
    }

    .el-seal__text {
        font-family: var(--font-header);
    }
</style>
