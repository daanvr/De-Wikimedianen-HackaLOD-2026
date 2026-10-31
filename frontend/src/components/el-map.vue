<script setup>
    import maplibregl from 'maplibre-gl';
    import { onBeforeUnmount, onMounted, ref, toRaw, watch } from 'vue';
    import { LAND_LABELS, SEA_LABELS, limitZoom, seaChartLayers, seaChartSources } from '@/services/sea-chart.js';

    const ARCHIPELAGO_BOUNDS = [[106, -12], [136, 6]];
    const MAX_ZOOM = 11;
    const TRAVEL_MS = 2600;
    // How far the map zooms in on the markers of a chapter, also when there is only one
    const MARKERS_MAX_ZOOM = 8;
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

    const emit = defineEmits(['open']);

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
        markers : {
            type : Array,
            default : () => []
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
    let chapterMarkers = [];
    let focusMarker = null;

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

        // A focus without a centre shows its bounds, or else the whole route
        if (props.focus?.lon === undefined) {
            map.fitBounds(props.focus?.bounds ?? ARCHIPELAGO_BOUNDS, {
                padding : {
                    top : padding.top + 48,
                    right : padding.right + 48,
                    bottom : padding.bottom + 48,
                    left : padding.left + 48
                },
                maxZoom : MARKERS_MAX_ZOOM,
                duration : animate ? 1400 : 0
            });
            return;
        }

        map.easeTo({
            center : [props.focus.lon, props.focus.lat],
            zoom : props.focus.zoom ?? map.getZoom(),
            padding,
            duration : animate ? (props.focus.duration ?? 1600) : 0,
            essential : true
        });
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
                ...seaChartSources(layers),
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
                ...seaChartLayers(),
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

    function createChapterMarker(marker) {
        const element = document.createElement(marker.ref ? 'button' : 'div');

        element.className = 'map-marker';
        element.append(createMarkerLabel(marker.label, marker.kicker));

        if (marker.ref) {
            element.type = 'button';
            element.setAttribute('is-link', '');
            element.addEventListener('click', () => emit('open', marker.ref));
        }

        return new maplibregl.Marker({
            element,
            anchor : 'center'
        }).setLngLat([marker.lon, marker.lat]).addTo(map);
    }

    function createMarkerLabel(text, kicker) {
        const label = document.createElement('span');

        label.className = 'map-marker__label';

        if (kicker) {
            const small = document.createElement('small');

            small.className = 'map-marker__kicker';
            small.textContent = kicker;
            label.append(small);
        }

        label.append(text ?? '');

        return label;
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

    function setLayerData() {
        if (!map || !isReady.value || !props.layers) {
            return;
        }

        const layers = toRaw(props.layers);

        for (const key of ['bathymetry', 'land', 'route']) {
            map.getSource(key)?.setData(toRaw(layers[key]));
        }
    }

    function updateMarkers() {
        if (!map || !isReady.value) {
            return;
        }

        for (const marker of chapterMarkers) {
            marker.remove();
        }

        chapterMarkers = props.markers.map(createChapterMarker);
    }

    // The place the map zooms in on, e.g. the location of a record, with its name next to it
    function updateFocusMarker() {
        if (!map || !isReady.value) {
            return;
        }

        focusMarker?.remove();
        focusMarker = null;

        const focus = props.focus;

        if (focus?.lon === undefined || !focus.label) {
            return;
        }

        const element = document.createElement('div');

        element.className = 'map-marker';
        element.setAttribute('is-focus', '');
        element.append(createMarkerLabel(focus.label, focus.kicker));

        focusMarker = new maplibregl.Marker({
            element,
            anchor : 'center'
        }).setLngLat([focus.lon, focus.lat]).addTo(map);
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
    watch(() => props.markers, updateMarkers);
    watch(() => props.focus, updateFocusMarker);
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
            transformCameraUpdate : limitZoom(MAX_ZOOM),
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
            updateMarkers();
            updateFocusMarker();
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
        map?.remove();
        map = null;
        labels = [];
        chapterMarkers = [];
        focusMarker = null;
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

        // A place from the chapter's GeoJSON; only clickable if it links to a page
        :deep(.map-marker) {
            position: relative;
            width: 1.2rem;
            height: 1.2rem;
            padding: 0;
            border: 2px solid var(--c-paper);
            border-radius: 50%;
            background: var(--c-terracotta);
            box-shadow: 0 1px 3px rgba(8, 26, 44, 0.4);
            pointer-events: none;
        }

        :deep(.map-marker[is-link]) {
            pointer-events: auto;
            cursor: pointer;
        }

        :deep(.map-marker__label) {
            position: absolute;
            top: 50%;
            left: calc(100% + 0.6rem);
            transform: translateY(-50%);
            white-space: nowrap;
            font-family: var(--font-header);
            font-style: italic;
            font-size: 1.4rem;
            color: var(--c-ink);
            text-shadow: 0 0 3px var(--c-paper), 0 0 6px var(--c-paper);
        }

        // The place being looked at: larger, with a ring around it
        :deep(.map-marker[is-focus]) {
            z-index: 1;
            width: 1.4rem;
            height: 1.4rem;
            box-shadow: 0 0 0 0.35rem rgba(169, 81, 47, 0.35), 0 1px 3px rgba(8, 26, 44, 0.4);
        }

        // On a paper card, so it stays readable on top of the old map
        :deep(.map-marker[is-focus] .map-marker__label) {
            left: calc(100% + 0.9rem);
            padding: 0.5rem 0.9rem;
            border-radius: 0.4rem;
            background: var(--c-paper);
            box-shadow: 0 1px 4px rgba(8, 26, 44, 0.35);
            font-size: 1.7rem;
            line-height: 1.2;
            text-shadow: none;
        }

        :deep(.map-marker__kicker) {
            display: block;
            font-family: var(--font-text);
            font-style: normal;
            font-size: 1.05rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--c-terracotta);
        }

        :deep(.map-marker[is-link]:hover .map-marker__label),
        :deep(.map-marker[is-link]:focus-visible .map-marker__label) {
            text-decoration: underline;
        }

        // Light names with a shadow stay readable on the photo
        &[base="satellite"] {
            :deep(.map-label),
            :deep(.map-marker__label) {
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
            }

            :deep(.map-label--land),
            :deep(.map-marker__label) {
                color: #F2ECDB;
            }

            :deep(.map-marker[is-focus] .map-marker__label) {
                color: var(--c-ink);
                text-shadow: none;
            }
        }
    }
</style>
