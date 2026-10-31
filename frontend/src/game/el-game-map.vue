<script setup>
    // The map of the game: the sea chart of the site, the stations as buoys, the specimens that
    // float near the ship, the fog of what is not discovered yet, and the ship with its smoke and
    // wake. The game loop drives it from outside through the exposed functions.
    import maplibregl from 'maplibre-gl';
    import { inject, onBeforeUnmount, onMounted, ref, toRaw } from 'vue';
    import { seaChartLayers, seaChartSources } from '@/services/sea-chart.js';
    import { BOAT_SVG } from '@/explorer/boat.js';
    import { ICON_PATHS } from '@/explorer/groups.js';
    import { EAST, NORTH, SOUTH, WEST, moveKm, ringAround } from './geo.js';
    import { RARITIES } from './rarity.js';

    const GAME_ZOOM = 7.4;
    const MIN_ZOOM = 6;
    const MAX_ZOOM = 9.5;
    const PITCH = 30;
    // Seconds of sailing the camera looks ahead of the ship
    const LOOK_AHEAD = 1.4;
    const FOLLOW_RATE = 3;
    // After the hand moved the map, the camera goes back to the ship after this many milliseconds
    const RESUME_MS = 2000;
    const WAKE_POINTS = 42;
    const WAKE_INTERVAL = 0.12;
    const ICON_SIZE = 52;
    const EMPTY = {
        type : 'FeatureCollection',
        features : []
    };

    const store = inject('store');

    const props = defineProps({
        stations : {
            type : Array,
            required : true
        },
        line : {
            type : Array,
            required : true
        },
        start : {
            type : Object,
            required : true
        },
        fogCanvas : {
            type : Object,
            default : null
        }
    });

    const root = ref(null);
    const container = ref(null);
    const effects = ref(null);

    let map = null;
    let ship = null;
    let hull = null;
    let smoke = null;
    let center = null;
    let resumeAt = 0;
    let isDragging = false;
    let smokeBudget = 0;
    let wakeTimer = 0;
    let wake = [];
    let resizeObserver = null;

    function buildStyle() {
        const layers = toRaw(store.mapLayers);
        const visited = ['boolean', ['feature-state', 'visited'], false];
        const sources = {
            ...seaChartSources(layers),
            route : {
                type : 'geojson',
                data : {
                    type : 'Feature',
                    properties : {},
                    geometry : {
                        type : 'LineString',
                        coordinates : props.line.map((point) => [point[1], point[2]])
                    }
                }
            },
            wake : {
                type : 'geojson',
                data : EMPTY,
                lineMetrics : true
            },
            stations : {
                type : 'geojson',
                data : stationFeatures(),
                promoteId : 'fid'
            },
            specimens : {
                type : 'geojson',
                data : EMPTY
            },
            target : {
                type : 'geojson',
                data : EMPTY
            }
        };
        const styleLayers = [
            ...seaChartLayers(),
            {
                id : 'route',
                type : 'line',
                source : 'route',
                paint : {
                    'line-color' : '#FBF8F1',
                    'line-width' : 1.2,
                    'line-opacity' : 0.3,
                    'line-dasharray' : [2, 3]
                }
            },
            {
                id : 'wake',
                type : 'line',
                source : 'wake',
                layout : {
                    'line-cap' : 'round'
                },
                paint : {
                    'line-width' : ['interpolate', ['linear'], ['zoom'], 6, 3, 9, 9],
                    'line-gradient' : ['interpolate', ['linear'], ['line-progress'], 0, 'rgba(251, 248, 241, 0)', 1, 'rgba(251, 248, 241, 0.75)']
                }
            },
            {
                id : 'stations',
                type : 'circle',
                source : 'stations',
                paint : {
                    'circle-radius' : ['interpolate', ['linear'], ['zoom'], 6, ['case', ['>', ['get', 'count'], 0], 4, 2.6], 9, ['case', ['>', ['get', 'count'], 0], 8, 5]],
                    'circle-color' : ['case', visited, '#A9512F', '#FBF8F1'],
                    'circle-stroke-color' : ['case', ['>', ['get', 'count'], 0], '#D88A63', '#163A5C'],
                    'circle-stroke-width' : 1.6
                }
            },
            {
                id : 'specimens',
                type : 'symbol',
                source : 'specimens',
                layout : {
                    'icon-image' : ['get', 'icon'],
                    'icon-size' : ['interpolate', ['linear'], ['zoom'], 6, ['*', 0.55, ['get', 'size']], 9, ['*', 1.05, ['get', 'size']]],
                    'icon-allow-overlap' : true,
                    'icon-ignore-placement' : true,
                    'symbol-sort-key' : ['get', 'order']
                }
            }
        ];

        if (props.fogCanvas) {
            sources.fog = {
                type : 'canvas',
                canvas : props.fogCanvas,
                animate : false,
                coordinates : [[WEST, NORTH], [EAST, NORTH], [EAST, SOUTH], [WEST, SOUTH]]
            };
            styleLayers.push({
                id : 'fog',
                type : 'raster',
                source : 'fog',
                paint : {
                    'raster-opacity' : 1,
                    'raster-fade-duration' : 0,
                    'raster-resampling' : 'linear'
                }
            });
        }

        // The mission area stays visible on the undiscovered chart
        styleLayers.push({
            id : 'target-fill',
            type : 'fill',
            source : 'target',
            paint : {
                'fill-color' : '#A9512F',
                'fill-opacity' : 0.1
            }
        }, {
            id : 'target-line',
            type : 'line',
            source : 'target',
            paint : {
                'line-color' : '#A9512F',
                'line-width' : 2,
                'line-dasharray' : [2, 2]
            }
        });

        return {
            version : 8,
            sources,
            layers : styleLayers
        };
    }

    function createShip() {
        const element = document.createElement('div');

        element.className = 'ship';
        element.setAttribute('aria-hidden', 'true');
        element.innerHTML = `
            <div class="ship__glints"><i></i><i></i><i></i><i></i><i></i></div>
            <div class="ship__bob">
                <div class="ship__hull">${BOAT_SVG}<div class="ship__smoke"></div></div>
            </div>`;
        hull = element.querySelector('.ship__hull');
        smoke = element.querySelector('.ship__smoke');

        return new maplibregl.Marker({
            element,
            rotationAlignment : 'map',
            pitchAlignment : 'map'
        });
    }

    // Draws the icon of a group with a ring in the colour of its rarity, when the map first asks for it
    function drawIcon(id) {
        const [, key, rarity] = id.split('|');
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        const half = ICON_SIZE / 2;
        const isNameBearer = rarity === 'nameBearer';
        const color = RARITIES[rarity]?.color ?? '#FBF8F1';

        canvas.width = ICON_SIZE;
        canvas.height = ICON_SIZE;
        context.shadowColor = isNameBearer ? 'rgba(255, 214, 120, 0.95)' : 'rgba(8, 26, 44, 0.45)';
        context.shadowBlur = isNameBearer ? 10 : 4;
        context.beginPath();
        context.arc(half, half, half - 6, 0, 2 * Math.PI);
        context.fillStyle = isNameBearer ? '#FFF4D6' : '#FBF8F1';
        context.fill();
        context.shadowColor = 'transparent';
        context.lineWidth = rarity === 'common' ? 1.5 : 4;
        context.strokeStyle = rarity === 'common' ? 'rgba(27, 36, 51, 0.45)' : color;
        context.stroke();

        const scale = 1.25;

        context.save();
        context.translate(half - 12 * scale, half - 12 * scale);
        context.scale(scale, scale);
        context.lineWidth = 1.8;
        context.lineCap = 'round';
        context.lineJoin = 'round';
        context.strokeStyle = '#163A5C';
        context.stroke(new Path2D(ICON_PATHS[key] ?? ICON_PATHS.unknown));
        context.restore();

        map.addImage(id, context.getImageData(0, 0, ICON_SIZE, ICON_SIZE), {
            pixelRatio : 2
        });
    }

    // Little drops that spring up where something was caught
    function splash(point, color) {
        if (!map || !effects.value) {
            return;
        }

        const { x, y } = map.project([point.lon, point.lat]);

        for (let i = 0; i < 9; i++) {
            const drop = document.createElement('span');
            const angle = (i / 9) * 2 * Math.PI + Math.random() * 0.4;
            const distance = 18 + Math.random() * 22;

            drop.className = 'drop';
            drop.style.background = color;
            effects.value.appendChild(drop);
            drop.animate([
                {
                    transform : `translate(${x}px, ${y}px) scale(1)`,
                    opacity : 1
                },
                {
                    transform : `translate(${x + Math.cos(angle) * distance}px, ${y + Math.sin(angle) * distance - 14}px) scale(0.4)`,
                    opacity : 0
                }
            ], {
                duration : 520 + Math.random() * 200,
                easing : 'cubic-bezier(0.2, 0.7, 0.4, 1)'
            }).onfinish = () => drop.remove();
        }

        const ring = document.createElement('span');

        ring.className = 'ring';
        ring.style.left = `${x}px`;
        ring.style.top = `${y}px`;
        effects.value.appendChild(ring);
        ring.addEventListener('animationend', () => ring.remove());
    }

    function project(point) {
        return map ? map.project([point.lon, point.lat]) : null;
    }

    function puff(level) {
        const element = document.createElement('span');

        element.className = 'puff';
        element.style.setProperty('--size', `${6 + level * 7}px`);
        element.style.setProperty('--drift', `${-30 - level * 40}px`);
        element.style.setProperty('--side', `${(Math.random() - 0.5) * 14}px`);
        element.addEventListener('animationend', () => element.remove());
        smoke.appendChild(element);
    }

    function refreshFog() {
        const source = map?.getSource('fog');

        if (source) {
            source.play();
            source.pause();
            map.triggerRepaint();
        }
    }

    function setSpecimens(features) {
        map?.getSource('specimens')?.setData({
            type : 'FeatureCollection',
            features
        });
    }

    function setTarget(mission) {
        map?.getSource('target')?.setData(mission ? {
            type : 'Feature',
            properties : {},
            geometry : {
                type : 'Polygon',
                coordinates : [ringAround(mission.center, mission.radiusKm)]
            }
        } : EMPTY);
    }

    function setVisited(index) {
        map?.setFeatureState({
            source : 'stations',
            id : index + 1
        }, {
            visited : true
        });
    }

    function shake() {
        root.value?.removeAttribute('is-shaking');
        requestAnimationFrame(() => root.value?.setAttribute('is-shaking', ''));
    }

    function stationFeatures() {
        return {
            type : 'FeatureCollection',
            features : props.stations.map((station) => ({
                type : 'Feature',
                properties : {
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

    // Once per frame: the ship, its smoke and wake, and the camera that follows it
    function update(state, dt, level) {
        if (!map) {
            return;
        }

        ship.setLngLat([state.lon, state.lat]);
        hull.style.transform = `rotate(${state.heading - 90}deg)`;

        smokeBudget += dt * (1.2 + level * 4);

        while (smokeBudget >= 1) {
            smokeBudget--;
            puff(level);
        }

        wakeTimer += dt;

        if (wakeTimer >= WAKE_INTERVAL) {
            wakeTimer = 0;
            wake.push([state.lon, state.lat]);
            wake = wake.slice(-WAKE_POINTS);

            if (wake.length > 1) {
                map.getSource('wake')?.setData({
                    type : 'Feature',
                    properties : {},
                    geometry : {
                        type : 'LineString',
                        coordinates : wake
                    }
                });
            }
        }

        if (isDragging || performance.now() < resumeAt) {
            center = null;

            return;
        }

        const radians = state.heading * Math.PI / 180;
        const ahead = moveKm(state, Math.sin(radians) * state.speed * LOOK_AHEAD, Math.cos(radians) * state.speed * LOOK_AHEAD);
        const current = center ?? map.getCenter().toArray();
        const rate = Math.min(1, dt * FOLLOW_RATE);

        center = [current[0] + (ahead.lon - current[0]) * rate, current[1] + (ahead.lat - current[1]) * rate];
        map.jumpTo({
            center
        });
    }

    onMounted(() => {
        map = new maplibregl.Map({
            container : container.value,
            style : buildStyle(),
            center : [props.start.lon, props.start.lat],
            zoom : GAME_ZOOM,
            pitch : PITCH,
            minZoom : MIN_ZOOM,
            maxZoom : MAX_ZOOM,
            minPitch : PITCH,
            maxPitch : PITCH,
            maxBounds : [[WEST - 3, SOUTH - 3], [EAST + 3, NORTH + 3]],
            dragRotate : false,
            pitchWithRotate : false,
            touchPitch : false,
            keyboard : false,
            attributionControl : false
        });
        // Zoom around the middle, where the camera keeps the ship anyway
        map.scrollZoom.enable({
            around : 'center'
        });
        map.touchZoomRotate.enable({
            around : 'center'
        });
        map.touchZoomRotate.disableRotation();
        map.setPadding({
            top : 40,
            right : 0,
            bottom : 140,
            left : 0
        });

        if (import.meta.env.DEV) {
            window.gameMap = map;
        }

        resizeObserver = new ResizeObserver(() => map?.resize());
        resizeObserver.observe(container.value);
        ship = createShip().setLngLat([props.start.lon, props.start.lat]).addTo(map);

        map.on('styleimagemissing', (event) => {
            if (event.id.startsWith('sp|')) {
                drawIcon(event.id);
            }
        });
        map.on('dragstart', () => {
            isDragging = true;
        });
        map.on('dragend', () => {
            isDragging = false;
            resumeAt = performance.now() + RESUME_MS;
        });
    });

    onBeforeUnmount(() => {
        resizeObserver?.disconnect();
        map?.remove();
        map = null;
    });

    defineExpose({
        project,
        refreshFog,
        setSpecimens,
        setTarget,
        setVisited,
        shake,
        splash,
        update
    });
</script>

<template>
    <div
        ref="root"
        class="el-game-map">
        <div
            ref="container"
            class="canvas"></div>
        <div
            ref="effects"
            class="effects"></div>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-map {
        position: absolute;
        inset: 0;
        background: var(--c-sea);

        &[is-shaking] .canvas {
            animation: shake 0.35s ease-out;
        }

        .canvas {
            position: absolute;
            inset: 0;
        }
    }

    .effects {
        position: absolute;
        inset: 0;
        pointer-events: none;
        overflow: hidden;

        :deep(.drop) {
            position: absolute;
            left: -4px;
            top: -4px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            box-shadow: 0 0 0 1px rgba(251, 248, 241, 0.8);
        }

        :deep(.ring) {
            position: absolute;
            width: 1rem;
            height: 1rem;
            margin: -0.5rem 0 0 -0.5rem;
            border: 2px solid rgba(251, 248, 241, 0.9);
            border-radius: 50%;
            animation: ring 0.6s ease-out forwards;
        }
    }

    // Light comes from the north west, so the shadow falls to the south east
    :deep(.ship) {
        pointer-events: none;
        filter: drop-shadow(3px 5px 3px rgba(8, 26, 44, 0.45));
    }

    :deep(.ship__bob) {
        animation: bob 2.6s ease-in-out infinite;
    }

    :deep(.ship__hull) {
        position: relative;
        width: 72px;
        height: 36px;

        svg {
            display: block;
        }
    }

    :deep(.ship__smoke) {
        position: absolute;
        left: 50%;
        top: 50%;
    }

    :deep(.puff) {
        position: absolute;
        left: calc(var(--size) / -2);
        top: calc(var(--size) / -2);
        width: var(--size);
        height: var(--size);
        border-radius: 50%;
        background: rgba(70, 70, 76, 0.35);
        animation: puff 1.6s ease-out forwards;
    }

    :deep(.ship__glints) {
        position: absolute;
        inset: -18px;
        pointer-events: none;

        i {
            position: absolute;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.9);
            opacity: 0;
            animation: glint 2.4s ease-in-out infinite;

            &:nth-child(1) {
                left: 6%;
                top: 18%;
            }

            &:nth-child(2) {
                left: 88%;
                top: 30%;
                animation-delay: 0.6s;
            }

            &:nth-child(3) {
                left: 20%;
                top: 86%;
                animation-delay: 1.1s;
            }

            &:nth-child(4) {
                left: 72%;
                top: 92%;
                animation-delay: 1.7s;
            }

            &:nth-child(5) {
                left: 48%;
                top: 2%;
                animation-delay: 2s;
            }
        }
    }

    @keyframes bob {
        0%,
        100% {
            transform: translateY(0) scale(1);
        }

        50% {
            transform: translateY(-1.5px) scale(1.015);
        }
    }

    @keyframes puff {
        0% {
            opacity: 0.8;
            transform: translate(0, 0) scale(0.6);
        }

        100% {
            opacity: 0;
            transform: translate(var(--drift), var(--side)) scale(2.4);
        }
    }

    @keyframes glint {
        0%,
        100% {
            opacity: 0;
            transform: scale(0.4);
        }

        50% {
            opacity: 0.85;
            transform: scale(1);
        }
    }

    @keyframes ring {
        0% {
            opacity: 1;
            transform: scale(1);
        }

        100% {
            opacity: 0;
            transform: scale(6);
        }
    }

    @keyframes shake {
        0%,
        100% {
            transform: translate(0, 0);
        }

        20% {
            transform: translate(-6px, 3px);
        }

        40% {
            transform: translate(5px, -3px);
        }

        60% {
            transform: translate(-3px, 2px);
        }

        80% {
            transform: translate(2px, -1px);
        }
    }
</style>
