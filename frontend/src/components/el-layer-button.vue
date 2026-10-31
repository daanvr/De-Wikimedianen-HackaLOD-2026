<script setup>
    import { computed, inject, onBeforeUnmount, ref } from 'vue';
    import ElMapButton from '@/components/el-map-button.vue';

    // Every tap moves on to the next base map, in this order
    const ORDER = ['historic', 'historicHalf', 'chart', 'satellite'];
    const NOTE_MS = 1600;

    const t = inject('t');

    const props = defineProps({
        layer : {
            type : String,
            default : 'historic'
        }
    });

    const emit = defineEmits(['change']);

    const isNoteVisible = ref(false);
    const label = computed(() => `${t('map_layer')}: ${t(`map_layer_${props.layer}`)}`);

    let noteTimer = null;

    function next() {
        const index = ORDER.indexOf(props.layer);

        emit('change', ORDER[(index + 1) % ORDER.length]);
        isNoteVisible.value = true;
        clearTimeout(noteTimer);
        noteTimer = setTimeout(() => {
            isNoteVisible.value = false;
        }, NOTE_MS);
    }

    onBeforeUnmount(() => {
        clearTimeout(noteTimer);
    });
</script>

<template>
    <div class="el-layer-button">
        <p
            class="note"
            v-bind:is-visible="isNoteVisible ? '' : null"
            aria-live="polite">
            {{ t(`map_layer_${layer}`) }}
        </p>

        <el-map-button
            icon="layers"
            v-bind:label="label"
            v-on:click="next()" />
    </div>
</template>

<style lang="scss" scoped>
    .el-layer-button {
        position: relative;
        pointer-events: none;
    }

    .note {
        position: absolute;
        top: 50%;
        right: calc(100% + 0.8rem);
        padding: 0.6rem 1.2rem;
        border-radius: 3px;
        background: rgba(22, 58, 92, 0.88);
        color: var(--c-paper);
        font-family: var(--font-header);
        font-style: italic;
        font-size: 1.4rem;
        white-space: nowrap;
        opacity: 0;
        transform: translate(0.4rem, -50%);
        transition: opacity 0.2s ease, transform 0.2s ease;

        &[is-visible] {
            opacity: 1;
            transform: translate(0, -50%);
        }
    }
</style>
