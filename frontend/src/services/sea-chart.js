// The blue sea chart that every map of the site draws: detailed layers for the research area
// (prepared by scripts/prepare_map.py), coarse layers for the rest of the world, and names.

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
const EMPTY = {
    type : 'FeatureCollection',
    features : []
};

// The research area: the extent of the detailed layers in public/map/. Outside it the
// coarse world layers take over, and you can only zoom in to about province level.
export const LAYER_BOUNDS = [[104, -16], [142, 10]];
const OUTSIDE_MAX_ZOOM = 6;
// How fast the zoom limit drops when you pan out of the research area, in zoom levels per degree
const ZOOM_DROP_PER_DEGREE = 2;

export const SEA_LABELS = [
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

export const LAND_LABELS = [
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

// Allows deep zoom only in the research area: the farther the centre is outside it, the lower the limit.
// Returns a function for the transformCameraUpdate option of MapLibre.
export function limitZoom(maxZoom) {
    return ({ center, zoom }) => {
        const [[west, south], [east, north]] = LAYER_BOUNDS;
        const lon = ((center.lng + 540) % 360) - 180;
        const dx = Math.max(west - lon, 0, lon - east);
        const dy = Math.max(south - center.lat, 0, center.lat - north);
        const distance = Math.hypot(dx, dy);
        const limit = Math.max(OUTSIDE_MAX_ZOOM, maxZoom - distance * ZOOM_DROP_PER_DEGREE);

        return {
            zoom : Math.min(zoom, limit)
        };
    };
}

// Bottom to top: sea, depth, land and coastline; other layers go on top
export function seaChartLayers() {
    const depthColor = ['match', ['get', 'depth'], ...DEPTH_COLORS, '#1F5280'];
    const isLine = ['==', ['geometry-type'], 'LineString'];
    const isPolygon = ['==', ['geometry-type'], 'Polygon'];

    return [
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
                'fill-color' : depthColor,
                'fill-antialias' : false
            }
        },
        {
            id : 'depth',
            type : 'fill',
            source : 'bathymetry',
            paint : {
                'fill-color' : depthColor,
                'fill-antialias' : false
            }
        },
        {
            id : 'land-lagoon',
            type : 'line',
            source : 'land',
            filter : isLine,
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
            filter : isPolygon,
            paint : {
                'fill-color' : '#F2ECDB'
            }
        },
        {
            id : 'world-land',
            type : 'fill',
            source : 'worldLand',
            filter : isPolygon,
            paint : {
                'fill-color' : '#F2ECDB'
            }
        },
        {
            id : 'world-land-outline',
            type : 'line',
            source : 'worldLand',
            filter : isLine,
            paint : {
                'line-color' : '#7C6E52',
                'line-width' : 0.5
            }
        },
        {
            id : 'land-outline',
            type : 'line',
            source : 'land',
            filter : isLine,
            paint : {
                'line-color' : '#7C6E52',
                'line-width' : ['interpolate', ['linear'], ['zoom'], 4, 0.5, 9, 1.2]
            }
        }
    ];
}

// The detailed layers come from the store; MapLibre loads the coarse world layers itself, so the site does not wait for them
export function seaChartSources(layers) {
    return {
        bathymetry : {
            type : 'geojson',
            data : layers?.bathymetry ?? EMPTY
        },
        land : {
            type : 'geojson',
            data : layers?.land ?? EMPTY
        },
        worldBathymetry : {
            type : 'geojson',
            data : '/map/world-bathymetry.geojson'
        },
        worldLand : {
            type : 'geojson',
            data : '/map/world-land.geojson'
        }
    };
}
