<script setup>
    // The explore mode: a map with the route, a timeline to sail along it, the net that fills up,
    // and a dive into the water column at every station. Also the plugin `deepdive` of the content repo.
    import { computed, onMounted, ref, shallowRef } from 'vue';
    import { formatDate } from '@/services/format.js';
    import ElExplorerDive from './el-explorer-dive.vue';
    import ElExplorerMap from './el-explorer-map.vue';
    import ElExplorerNet from './el-explorer-net.vue';
    import ElExplorerSpecimen from './el-explorer-specimen.vue';
    import ElExplorerTimeline from './el-explorer-timeline.vue';
    import { loadExplorer, stationIndexAt } from './data.js';

    // Keeps the ship in the part of the map above the timeline
    const MAP_PADDING = {
        top : 40,
        right : 0,
        bottom : 150,
        left : 0
    };

    const props = defineProps({
        // A station number, as in [[Diep onder het schip#99]], dives at that station
        argument : {
            type : String,
            default : null
        },
        fullscreen : {
            type : Boolean,
            default : false
        }
    });

    const map = ref(null);
    const data = shallowRef(null);
    const error = ref(null);
    // Kilometres along the route
    const position = ref(0);
    // sail: on the map with the timeline; flying: on the way to a station; dive: under water
    const phase = ref('sail');
    const diveStation = shallowRef(null);
    const selectedSpecimen = shallowRef(null);
    const isNetOpen = ref(false);

    const currentStation = computed(() => data.value?.stations[stationIndexAt(data.value.stations, position.value)] ?? null);
    const dateLabel = computed(() => formatDate(currentStation.value?.datum ?? '1899-03-01'));

    async function dive(station) {
        if (phase.value !== 'sail') {
            return;
        }

        selectedSpecimen.value = null;
        isNetOpen.value = false;
        position.value = station.km;
        phase.value = 'flying';
        await map.value.dive(station);
        diveStation.value = station;
        phase.value = 'dive';
    }

    async function onSurface() {
        diveStation.value = null;
        phase.value = 'flying';
        await map.value.surface();
        phase.value = 'sail';
    }

    function selectSpecimen(specimen) {
        isNetOpen.value = false;
        selectedSpecimen.value = specimen;
    }

    onMounted(async () => {
        try {
            data.value = await loadExplorer();
            position.value = data.value.stations[0].km;

            const station = props.argument ? data.value.stations.find((item) => item.nummer === props.argument) : null;

            if (station) {
                // Let the map settle on the route before flying off
                setTimeout(() => dive(station), 600);
            }
        } catch (loadError) {
            console.error(loadError);
            error.value = loadError.message;
        }
    });
</script>

<template>
    <div
        class="el-explorer"
        v-bind:is-fullscreen="fullscreen ? '' : null"
        v-bind:phase="phase">
        <p
            v-if="error"
            class="message">De gegevens konden niet geladen worden.</p>

        <p
            v-else-if="!data"
            class="message">Het schip wordt klaargemaakt…</p>

        <template v-else>
            <el-explorer-map
                ref="map"
                v-bind:stations="data.stations"
                v-bind:line="data.line"
                v-bind:position="position"
                v-bind:padding="MAP_PADDING"
                v-on:select="dive($event)" />

            <p
                class="date"
                aria-live="polite">{{ dateLabel }}</p>

            <el-explorer-timeline
                class="timeline"
                v-bind:stations="data.stations"
                v-bind:line="data.line"
                v-bind:length="data.length"
                v-bind:position="position"
                v-bind:total="data.total"
                v-on:update:position="position = $event"
                v-on:select="dive($event)"
                v-on:open-net="isNetOpen = true" />

            <el-explorer-dive
                v-if="diveStation"
                v-bind:key="diveStation.index"
                v-bind:station="diveStation"
                v-bind:wikidata-url="data.wikidataUrl"
                v-on:surface="onSurface()"
                v-on:select-specimen="selectSpecimen($event)" />

            <el-explorer-net
                v-if="isNetOpen"
                v-bind:stations="data.stations"
                v-bind:position="position"
                v-bind:total="data.total"
                v-on:close="isNetOpen = false"
                v-on:select-station="dive($event)"
                v-on:select-specimen="selectSpecimen($event)" />

            <el-explorer-specimen
                v-if="selectedSpecimen"
                v-bind:key="selectedSpecimen.id"
                v-bind:specimen="selectedSpecimen"
                v-on:close="selectedSpecimen = null" />
        </template>
    </div>
</template>

<style lang="scss" scoped>
    .el-explorer {
        position: relative;
        height: 56rem;
        overflow: hidden;
        background: var(--c-sea);
        color: var(--c-ink);

        &[is-fullscreen] {
            height: 100%;
        }
    }

    .message {
        position: absolute;
        inset: 0;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-style: italic;
        color: var(--c-paper);
    }

    // The date sits on the map itself, not in a box
    .date {
        position: absolute;
        top: 1.6rem;
        left: 1.6rem;
        z-index: 1;
        margin: 0;
        font-family: var(--font-header);
        font-size: 2.6rem;
        color: var(--c-paper);
        text-shadow: 0 1px 3px rgba(8, 26, 44, 0.7), 0 0 12px rgba(8, 26, 44, 0.35);
        pointer-events: none;
        transition: opacity 0.4s;

        [phase="flying"] > &,
        [phase="dive"] > & {
            opacity: 0;
        }
    }

    .timeline {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 2;
        transition: transform 0.5s cubic-bezier(0.2, 0.7, 0.2, 1), opacity 0.3s;

        [phase="flying"] > &,
        [phase="dive"] > & {
            transform: translateY(100%);
            opacity: 0;
            pointer-events: none;
        }
    }
</style>
