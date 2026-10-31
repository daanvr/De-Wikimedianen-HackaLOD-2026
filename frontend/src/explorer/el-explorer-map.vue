<script setup>
    import maplibregl from 'maplibre-gl';
    import { computed, inject, onBeforeUnmount, onMounted, ref, toRaw, watch } from 'vue';
    import { LAND_LABELS, SEA_LABELS, limitZoom, seaChartLayers, seaChartSources } from '@/services/sea-chart.js';
    import { lineIndexAt, pointAt, stationIndexAt } from './data.js';

    const MAX_ZOOM = 12;
    const FOLLOW_ZOOM = 6.4;
    // The dive from the dive prototype: fly over and tilt, then go under at a steep angle
    const FOCUS_ZOOM = 10.4;
    const FOCUS_PITCH = 45;
    const DIVE_ZOOM = 13.4;
    const DIVE_PITCH = 80;
    const TOP_STATIONS = 5;
    // Zoomed out further than this, the photos of the stations would cover the whole map
    const PHOTO_MIN_ZOOM = 4.5;
    // The compass lies down with the camera, but only partly, so it stays readable
    const COMPASS_TILT = 0.6;
    const EMPTY = {
        type : 'FeatureCollection',
        features : []
    };

    const store = inject('store');

    const emit = defineEmits(['select']);

    const props = defineProps({
        stations : {
            type : Array,
            required : true
        },
        line : {
            type : Array,
            required : true
        },
        // Kilometres along the route
        position : {
            type : Number,
            default : 0
        },
        padding : {
            type : Object,
            default : () => ({
                top : 0,
                right : 0,
                bottom : 0,
                left : 0
            })
        }
    });

    const root = ref(null);
    const container = ref(null);
    const camera = ref({
        pitch : 0,
        bearing : 0,
        isDiving : false
    });

    // Only when the camera is tilted or the map turned; under water the dive has the screen
    const isCompassVisible = computed(() => !camera.value.isDiving && (camera.value.pitch >= 0.5 || Math.abs(camera.value.bearing) >= 0.5));
    // North of the compass points to north on the map
    const compassTransform = computed(() => `rotateX(${camera.value.pitch * COMPASS_TILT}deg) rotateZ(${-camera.value.bearing}deg)`);

    let map = null;
    let boat = null;
    let frame = null;
    let isFollowing = true;
    let isDiving = false;
    let target = null;
    let visitedUpTo = -1;
    let trailKm = -1;
    let topMarkers = [];
    let photoMarkers = [];
    let labels = [];
    let resizeObserver = null;

    function buildStyle() {
        const layers = toRaw(store.mapLayers);
        const visited = ['boolean', ['feature-state', 'visited'], false];

        return {
            version : 8,
            sources : {
                ...seaChartSources(layers),
                route : {
                    type : 'geojson',
                    data : lineFeature(props.line.map((point) => [point[1], point[2]]))
                },
                trail : {
                    type : 'geojson',
                    data : EMPTY
                },
                stations : {
                    type : 'geojson',
                    data : stationFeatures(),
                    // Feature id 0 does not take feature state, so ids start at 1
                    promoteId : 'fid'
                }
            },
            layers : [
                ...seaChartLayers(),
                {
                    id : 'route',
                    type : 'line',
                    source : 'route',
                    paint : {
                        'line-color' : '#FBF8F1',
                        'line-width' : 1.2,
                        'line-opacity' : 0.35,
                        'line-dasharray' : [2, 3]
                    }
                },
                {
                    id : 'trail',
                    type : 'line',
                    source : 'trail',
                    paint : {
                        'line-color' : '#FBF8F1',
                        'line-width' : 1.6,
                        'line-opacity' : 0.95,
                        'line-dasharray' : [2, 3]
                    }
                },
                {
                    id : 'stations',
                    type : 'circle',
                    source : 'stations',
                    filter : ['==', ['get', 'count'], 0],
                    paint : {
                        'circle-radius' : ['interpolate', ['linear'], ['zoom'], 4, 1.6, 10, 4],
                        'circle-color' : ['case', visited, '#FBF8F1', 'rgba(251, 248, 241, 0)'],
                        'circle-stroke-color' : '#FBF8F1',
                        'circle-stroke-width' : 0.8,
                        'circle-stroke-opacity' : ['case', visited, 1, 0.55]
                    }
                },
                {
                    id : 'stations-finds',
                    type : 'circle',
                    source : 'stations',
                    filter : ['>', ['get', 'count'], 0],
                    paint : {
                        'circle-radius' : [
                            'interpolate',
                            ['linear'],
                            ['zoom'],
                            4,
                            ['+', 2.5, ['*', 1.5, ['sqrt', ['get', 'count']]]],
                            10,
                            ['+', 5, ['*', 3, ['sqrt', ['get', 'count']]]]
                        ],
                        'circle-color' : ['case', visited, '#D88A63', '#1F5280'],
                        'circle-stroke-color' : ['case', visited, '#FBF8F1', '#D88A63'],
                        'circle-stroke-width' : 1.4
                    }
                }
            ]
        };
    }

    function createBoat() {
        const element = document.createElement('div');

        element.className = 'boat';
        element.setAttribute('aria-hidden', 'true');
        element.innerHTML = `
            <svg width="72" height="36" viewBox="-46 -23 92 46">
                <path d="M-27,0 L-44,-7 M-27,0 L-44,7" stroke="#FBF8F1" stroke-width="1.4" fill="none" opacity="0.7"/>
                <path d="M-25,0 C-21,-6 8,-7 26,0 C8,7 -21,6 -25,0 Z" fill="#FBF8F1" stroke="#1B2433" stroke-width="1.3"/>
                <path d="M-9,-6 L-9,6 M8,-5 L8,5" stroke="#1B2433" stroke-width="1.3" fill="none"/>
                <circle r="2.4" fill="#A9512F"/>
            </svg>`;

        return new maplibregl.Marker({
            element,
            rotationAlignment : 'map',
            pitchAlignment : 'map'
        });
    }

    // The names of the main map; they stay flat on the screen, so they go when the map tilts
    function createLabels() {
        const kinds = [
            [SEA_LABELS, 'sea'],
            [LAND_LABELS, 'land']
        ];

        labels = kinds.flatMap(([list, kind]) => list.map((label) => {
            const element = document.createElement('div');

            element.className = `map-label map-label--${kind}`;
            element.textContent = label.text;

            return new maplibregl.Marker({
                element,
                anchor : 'center'
            }).setLngLat([label.lon, label.lat]).addTo(map);
        }));
    }

    // A round photo above the stations that have one on Wikidata, as an invitation to tap
    function createPhotoMarkers() {
        photoMarkers = props.stations
            .filter((station) => station.photo)
            .map((station) => {
                const element = document.createElement('button');
                const image = document.createElement('img');

                element.type = 'button';
                element.className = 'photo-marker';
                element.title = `Station ${station.nummer}: ${station.photo.caption}`;
                element.setAttribute('aria-label', `Station ${station.nummer}, foto: ${station.photo.caption}`);
                image.src = station.photo.thumb;
                image.alt = '';
                image.loading = 'lazy';
                element.appendChild(image);
                element.addEventListener('click', () => emit('select', station));

                return new maplibregl.Marker({
                    element,
                    anchor : 'bottom',
                    offset : [0, -4]
                }).setLngLat([station.lon, station.lat]).addTo(map);
            });
    }

    function createTopMarkers() {
        const top = [...props.stations]
            .filter((station) => station.specimens.length)
            .sort((a, b) => b.specimens.length - a.specimens.length)
            .slice(0, TOP_STATIONS);

        topMarkers = top.map((station) => {
            const element = document.createElement('button');

            element.type = 'button';
            element.className = 'top-station';
            element.innerHTML = `<strong>${station.specimens.length}</strong><span>st. ${station.nummer}</span>`;
            element.setAttribute('aria-label', `Station ${station.nummer}: ${station.specimens.length} specimens`);
            element.addEventListener('click', () => emit('select', station));

            return new maplibregl.Marker({
                element,
                anchor : 'left',
                offset : [10, 0]
            }).setLngLat([station.lon, station.lat]).addTo(map);
        });
    }

    // Flies to the ship and tilts, then goes under; resolves when the camera is under water
    async function dive(station) {
        if (!map) {
            return;
        }

        const ship = pointAt(props.line, station.km);
        const height = container.value.clientHeight;

        isDiving = true;
        stopFollowing();
        setInteractive(false);
        updateCamera();
        boat.setLngLat([ship.lon, ship.lat]);

        await move('flyTo', {
            center : [ship.lon, ship.lat],
            zoom : FOCUS_ZOOM,
            pitch : FOCUS_PITCH,
            bearing : -10,
            duration : 2200,
            essential : true,
            padding : {
                ...props.padding,
                bottom : Math.round(height * 0.3)
            }
        });

        setMarkersHidden(true);
        map.easeTo({
            center : [ship.lon, ship.lat],
            zoom : DIVE_ZOOM,
            pitch : DIVE_PITCH,
            bearing : map.getBearing() + 12,
            duration : 1900,
            padding : {
                top : 0,
                right : 0,
                bottom : 0,
                left : 0
            }
        });
    }

    function isLevel() {
        return map.getPitch() < 0.5 && Math.abs(map.getBearing()) < 0.5;
    }

    function move(method, options) {
        return new Promise((resolve) => {
            map.once('moveend', resolve);
            map[method](options);
        });
    }

    // Under water the drawn ship takes over from the marker; the labels go too
    function setMarkersHidden(hidden) {
        for (const marker of [boat, ...topMarkers, ...photoMarkers, ...labels]) {
            marker.getElement().style.visibility = hidden ? 'hidden' : '';
        }
    }

    // Straight down with north up; the map stays where it is
    async function resetNorth() {
        // The follow loop would stop the ease halfway
        cancelAnimationFrame(frame);
        frame = null;
        await move('easeTo', {
            pitch : 0,
            bearing : 0,
            duration : 700
        });

        if (isFollowing) {
            startFollowing();
        }
    }

    function setInteractive(isInteractive) {
        const handlers = [map.boxZoom, map.doubleClickZoom, map.dragPan, map.keyboard, map.scrollZoom, map.touchZoomRotate];

        for (const handler of [...handlers, map.dragRotate, map.touchPitch]) {
            if (isInteractive) {
                handler.enable();
            } else {
                handler.disable();
            }
        }
    }

    // Back up from under water to following the ship. The map ignores the hand meanwhile: a scroll
    // that brought you up would otherwise carry on into the map and stop it halfway, still tilted.
    async function surface() {
        if (!map) {
            return;
        }

        setMarkersHidden(false);
        await move('easeTo', {
            center : target ? [target.lon, target.lat] : map.getCenter(),
            zoom : FOLLOW_ZOOM,
            pitch : 0,
            bearing : 0,
            duration : 1600,
            padding : props.padding
        });

        if (!isLevel()) {
            map.jumpTo({
                pitch : 0,
                bearing : 0
            });
        }

        isDiving = false;
        isFollowing = true;
        setInteractive(true);
        updateCamera();
    }

    function follow() {
        frame = null;

        if (!map || !isFollowing || !target || isDiving) {
            return;
        }

        const center = map.getCenter();
        const dx = target.lon - center.lng;
        const dy = target.lat - center.lat;

        if (Math.abs(dx) + Math.abs(dy) < 0.0005) {
            return;
        }

        map.jumpTo({
            center : [center.lng + dx * 0.16, center.lat + dy * 0.16]
        });
        frame = requestAnimationFrame(follow);
    }

    function lineFeature(coordinates) {
        return {
            type : 'Feature',
            properties : {},
            geometry : {
                type : 'LineString',
                coordinates
            }
        };
    }

    function stationFeatures() {
        return {
            type : 'FeatureCollection',
            features : props.stations.map((station) => ({
                type : 'Feature',
                properties : {
                    index : station.index,
                    fid : station.index + 1,
                    count : station.specimens.length
                },
                geometry : {
                    type : 'Point',
                    coordinates : [station.lon, station.lat]
                }
            }))
        };
    }

    function startFollowing() {
        if (!frame) {
            frame = requestAnimationFrame(follow);
        }
    }

    function stopFollowing() {
        isFollowing = false;
        cancelAnimationFrame(frame);
        frame = null;
    }

    function updatePhotoZoom() {
        root.value?.toggleAttribute('is-far', map.getZoom() < PHOTO_MIN_ZOOM);
    }

    function updateCamera() {
        const pitch = Math.round(map.getPitch() * 10) / 10;
        const bearing = Math.round(map.getBearing() * 10) / 10;
        const current = camera.value;

        if (pitch !== current.pitch || bearing !== current.bearing || isDiving !== current.isDiving) {
            camera.value = {
                pitch,
                bearing,
                isDiving
            };
        }
    }

    function updatePosition() {
        if (!map) {
            return;
        }

        const km = props.position;

        target = pointAt(props.line, km);
        boat.setLngLat([target.lon, target.lat]).setRotation(target.bearing - 90);
        updateVisited(stationIndexAt(props.stations, km));

        if (Math.abs(km - trailKm) > 6) {
            updateTrail(km);
        }

        if (!isDiving) {
            isFollowing = true;
            startFollowing();
        }
    }

    function updateTrail(km) {
        const end = lineIndexAt(props.line, km);
        const coordinates = props.line.slice(0, end).map((point) => [point[1], point[2]]);

        trailKm = km;
        coordinates.push([target.lon, target.lat]);
        map.getSource('trail')?.setData(lineFeature(coordinates));
    }

    function updateVisited(index) {
        if (index === visitedUpTo || !map.getSource('stations')) {
            return;
        }

        const from = Math.min(index, visitedUpTo) + 1;
        const to = Math.max(index, visitedUpTo);

        for (let i = Math.max(0, from); i <= to; i++) {
            map.setFeatureState({
                source : 'stations',
                id : i + 1
            }, {
                visited : i <= index
            });
        }

        visitedUpTo = index;
    }

    watch(() => props.position, updatePosition);
    watch(() => props.padding, (padding) => map?.setPadding(padding), {
        deep : true
    });
    watch(() => store.mapLayers, (layers) => {
        map?.getSource('bathymetry')?.setData(toRaw(layers?.bathymetry) ?? EMPTY);
        map?.getSource('land')?.setData(toRaw(layers?.land) ?? EMPTY);
    });

    onMounted(() => {
        const start = pointAt(props.line, props.position);

        map = new maplibregl.Map({
            container : container.value,
            style : buildStyle(),
            center : [start.lon, start.lat],
            zoom : FOLLOW_ZOOM,
            // The whole world, as on the main map; deep zoom only in the research area
            minZoom : 1.5,
            maxZoom : MAX_ZOOM,
            maxPitch : 85,
            transformCameraUpdate : limitZoom(MAX_ZOOM),
            // Turning and tilting by hand are fine: the compass sets them straight again
            attributionControl : false
        });

        map.setPadding(props.padding);

        if (import.meta.env.DEV) {
            window.explorerMap = map;
        }

        // The plugin can mount before its frame has its final size
        resizeObserver = new ResizeObserver(() => map?.resize());
        resizeObserver.observe(container.value);
        boat = createBoat().setLngLat([start.lon, start.lat]).addTo(map);

        // A user who moves the map takes over until the timeline moves again
        map.on('dragstart', stopFollowing);
        map.on('wheel', stopFollowing);
        map.on('touchstart', stopFollowing);
        map.on('move', updateCamera);
        map.on('zoomend', updatePhotoZoom);

        for (const layer of ['stations', 'stations-finds']) {
            map.on('click', layer, (event) => {
                const index = event.features[0]?.properties.index;

                if (index !== undefined) {
                    emit('select', props.stations[index]);
                }
            });
            map.on('mouseenter', layer, () => {
                map.getCanvas().style.cursor = 'pointer';
            });
            map.on('mouseleave', layer, () => {
                map.getCanvas().style.cursor = '';
            });
        }

        map.on('load', () => {
            createLabels();
            createPhotoMarkers();
            createTopMarkers();
            updatePhotoZoom();
            updatePosition();
        });
    });

    onBeforeUnmount(() => {
        resizeObserver?.disconnect();
        stopFollowing();
        [...topMarkers, ...photoMarkers, ...labels].forEach((marker) => marker.remove());
        map?.remove();
        map = null;
    });

    defineExpose({
        dive,
        surface
    });
