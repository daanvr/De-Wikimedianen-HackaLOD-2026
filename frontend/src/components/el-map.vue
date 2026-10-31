<script setup>
    import maplibregl from 'maplibre-gl';
    import { onBeforeUnmount, onMounted, ref, toRaw, watch } from 'vue';

    // Flat depth bands: the deeper, the darker. Keys are Natural Earth depths in metres.
    const DEPTH_COLORS = [
        200, '#6FB0C2',
        1000, '#4387A8',
        2000, '#2B6A92',
        3000, '#255E8B',
        4000, '#1F5280',
        5000, '#1A4672',
        6000, '#163C61',
        7000, '#12324F'
    ];

    const SHALLOW_COLOR = '#A3D3D2';
    const ARCHIPELAGO_BOUNDS = [[106, -12], [136, 6]];
    // The research area: the extent of the detailed layers in public/map/. Outside it the
    // coarse world layers take over, and you can only zoom in to about province level.
    const LAYER_BOUNDS = [[104, -16], [142, 10]];
    const MAX_ZOOM = 11;
    const OUTSIDE_MAX_ZOOM = 6;
    // How fast the zoom limit drops when you pan out of the research area, in zoom levels per degree
    const ZOOM_DROP_PER_DEGREE = 2;
    const TRAVEL_MS = 2600;
    // Historical map, georeferenced with Allmaps; loaded live, the vector layers stay underneath as a fallback
    const HISTORIC_MAP_TILES = 'https://allmaps.xyz/images/1fd0accb445d424e/{z}/{x}/{y}@2x.png';
    const HISTORIC_MAP_BOUNDS = [111.67, -12.29, 135.37, 7.33];
    const SATELLITE_TILES = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

    // What each base map shows on top of the vector layers, which are always drawn as a fallback
    const BASES = {
        historic : {
            historic : 1,
            satellite : false
        },
        historicHalf : {
            historic : 0.5,
            satellite : true
        },
        chart : {
            historic : 0,
            satellite : false
        },
        satellite : {
            historic : 0,
            satellite : true
        }
    };

    const SEA_LABELS = [
        {
            text : 'Java-zee',
            lon : 111.5,
            lat : -5.0
        },
        {
            text : 'Flores-zee',
            lon : 120.2,
            lat : -7.4
        },
        {
            text : 'Banda-zee',
            lon : 127.0,
            lat : -5.6
        },
        {
            text : 'Molukse Zee',
            lon : 126.0,
            lat : 1.4
        },
        {
            text : 'Celebes-zee',
            lon : 121.6,
            lat : 3.8
        },
        {
            text : 'Indische Oceaan',
            lon : 116.0,
            lat : -12.6
        },
        {
            text : 'Stille Oceaan',
            lon : 133.0,
            lat : 3.6
        },
        {
            text : 'Arafura-zee',
            lon : 135.5,
            lat : -9.2
        }
    ];

    const LAND_LABELS = [
        {
            text : 'Celebes',
            lon : 120.3,
            lat : -2.0
        },
        {
            text : 'Borneo',
            lon : 114.2,
            lat : 0.4
        },
        {
            text : 'Java',
            lon : 110.2,
            lat : -7.35
        },
        {
            text : 'Nieuw-Guinea',
            lon : 138.5,
            lat : -4.6
        },
        {
            text : 'Halmahera',
            lon : 128.15,
            lat : 0.9
        },
        {
            text : 'Ceram',
            lon : 129.5,
            lat : -3.15
        },
        {
            text : 'Timor',
            lon : 125.0,
            lat : -9.3
        }
    ];

    const props = defineProps({
        base : {
            type : String,
            default : 'historic'
        },
        layers : {
            type : Object,
            default : null
        },
        mode : {
            type : String,
            default : 'home'
        },
        focus : {
            type : Object,
            default : null
        },
        boat : {
            type : Object,
            default : null
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

    const container = ref(null);
    const isReady = ref(false);

    let map = null;
    let labels = [];
    let boatMarker = null;
    let boatPosition = null;
    let boatAnimation = null;

    function animateBoat(target) {
        if (!boatMarker) {
            return;
        }

        if (!boatPosition) {
            boatPosition = target;
            boatMarker.setLngLat([target.lon, target.lat]);
            return;
        }

        const start = boatPosition;
        const bearing = Math.atan2(target.lon - start.lon, target.lat - start.lat) * 180 / Math.PI;
        const startedAt = performance.now();

        cancelAnimationFrame(boatAnimation);
        boatMarker.setRotation(bearing - 90);

        function step(now) {
            const progress = Math.min(1, (now - startedAt) / TRAVEL_MS);
            const eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;

            boatPosition = {
                lon : start.lon + (target.lon - start.lon) * eased,
                lat : start.lat + (target.lat - start.lat) * eased
            };

            boatMarker.setLngLat([boatPosition.lon, boatPosition.lat]);

            if (progress < 1) {
                boatAnimation = requestAnimationFrame(step);
            }
        }

        boatAnimation = requestAnimationFrame(step);
    }

    function applyBase() {
        if (!map || !isReady.value) {
            return;
        }

        const base = currentBase();

        map.setLayoutProperty('satellite', 'visibility', base.satellite ? 'visible' : 'none');
        map.setLayoutProperty('historic-map', 'visibility', base.historic ? 'visible' : 'none');
        map.setPaintProperty('historic-map', 'raster-opacity', base.historic || 1);

        // The historical map prints its own names, so hide ours where they would overlap
        for (const label of labels) {
            label.marker.getElement().hidden = Boolean(base.historic) && label.onHistoricMap;
        }
    }

    function applyFocus(animate = true) {
        if (!map) {
            return;
        }

        const padding = props.padding;

        if (!props.focus) {
            map.fitBounds(ARCHIPELAGO_BOUNDS, {
                padding : {
                    top : padding.top + 24,
                    right : padding.right + 24,
                    bottom : padding.bottom + 24,
                    left : padding.left + 24
                },
                duration : animate ? 1400 : 0
            });
            return;
        }

        const options = {
            center : [props.focus.lon, props.focus.lat],
            zoom : props.focus.zoom ?? map.getZoom(),
            padding,
            duration : animate ? (props.focus.duration ?? 1600) : 0,
            essential : true
        };

        if (animate && props.focus.fly) {
            map.flyTo({
                ...options,
                duration : TRAVEL_MS,
                curve : 1.3
            });
        } else {
            map.easeTo(options);
        }
    }

    function buildStyle() {
        const base = currentBase();
        const empty = {
            type : 'FeatureCollection',
            features : []
        };
        const layers = props.layers ?? {};

        return {
            version : 8,
            sources : {
                bathymetry : {
                    type : 'geojson',
                    data : layers.bathymetry ?? empty
                },
                land : {
                    type : 'geojson',
                    data : layers.land ?? empty
                },
                // Coarse layers for the rest of the world; MapLibre loads them itself, so the site does not wait for them
                worldBathymetry : {
                    type : 'geojson',
                    data : '/map/world-bathymetry.geojson'
                },
                worldLand : {
                    type : 'geojson',
                    data : '/map/world-land.geojson'
                },
                satellite : {
                    type : 'raster',
                    tiles : [SATELLITE_TILES],
                    tileSize : 256,
                    maxzoom : 19
                },
                historicMap : {
                    type : 'raster',
                    tiles : [HISTORIC_MAP_TILES],
                    tileSize : 256,
                    bounds : HISTORIC_MAP_BOUNDS,
                    maxzoom : 10
                },
                route : {
                    type : 'geojson',
                    data : layers.route ?? empty
                }
            },
            layers : [
                {
                    id : 'sea',
                    type : 'background',
                    paint : {
                        'background-color' : SHALLOW_COLOR
                    }
                },
                {
                    id : 'world-depth',
                    type : 'fill',
                    source : 'worldBathymetry',
                    paint : {
                        'fill-color' : ['match', ['get', 'depth'], ...DEPTH_COLORS, '#1F5280'],
                        'fill-antialias' : false
                    }
                },
                {
                    id : 'depth',
                    type : 'fill',
                    source : 'bathymetry',
                    paint : {
                        'fill-color' : ['match', ['get', 'depth'], ...DEPTH_COLORS, '#1F5280'],
                        'fill-antialias' : false
                    }
                },
                {
                    id : 'land-lagoon',
                    type : 'line',
                    source : 'land',
                    paint : {
                        'line-color' : '#CBE8E2',
                        'line-width' : ['interpolate', ['linear'], ['zoom'], 4, 3, 9, 10],
                        'line-blur' : 1.5,
                        'line-opacity' : 0.8
                    }
                },
                {
                    id : 'land',
                    type : 'fill',
                    source : 'land',
                    paint : {
                        'fill-color' : '#F2ECDB'
                    }
                },
                {
                    id : 'world-land',
                    type : 'fill',
                    source : 'worldLand',
                    paint : {
                        'fill-color' : '#F2ECDB'
                    }
                },
                {
                    id : 'world-land-outline',
                    type : 'line',
                    source : 'worldLand',
                    paint : {
                        'line-color' : '#7C6E52',
                        'line-width' : 0.5
                    }
                },
                {
                    id : 'land-outline',
                    type : 'line',
                    source : 'land',
                    paint : {
                        'line-color' : '#7C6E52',
                        'line-width' : ['interpolate', ['linear'], ['zoom'], 4, 0.5, 9, 1.2]
                    }
                },
                {
                    id : 'satellite',
                    type : 'raster',
                    source : 'satellite',
                    layout : {
                        visibility : base.satellite ? 'visible' : 'none'
                    },
                    paint : {
                        'raster-fade-duration' : 200
                    }
                },
                {
                    id : 'historic-map',
                    type : 'raster',
                    source : 'historicMap',
                    layout : {
                        visibility : base.historic ? 'visible' : 'none'
                    },
                    paint : {
                        'raster-fade-duration' : 200,
                        'raster-opacity' : base.historic || 1
                    }
                },
                {
                    id : 'route-casing',
                    type : 'line',
                    source : 'route',
                    filter : ['==', ['geometry-type'], 'LineString'],
                    layout : {
                        'line-cap' : 'round',
                        'line-join' : 'round'
                    },
                    paint : {
                        'line-color' : '#FBF8F1',
                        'line-width' : ['interpolate', ['linear'], ['zoom'], 4, 3, 9, 6],
                        'line-opacity' : 0.3
                    }
                },
                {
                    id : 'route',
                    type : 'line',
                    source : 'route',
                    filter : ['==', ['geometry-type'], 'LineString'],
                    layout : {
                        'line-cap' : 'round',
                        'line-join' : 'round'
                    },
                    paint : {
                        'line-color' : '#D88A63',
                        'line-width' : ['interpolate', ['linear'], ['zoom'], 4, 1.4, 9, 2.8],
                        'line-dasharray' : [3, 2]
                    }
                },
                {
                    // Small dots where the ship stopped; not interactive
                    id : 'route-stations',
                    type : 'circle',
                    source : 'route',
                    filter : ['==', ['geometry-type'], 'Point'],
                    paint : {
                        'circle-color' : '#A9512F',
                        'circle-radius' : ['interpolate', ['linear'], ['zoom'], 4, ['case', ['get', 'port'], 3.5, 1.8], 9, ['case', ['get', 'port'], 6, 3.5]],
                        'circle-stroke-color' : '#FBF8F1',
                        'circle-stroke-width' : ['interpolate', ['linear'], ['zoom'], 4, 0.6, 9, 1.2]
                    }
                }
            ]
        };
    }

    function createBoatElement() {
        const element = document.createElement('div');

        element.className = 'map-boat';
        element.setAttribute('aria-hidden', 'true');
        // Placeholder: the hand drawn boat replaces this drawing later
        element.innerHTML = `
            <svg width="92" height="46" viewBox="-46 -23 92 46">
                <ellipse rx="36" ry="18" fill="none" stroke="#FBF8F1" stroke-width="1.2" stroke-dasharray="3 3" opacity="0.9"/>
                <path d="M-27,0 L-44,-7 M-27,0 L-44,7" stroke="#FBF8F1" stroke-width="1.4" fill="none" opacity="0.7"/>
                <path d="M-25,0 C-21,-6 8,-7 26,0 C8,7 -21,6 -25,0 Z" fill="#FBF8F1" stroke="#1B2433" stroke-width="1.3"/>
                <path d="M-9,-6 L-9,6 M8,-5 L8,5" stroke="#1B2433" stroke-width="1.3" fill="none"/>
                <circle r="2.4" fill="#A9512F"/>
            </svg>`;

        return element;
    }

    function createLabel(label, kind) {
        const element = document.createElement('div');

        element.className = `map-label map-label--${kind}`;
        element.textContent = label.text;

        labels.push({
            marker : new maplibregl.Marker({
                element,
                anchor : 'center'
            }).setLngLat([label.lon, label.lat]).addTo(map),
            onHistoricMap : isOnHistoricMap(label)
        });
    }

    function currentBase() {
        return BASES[props.base] ?? BASES.historic;
    }

    function isOnHistoricMap(label) {
        const [west, south, east, north] = HISTORIC_MAP_BOUNDS;
        const margin = 0.5;

        return label.lon > west - margin && label.lon < east + margin && label.lat > south - margin && label.lat < north + margin;
    }

    // Allows deep zoom only in the research area: the farther the centre is outside it, the lower the limit
    function limitZoom({ center, zoom }) {
        const [[west, south], [east, north]] = LAYER_BOUNDS;
        const lon = ((center.lng + 540) % 360) - 180;
        const dx = Math.max(west - lon, 0, lon - east);
        const dy = Math.max(south - center.lat, 0, center.lat - north);
        const distance = Math.hypot(dx, dy);
        const limit = Math.max(OUTSIDE_MAX_ZOOM, MAX_ZOOM - distance * ZOOM_DROP_PER_DEGREE);

        return {
            zoom : Math.min(zoom, limit)
        };
    }

    function setLayerData() {
        if (!map || !isReady.value || !props.layers) {
            return;
        }

        const layers = toRaw(props.layers);

        for (const key of ['bathymetry', 'land', 'route']) {
            map.getSource(key)?.setData(toRaw(layers[key]));
        }
    }

    function updateBoat() {
        if (!map) {
            return;
        }

        if (!props.boat) {
            boatMarker?.remove();
            boatMarker = null;
            boatPosition = null;
            return;
        }

        if (!boatMarker) {
            boatMarker = new maplibregl.Marker({
                element : createBoatElement(),
                rotationAlignment : 'map'
            }).setLngLat([props.boat.lon, props.boat.lat]).addTo(map);
            boatMarker.setRotation(-20);
            boatPosition = {
                lon : props.boat.lon,
                lat : props.boat.lat
            };
            return;
        }

        animateBoat(props.boat);
    }

    function updateMode() {
        if (!map || !isReady.value) {
            return;
        }

        const explore = props.mode === 'explore';

        map.setPaintProperty('route', 'line-opacity', explore ? 0.8 : 1);
    }

    watch(() => props.base, applyBase);
    watch(() => props.layers, setLayerData);
    watch(() => props.mode, updateMode);
    watch(() => props.boat, updateBoat, {
        deep : true
    });
    watch(() => [props.focus, props.padding], () => applyFocus(true), {
        deep : true
    });

    onMounted(() => {
        map = new maplibregl.Map({
            container : container.value,
            style : buildStyle(),
            bounds : ARCHIPELAGO_BOUNDS,
            minZoom : 1.5,
            maxZoom : MAX_ZOOM,
            transformCameraUpdate : limitZoom,
            dragRotate : false,
            pitchWithRotate : false,
            touchPitch : false,
            // The credits for the map layers are on the about page
            attributionControl : false
        });

        map.touchZoomRotate.disableRotation();

        if (import.meta.env.DEV) {
            window.sibogaMap = map;
        }

        map.on('load', () => {
            isReady.value = true;
            setLayerData();
            updateMode();
            updateBoat();
            applyFocus(false);

            for (const label of SEA_LABELS) {
                createLabel(label, 'sea');
            }

            for (const label of LAND_LABELS) {
                createLabel(label, 'land');
            }

            applyBase();
        });
    });

    onBeforeUnmount(() => {
        cancelAnimationFrame(boatAnimation);
        map?.remove();
        map = null;
        labels = [];
    });

    defineExpose({
        recenter : () => applyFocus(true)
    });
</script>

<template>
    <div
        ref="container"
        class="el-map"
        v-bind:mode="mode"
        v-bind:base="base"></div>
</template>

<style lang="scss" scoped>
    .el-map {
        position: absolute;
        inset: 0;
        z-index: 0;
        isolation: isolate;
        background: var(--c-sea);

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

        // Light names with a shadow stay readable on the photo
        &[base="satellite"] {
            :deep(.map-label) {
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
            }

            :deep(.map-label--land) {
                color: #F2ECDB;
            }
        }

        :deep(.map-boat) {
            pointer-events: none;
            filter: drop-shadow(0 2px 3px rgba(8, 26, 44, 0.35));
        }
    }
</style>
