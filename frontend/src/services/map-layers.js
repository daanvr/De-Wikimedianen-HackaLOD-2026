// Static map layers, prepared by scripts/prepare_map.py and served from public/map/.
const LAYER_FILES = {
    bathymetry : '/map/bathymetry.geojson',
    land : '/map/land.geojson',
    route : '/map/route.geojson',
    stations : '/map/stations.geojson'
};

export async function loadMapLayers() {
    const entries = await Promise.all(
        Object.entries(LAYER_FILES).map(async ([key, url]) => {
            try {
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return [key, await response.json()];
            } catch (error) {
                console.warn(`Could not load map layer ${url}: ${error.message}`);

                return [key, {
                    type : 'FeatureCollection',
                    features : []
                }];
            }
        })
    );

    return Object.fromEntries(entries);
}
