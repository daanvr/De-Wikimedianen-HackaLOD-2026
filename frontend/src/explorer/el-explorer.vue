<script setup>
    // The explore mode: a map with the route, a timeline to sail along it, the net that fills up,
    // and a dive into the water column at every station. Also the plugin `deepdive` of the content repo.
    import { computed, onMounted, ref, shallowRef, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
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

    const route = useRoute();
    const router = useRouter();

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
    // What is open (station, net, specimen) when the explorer is not full screen, as in a chapter
    const localQuery = ref({});

    // Full screen, every open layer is a step in the browser history, so the back button closes it.
    // In a chapter the explorer keeps it to itself: the page must not jump or fill the history.
    const usesHistory = computed(() => props.fullscreen);
    const query = computed(() => usesHistory.value ? route.query : localQuery.value);
    const currentStation = computed(() => data.value?.stations[stationIndexAt(data.value.stations, position.value)] ?? null);
    // Full screen the ship sets sail by itself, unless a link asks for a station or specimen straight away
    const autoplay = usesHistory.value && !route.query.station && !route.query.specimen;
    const dateLabel = computed(() => formatDate(currentStation.value?.datum ?? '1899-03-01'));

    // The history position when the explorer opened; anything after it was opened here
    let basePosition = null;
    let isSyncing = false;
    let needsSync = false;

    // Closes the top layer: a step back in the history if this explorer made it, otherwise in place
    function back(fallback) {
        if (!usesHistory.value) {
            localQuery.value = fallback;
            return;
        }

        if ((window.history.state?.position ?? 0) > basePosition) {
            router.back();
        } else {
            router.replace({
                query : fallback
            });
        }
    }

    async function dive(station) {
        selectedSpecimen.value = null;
        position.value = station.km;
        phase.value = 'flying';
        await map.value.dive(station);
        diveStation.value = station;
        phase.value = 'dive';
    }

    function open(next) {
        if (usesHistory.value) {
            router.push({
                query : next
            });
        } else {
            localQuery.value = next;
        }
    }

    function openNet() {
        open({
            ...query.value,
            net : '1'
        });
    }

    function openStation(station) {
        if (phase.value === 'sail' || isNetOpen.value) {
            open({
                station : station.nummer
            });
        }
    }

    function openSpecimen(specimen) {
        open({
            ...query.value,
            specimen : String(specimen.id)
        });
    }

    function closeNet() {
        const { net, ...rest } = query.value;

        back(rest);
    }

    function closeSpecimen() {
        const { specimen, ...rest } = query.value;

        back(rest);
    }

    function surface() {
        back({});
    }

    async function surfaceNow() {
        diveStation.value = null;
        phase.value = 'flying';
        await map.value.surface();
        phase.value = 'sail';
    }

    // Brings what is open in line with the query; a dive or surfacing finishes before the next change
    async function sync() {
        if (!data.value || !map.value) {
            return;
        }

        if (isSyncing) {
            needsSync = true;
            return;
        }

        isSyncing = true;

        do {
            needsSync = false;

            const wanted = query.value;
            const station = wanted.station ? data.value.stations.find((item) => item.nummer === wanted.station) ?? null : null;
            const specimenId = Number(wanted.specimen);

            isNetOpen.value = wanted.net === '1';
            selectedSpecimen.value = wanted.specimen ? data.value.specimens.find((item) => item.id === specimenId) ?? null : null;

            if (diveStation.value && diveStation.value !== station) {
                await surfaceNow();
            }

            if (station && diveStation.value !== station) {
                await dive(station);
                // A specimen in the query stays open over the dive
                selectedSpecimen.value = wanted.specimen ? data.value.specimens.find((item) => item.id === specimenId) ?? null : null;
            }
        } while (needsSync);

        isSyncing = false;
    }

    watch(query, sync);

    onMounted(async () => {
        basePosition = window.history.state?.position ?? 0;

        try {
            data.value = await loadExplorer();
            position.value = data.value.stations[0].km;

            const station = props.argument ? data.value.stations.find((item) => item.nummer === props.argument) : null;

            // Let the map settle on the route before flying off
            setTimeout(() => {
                if (station && !query.value.station) {
                    localQuery.value = {
                        station : station.nummer
                    };
                } else {
                    sync();
                }
            }, 600);
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
                v-on:select="openStation($event)" />

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
                v-bind:autoplay="autoplay"
                v-on:update:position="position = $event"
                v-on:select="openStation($event)"
                v-on:open-net="openNet()" />

            <el-explorer-dive
                v-if="diveStation"
                v-bind:key="diveStation.index"
                v-bind:station="diveStation"
                v-bind:wikidata-url="data.wikidataUrl"
                v-on:surface="surface()"
                v-on:select-specimen="openSpecimen($event)" />

            <el-explorer-net
                v-if="isNetOpen"
                v-bind:stations="data.stations"
                v-bind:position="position"
                v-bind:total="data.total"
                v-on:close="closeNet()"
                v-on:select-station="openStation($event)"
                v-on:select-specimen="openSpecimen($event)" />

            <el-explorer-specimen
                v-if="selectedSpecimen"
                v-bind:key="selectedSpecimen.id"
                v-bind:specimen="selectedSpecimen"
                v-on:close="closeSpecimen()" />
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
