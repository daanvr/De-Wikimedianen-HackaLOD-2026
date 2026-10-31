// A land mask of the research area: the detailed land of the sea chart, drawn once on a
// canvas in Web Mercator, about 1.5 km per pixel. After that, asking whether a point is
// land is a single lookup, whatever the map shows. Outside the area counts as land, so the
// edge of the game works like a coast.
import { EAST, NORTH, SOUTH, WEST, mercatorY, moveKm } from './geo.js';

const WIDTH = 2800;
// Radius in pixels around a point to estimate which way the coast faces
const NORMAL_RADIUS = 4;

export function createLandMask(land) {
    const top = mercatorY(NORTH);
    const bottom = mercatorY(SOUTH);
    const height = Math.round(WIDTH * (bottom - top) / ((EAST - WEST) / 360));
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d', {
        willReadFrequently : true
    });

    canvas.width = WIDTH;
    canvas.height = height;
    context.fillStyle = '#000';

    const toPixel = (lon, lat) => [
        (lon - WEST) / (EAST - WEST) * WIDTH,
        (mercatorY(lat) - top) / (bottom - top) * height
    ];

    for (const feature of land?.features ?? []) {
        const geometry = feature.geometry;
        const polygons = geometry?.type === 'Polygon' ? [geometry.coordinates] : geometry?.type === 'MultiPolygon' ? geometry.coordinates : [];

        for (const polygon of polygons) {
            context.beginPath();

            for (const ring of polygon) {
                ring.forEach(([lon, lat], i) => {
                    const [x, y] = toPixel(lon, lat);

                    if (i) {
                        context.lineTo(x, y);
                    } else {
                        context.moveTo(x, y);
                    }
                });
                context.closePath();
            }

            context.fill('evenodd');
        }
    }

    const pixels = context.getImageData(0, 0, WIDTH, height).data;
    const mask = new Uint8Array(WIDTH * height);

    for (let i = 0; i < mask.length; i++) {
        mask[i] = pixels[i * 4 + 3] > 127 ? 1 : 0;
    }

    function isLandPixel(x, y) {
        if (x < 0 || y < 0 || x >= WIDTH || y >= height) {
            return true;
        }

        return mask[(y | 0) * WIDTH + (x | 0)] === 1;
    }

    function isLand(point) {
        const [x, y] = toPixel(point.lon, point.lat);

        return isLandPixel(x, y);
    }

    // Unit vector (east, north) pointing away from the land near a point, or null in open water
    function normalAt(point) {
        const [x, y] = toPixel(point.lon, point.lat);
        let east = 0;
        let north = 0;

        for (let dy = -NORMAL_RADIUS; dy <= NORMAL_RADIUS; dy++) {
            for (let dx = -NORMAL_RADIUS; dx <= NORMAL_RADIUS; dx++) {
                if (isLandPixel(x + dx, y + dy)) {
                    east -= dx;
                    north += dy;
                }
            }
        }

        const length = Math.hypot(east, north);

        return length ? {
            east : east / length,
            north : north / length
        } : null;
    }

    // The nearest point in the water, looking in rings of growing size; null if there is none close
    function nearestWater(point, maxKm = 80) {
        if (!isLand(point)) {
            return point;
        }

        for (let radius = 1.5; radius <= maxKm; radius += 1.5) {
            for (let i = 0; i < 24; i++) {
                const angle = i / 24 * 2 * Math.PI;
                const candidate = moveKm(point, Math.sin(angle) * radius, Math.cos(angle) * radius);

                if (!isLand(candidate)) {
                    return candidate;
                }
            }
        }

        return null;
    }

    return {
        isLand,
        nearestWater,
        normalAt
    };
}

// A coarse grid of cells of 0.1 degree over the research area, with which cells are water.
// The fog remembers what was discovered per cell; the missions look for a route over it.
export const CELL_DEGREES = 0.1;

export function createWaterGrid(mask) {
    const columns = Math.round((EAST - WEST) / CELL_DEGREES);
    const rows = Math.round((NORTH - SOUTH) / CELL_DEGREES);
    const water = new Uint8Array(columns * rows);
    let waterCount = 0;

    for (let row = 0; row < rows; row++) {
        for (let column = 0; column < columns; column++) {
            const isWater = !mask.isLand(centerOf(column, row));

            water[row * columns + column] = isWater ? 1 : 0;
            waterCount += isWater ? 1 : 0;
        }
    }

    function centerOf(column, row) {
        return {
            lon : WEST + (column + 0.5) * CELL_DEGREES,
            lat : NORTH - (row + 0.5) * CELL_DEGREES
        };
    }

    function indexOf(point) {
        const column = Math.floor((point.lon - WEST) / CELL_DEGREES);
        const row = Math.floor((NORTH - point.lat) / CELL_DEGREES);

        if (column < 0 || row < 0 || column >= columns || row >= rows) {
            return -1;
        }

        return row * columns + column;
    }

    return {
        centerOf,
        columns,
        indexOf,
        rows,
        water,
        waterCount
    };
}
