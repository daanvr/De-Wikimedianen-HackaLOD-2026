// [[west, south], [east, north]] around a list of [lon, lat] points, as MapLibre's fitBounds wants it.
export function boundsOf(points) {
    const lons = points.map(([lon]) => lon);
    const lats = points.map(([, lat]) => lat);

    return [
        [Math.min(...lons), Math.min(...lats)],
        [Math.max(...lons), Math.max(...lats)]
    ];
}
