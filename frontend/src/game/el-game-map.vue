<script setup>
    // The map of the game: the sea chart of the site, the stations as buoys, the specimens that
    // float near the ship, the fog of what is not discovered yet, and the ship: the small physical
    // model of the explore mode, drawn on its own canvas above the map. The game loop drives it
    // from outside through the exposed functions.
    import maplibregl from 'maplibre-gl';
    import { inject, onBeforeUnmount, onMounted, ref, toRaw } from 'vue';
    import { seaChartLayers, seaChartSources } from '@/services/sea-chart.js';
    import { ICON_PATHS } from '@/explorer/groups.js';
    import { EAST, NORTH, SOUTH, WEST, moveKm, ringAround } from './geo.js';
    import { RARITIES } from './rarity.js';
    import GameShip from './ship.js';

    const GAME_ZOOM = 7.4;
    const MIN_ZOOM = 6;
    const MAX_ZOOM = 9.5;
    const PITCH = 30;
    // Seconds of sailing the camera looks ahead of the ship
    const LOOK_AHEAD = 1.4;
    const FOLLOW_RATE = 3;
    // After the hand moved the map, the camera goes back to the ship after this many milliseconds
    const RESUME_MS = 2000;
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
    let shipCanvas = null;
    let shipContext = null;
    let pixelRatio = 1;
    let center = null;
    let resumeAt = 0;
    let isDragging = false;
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

    // The ship is drawn on its own canvas right above the map, under the effects and the controls
    function createShipCanvas() {
        shipCanvas = document.createElement('canvas');
        shipCanvas.className = 'ship';
        shipCanvas.setAttribute('aria-hidden', 'true');
        map.getCanvasContainer().insertBefore(shipCanvas, map.getCanvas().nextSibling);
        shipContext = shipCanvas.getContext('2d');
        resizeShipCanvas();
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

    function refreshFog() {
        const source = map?.getSource('fog');

        if (source) {
            source.play();
            source.pause();
            map.triggerRepaint();
        }
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

    // Drawn after every render of the map, so the ship and the sea under it never drift apart
    function drawShip() {
        if (!ship || !shipContext) {
            return;
        }

        shipContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        shipContext.clearRect(0, 0, shipCanvas.width, shipCanvas.height);
        ship.draw(shipContext, {
            bearing : map.getBearing(),
            pitch : map.getPitch(),
            zoom : map.getZoom(),
            project : (lon, lat) => {
                const point = map.project([lon, lat]);

                return [point.x, point.y];
            }
        });
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

    // Once per frame: the ship model, and the camera that follows it; wind is { from, strength }
    function update(state, dt, wind) {
        if (!map) {
            return;
        }

        ship.follow(state, dt, map.getZoom(), wind);
        map.triggerRepaint();

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

        resizeObserver = new ResizeObserver(() => {
            map?.resize();
            resizeShipCanvas();
        });
        resizeObserver.observe(container.value);
        ship = new GameShip(props.start);
        createShipCanvas();
        map.on('render', drawShip);

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

    :deep(.ship) {
        position: absolute;
        top: 0;
        left: 0;
        pointer-events: none;
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
