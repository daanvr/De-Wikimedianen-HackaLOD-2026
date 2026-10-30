<script setup>
    import { computed } from 'vue';

    // Placeholder icons; the hand drawn set replaces these paths later
    const ICONS = {
        anchor : '<circle cx="12" cy="5" r="2"/><path d="M12 7v13M8.5 10h7M5 13.5a7 7 0 0 0 14 0M5 13.5l-1.5 1.5M5 13.5l1.8 1M19 13.5l1.5 1.5M19 13.5l-1.8 1"/>',
        arrowLeft : '<path d="M19 12H5M11 6l-6 6 6 6"/>',
        arrowRight : '<path d="M5 12h14M13 6l6 6-6 6"/>',
        book : '<path d="M5 4.5h11a2 2 0 0 1 2 2V20H7a2 2 0 0 1-2-2z"/><path d="M5 18a2 2 0 0 1 2-2h11"/><path d="M9 8.5h6M9 11.5h4"/>',
        chapter : '<path d="M17 20H7a3 3 0 0 1-3-3v-1h10v1a3 3 0 0 0 3 3 3 3 0 0 0 3-3V5a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v11"/><path d="M10 8h6M10 11h4"/>',
        chevronDown : '<path d="M6 9l6 6 6-6"/>',
        chevronRight : '<path d="M9 6l6 6-6 6"/>',
        close : '<path d="M6 6l12 12M18 6L6 18"/>',
        explore : '<circle cx="12" cy="12" r="5.5"/><circle cx="12" cy="12" r="1.6"/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4M5.3 5.3l2.8 2.8M15.9 15.9l2.8 2.8M5.3 18.7l2.8-2.8M15.9 8.1l2.8-2.8"/>',
        external : '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
        fullscreen : '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
        image : '<rect x="3.5" y="5" width="17" height="14" rx="1"/><circle cx="9" cy="10" r="1.6"/><path d="M4 17l5-5 4 4 2.5-2.5L20 18"/>',
        info : '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5"/><circle cx="12" cy="7.8" r="0.6" fill="currentColor"/>',
        item : '<path d="M5 8l7-4 7 4v8l-7 4-7-4z"/><path d="M5 8l7 4 7-4M12 12v8"/>',
        list : '<path d="M9 6.5h11M9 12h11M9 17.5h11"/><path d="M4 6.5h1.5M4 12h1.5M4 17.5h1.5"/>',
        location : '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
        menu : '<path d="M4.5 7h15M4.5 12h15M4.5 17h15"/>',
        person : '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-4 3.1-6.5 7-6.5s7 2.5 7 6.5"/>',
        search : '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
        specimen : '<path d="M12 12.5a1.2 1.2 0 1 1 1.2 1.2A2.6 2.6 0 0 1 10.6 11a4 4 0 0 1 4-4 5.3 5.3 0 0 1 5.3 5.3 6.7 6.7 0 0 1-6.7 6.7A8 8 0 0 1 5.2 11 9.3 9.3 0 0 1 9 3.6"/>',
        station : '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="1.5"/><path d="M12 2.5v3.5M12 18v3.5M2.5 12H6M18 12h3.5"/>'
    };

    const props = defineProps({
        name : {
            type : String,
            required : true
        },
        size : {
            type : Number,
            default : 24
        },
        strokeWidth : {
            type : Number,
            default : 1.7
        }
    });

    const paths = computed(() => ICONS[props.name] ?? ICONS.info);
</script>

<template>
    <svg
        class="el-icon"
        v-bind:width="size"
        v-bind:height="size"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        v-bind:stroke-width="strokeWidth"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
        v-html="paths"></svg>
</template>

<style lang="scss" scoped>
    .el-icon {
        flex-shrink: 0;
        display: inline-block;
    }
</style>
