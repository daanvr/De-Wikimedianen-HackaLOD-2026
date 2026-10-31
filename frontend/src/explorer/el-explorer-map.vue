<script setup>
    import maplibregl from 'maplibre-gl';
    import { computed, inject, onBeforeUnmount, onMounted, ref, shallowRef, toRaw, watch } from 'vue';
    import { formatDate } from '@/services/format.js';
    import { LAND_LABELS, SEA_LABELS, limitZoom, seaChartLayers, seaChartSources } from '@/services/sea-chart.js';
    import { lineIndexAt, pointAt, stationIndexAt } from './data.js';
    import Ship, { monsoonAt } from './ship.js';

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
    // While the ship is within this many route kilometres of a station with a photo, that photo
    // gets a ring on the map and shows larger in a corner; it stays a moment after the ship has gone
    const PHOTO_NEAR_KM = 25;
    const PHOTO_LINGER = 1500;
    // Faster than this (km/s, scrubbing or a high speed) no new photo comes up, so it does not flicker
    const PHOTO_MAX_SPEED = 100;
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
    // The station whose photo shows in the corner
    const nearStation = shallowRef(null);
    const isCompassVisible = computed(() => !camera.value.isDiving && (camera.value.pitch >= 0.5 || Math.abs(camera.value.bearing) >= 0.5));
    // North of the compass points to north on the map
    const compassTransform = computed(() => `rotateX(${camera.value.pitch * COMPASS_TILT}deg) rotateZ(${-camera.value.bearing}deg)`);

    let map = null;
    let ship = null;
    let shipCanvas = null;
    let shipContext = null;
    let pixelRatio = 1;
    let frame = null;
    let lastFrame = 0;
    let isFollowing = true;
    let isFollowPaused = false;
    let isDiving = false;
    let isShipHidden = false;
    let visitedUpTo = -1;
    let trailKm = -1;
    let topMarkers = [];
    let photoMarkers = [];
    let photoStations = [];
    let nearIndex = -1;
    let nearLeftAt = 0;
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

    // The ship is drawn on its own canvas right above the map, under the markers and labels
    function createShipCanvas() {
        shipCanvas = document.createElement('canvas');
        shipCanvas.className = 'ship';
        shipCanvas.setAttribute('aria-hidden', 'true');
        map.getCanvasContainer().insertBefore(shipCanvas, map.getCanvas().nextSibling);
        shipContext = shipCanvas.getContext('2d');
        resizeShipCanvas();
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
        photoStations = props.stations.filter((station) => station.photo);
        photoMarkers = photoStations
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

        const spot = pointAt(props.line, station.km);
        const height = container.value.clientHeight;

        isDiving = true;
        stopFollowing();
        setInteractive(false);
        updateCamera();
        // The ship lies still at the station for the dive
        ship.place(station.km);

        await move('flyTo', {
            center : [spot.lon, spot.lat],
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
            center : [spot.lon, spot.lat],
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
        for (const marker of [...topMarkers, ...photoMarkers, ...labels]) {
            marker.getElement().style.visibility = hidden ? 'hidden' : '';
        }

        isShipHidden = hidden;
    }

    // Straight down with north up; the map stays where it is
    async function resetNorth() {
        // Following would stop the ease halfway
        isFollowPaused = true;
        await move('easeTo', {
            pitch : 0,
            bearing : 0,
            duration : 700
        });
        isFollowPaused = false;
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
            center : ship ? [ship.position.lon, ship.position.lat] : map.getCenter(),
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

    // Eases the camera towards the ship, one step per frame
    function followShip() {
        const center = map.getCenter();
        const dx = ship.position.lon - center.lng;
        const dy = ship.position.lat - center.lat;

        if (Math.abs(dx) + Math.abs(dy) < 0.00005) {
            return;
        }

        map.jumpTo({
            center : [center.lng + dx * 0.16, center.lat + dy * 0.16]
        });
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

    function resizeShipCanvas() {
        if (!shipCanvas) {
            return;
        }

        const width = container.value.clientWidth;
        const height = container.value.clientHeight;

        pixelRatio = Math.min(window.devicePixelRatio || 1, 3);
        shipCanvas.width = Math.round(width * pixelRatio);
        shipCanvas.height = Math.round(height * pixelRatio);
        shipCanvas.style.width = `${width}px`;
        shipCanvas.style.height = `${height}px`;
    }

    // One frame of the ship: physics, the camera following it, the trail and the drawing
    function step(now) {
        const dt = Math.min(0.05, Math.max(0.001, (now - lastFrame) / 1000));

        frame = requestAnimationFrame(step);
        lastFrame = now;

        if (!map || isShipHidden) {
            return;
        }

        const station = props.stations[Math.max(0, stationIndexAt(props.stations, ship.km))];
        const view = {
            bearing : map.getBearing(),
            pitch : map.getPitch(),
            zoom : map.getZoom(),
            project : (lon, lat) => {
                const point = map.project([lon, lat]);

                return [point.x, point.y];
            }
        };

        ship.update(dt, props.position, view.zoom, monsoonAt(station?.datum));

        if (isFollowing && !isFollowPaused && !isDiving) {
            followShip();
        }

        updateVisited(stationIndexAt(props.stations, ship.km));
        updateNearPhoto(now);

        if (Math.abs(ship.km - trailKm) > 6 || (Math.abs(ship.velocity) < 0.5 && Math.abs(ship.km - trailKm) > 0.5)) {
            updateTrail(ship.km);
        }

        shipContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        shipContext.clearRect(0, 0, shipCanvas.width, shipCanvas.height);
        ship.draw(shipContext, view);
    }

    function stopFollowing() {
        isFollowing = false;
    }

    // Rings the photo of the station the ship is passing and puts it in the corner
    function updateNearPhoto(now) {
        let index = -1;
        let distance = PHOTO_NEAR_KM;

        photoStations.forEach((station, i) => {
            const gap = Math.abs(station.km - ship.km);

            if (gap < distance) {
                index = i;
                distance = gap;
            }
        });

        // A new photo only comes up at a speed at which you can see it
        if (index !== nearIndex && Math.abs(ship.velocity) > PHOTO_MAX_SPEED) {
            index = -1;
        }

        // The photo stays a moment after the ship has gone
        if (index === -1 && nearIndex !== -1) {
            nearLeftAt ||= now;

            if (now - nearLeftAt < PHOTO_LINGER) {
                return;
            }
        } else {
            nearLeftAt = 0;
        }

        if (index === nearIndex) {
            return;
        }

        photoMarkers[nearIndex]?.getElement().removeAttribute('is-near');
        photoMarkers[index]?.getElement().setAttribute('is-near', '');
        nearIndex = index;
        nearLeftAt = 0;
        nearStation.value = photoStations[index] ?? null;
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

    // The timeline moved: the ship sails there by itself, and the camera follows it again
    function updatePosition() {
        if (map && !isDiving) {
            isFollowing = true;
        }
    }

    function updateTrail(km) {
        const end = lineIndexAt(props.line, km);
        const coordinates = props.line.slice(0, end).map((point) => [point[1], point[2]]);

        trailKm = km;
        coordinates.push([ship.position.lon, ship.position.lat]);
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
        resizeObserver = new ResizeObserver(() => {
            map?.resize();
            resizeShipCanvas();
        });
        resizeObserver.observe(container.value);
        // With less motion asked for, the ship lies on a flat sea
        ship = new Ship(props.line, {
            waves : window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 0 : 0.6
        });
        ship.place(props.position);
        createShipCanvas();

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
            lastFrame = performance.now();
            frame = requestAnimationFrame(step);
        });
    });

    onBeforeUnmount(() => {
        resizeObserver?.disconnect();
        stopFollowing();
        cancelAnimationFrame(frame);
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

        <transition name="photo-card">
            <button
                v-if="nearStation && !camera.isDiving"
                v-bind:key="nearStation.nummer"
                class="photo-card"
                type="button"
                v-bind:aria-label="`Station ${nearStation.nummer}, foto: ${nearStation.photo.caption}. Duik hier.`"
                v-on:click="emit('select', nearStation)">
                <img
                    v-bind:src="nearStation.photo.src"
                    alt="">
                <span class="photo-card__text">
                    <strong>Station {{ nearStation.nummer }}</strong>
                    {{ formatDate(nearStation.datum) }}
                    <small v-if="nearStation.photo.caption">{{ nearStation.photo.caption }}</small>
                </span>
            </button>
        </transition>

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

        :deep(.ship) {
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
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

            // Near the ship: a ring, above the other markers; it stays where it is and keeps its size
            &[is-near] {
                z-index: 2;
                border-color: var(--c-terracotta);
                box-shadow: 0 0 0 3px rgba(169, 81, 47, 0.35), 0 2px 6px rgba(8, 26, 44, 0.45);

                &::after {
                    border-top-color: var(--c-terracotta);
                }
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

    // The photo of the station the ship is passing, in the corner under the date
    .photo-card {
        position: absolute;
        top: 6rem;
        left: 1.6rem;
        z-index: 1;
        display: flex;
        flex-direction: column;
        width: 17rem;
        padding: 0;
        border: 0;
        border-radius: 0.6rem;
        overflow: hidden;
        background: var(--c-paper);
        color: var(--c-ink);
        text-align: left;
        box-shadow: var(--shadow-float);
        cursor: pointer;

        img {
            display: block;
            width: 100%;
            aspect-ratio: 4 / 3;
            object-fit: cover;
            filter: sepia(0.15);
        }
    }

    .photo-card__text {
        display: flex;
        flex-direction: column;
        padding: 0.6rem 1rem 0.8rem;
        font-family: var(--font-text);
        font-size: 1.3rem;
        line-height: 1.35;
        color: var(--c-ink-soft);

        strong {
            font-family: var(--font-header);
            font-weight: 400;
            font-size: 1.5rem;
            color: var(--c-ink);
        }

        small {
            display: -webkit-box;
            margin-top: 0.2rem;
            overflow: hidden;
            font-size: 1.2rem;
            font-style: italic;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
        }
    }

    .photo-card-enter-active,
    .photo-card-leave-active {
        transition: opacity 0.5s, transform 0.5s;
    }

    .photo-card-enter-from,
    .photo-card-leave-to {
        opacity: 0;
        transform: translateY(-0.6rem);
    }

    @media (prefers-reduced-motion: reduce) {
        .photo-card-enter-active,
        .photo-card-leave-active {
            transition: opacity 0.3s;
        }

        .photo-card-enter-from,
        .photo-card-leave-to {
            transform: none;
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