</script>

<template>
    <div
        ref="root"
        class="el-explorer-map">
        <div
            ref="container"
            class="canvas"></div>

        <button
            v-if="isCompassVisible"
            class="compass"
            type="button"
            aria-label="Kaart recht van boven, met het noorden boven"
            title="Kaart recht van boven, met het noorden boven"
            v-on:click="resetNorth()">
            <svg
                v-bind:style="{ transform : compassTransform }"
                width="26"
                height="26"
                viewBox="-12 -12 24 24"
                aria-hidden="true">
                <circle
                    r="11"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.2" />
                <path
                    d="M0,-6.5 L2.6,0 L-2.6,0 Z"
                    fill="var(--c-terracotta)" />
                <text
                    y="-7.2"
                    text-anchor="middle"
                    font-size="3.6"
                    font-weight="600"
                    fill="var(--c-terracotta)">N</text>
                <path
                    d="M0,7 L2.6,0 L-2.6,0 Z"
                    fill="currentColor" />
            </svg>
        </button>
    </div>
</template>

<style lang="scss" scoped>
    .el-explorer-map {
        position: absolute;
        inset: 0;
        background: var(--c-sea);

        .canvas {
            position: absolute;
            inset: 0;
        }

        :deep(.boat) {
            pointer-events: none;
            filter: drop-shadow(0 2px 3px rgba(8, 26, 44, 0.35));
        }

        :deep(.map-label) {
            pointer-events: none;
            white-space: nowrap;
            font-family: var(--font-header);
            font-style: italic;
            text-transform: uppercase;
        }

        :deep(.map-label--sea) {
            font-size: 1.1rem;
            letter-spacing: 0.3em;
            color: rgba(228, 240, 242, 0.85);
        }

        :deep(.map-label--land) {
            font-style: normal;
            font-size: 1rem;
            letter-spacing: 0.24em;
            color: #6E6248;
        }

        // Round like a pin, with a small point towards the station
        :deep(.photo-marker) {
            position: relative;
            width: 4.2rem;
            height: 4.2rem;
            padding: 0;
            border: 2px solid #FBF8F1;
            border-radius: 50%;
            background: var(--c-paper);
            box-shadow: 0 2px 6px rgba(8, 26, 44, 0.45);
            cursor: pointer;

            &::after {
                content: "";
                position: absolute;
                left: 50%;
                bottom: -7px;
                margin-left: -5px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #FBF8F1;
            }

            // MapLibre places the marker with an inline transform, so hover changes the border instead
            &:hover {
                border-color: var(--c-terracotta);
            }

            img {
                display: block;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                object-fit: cover;
                filter: sepia(0.15);
            }
        }

        &[is-far] :deep(.photo-marker) {
            display: none;
        }

        :deep(.top-station) {
            display: flex;
            align-items: baseline;
            gap: 0.4rem;
            padding: 0.2rem 0.8rem;
            border: 0;
            border-radius: 1.2rem;
            background: rgba(251, 248, 241, 0.92);
            color: var(--c-ink);
            font-family: var(--font-text);
            font-size: 1.2rem;
            line-height: 1.6;
            box-shadow: 0 1px 4px rgba(8, 26, 44, 0.3);
            cursor: pointer;

            strong {
                font-weight: 600;
                color: var(--c-terracotta);
            }

            span {
                color: var(--c-ink-soft);
            }
        }
    }

    // Below the menu button of the app
    .compass {
        position: absolute;
        top: 7.4rem;
        right: 1.6rem;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 4.4rem;
        height: 4.4rem;
        padding: 0;
        border: 0;
        border-radius: 50%;
        background: rgba(251, 248, 241, 0.94);
        color: var(--c-ink);
        box-shadow: 0 1px 4px rgba(8, 26, 44, 0.3);
        cursor: pointer;
        perspective: 8rem;

        svg {
            overflow: visible;
        }
    }
</style>
