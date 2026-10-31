// Small helpers for distances and directions on the scale of the game: a few hundred
// kilometres near the equator, where a flat approximation is good enough.
import { LAYER_BOUNDS } from '@/services/sea-chart.js';

const KM_PER_DEGREE_LAT = 110.57;
const KM_PER_DEGREE_LON = 111.32;

export const [[WEST, SOUTH], [EAST, NORTH]] = LAYER_BOUNDS;

// Compass bearing in degrees (0 is north, 90 east) from one point to another
export function bearingTo(from, to) {
    const { east, north } = offsetKm(from, to);

    return (Math.atan2(east, north) * 180 / Math.PI + 360) % 360;
}

export function distanceKm(from, to) {
    const { east, north } = offsetKm(from, to);

    return Math.hypot(east, north);
}

// Moves a point a number of kilometres east and north
export function moveKm(point, east, north) {
    return {
        lon : point.lon + east / (KM_PER_DEGREE_LON * Math.cos(point.lat * Math.PI / 180)),
        lat : point.lat + north / KM_PER_DEGREE_LAT
    };
}

// Web Mercator y in [0, 1] for a latitude, as MapLibre uses it
export function mercatorY(lat) {
    const sin = Math.sin(lat * Math.PI / 180);

    return 0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI);
}

export function offsetKm(from, to) {
    const lat = (from.lat + to.lat) / 2;

    return {
        east : (to.lon - from.lon) * KM_PER_DEGREE_LON * Math.cos(lat * Math.PI / 180),
        north : (to.lat - from.lat) * KM_PER_DEGREE_LAT
    };
}

// Stable pseudo random number in [0, 1) for an integer seed and a salt, so every
// specimen gets the same place in every game
export function random(seed, salt = 0) {
    let h = (Math.imul(seed | 0, 0x9E3779B1) ^ Math.imul((seed / 4294967296) | 0, 0x85EBCA77) ^ Math.imul(salt + 1, 0xC2B2AE3D)) >>> 0;

    h = Math.imul(h ^ (h >>> 16), 0x7FEB352D);
    h = Math.imul(h ^ (h >>> 15), 0x846CA68B);
    h ^= h >>> 16;

    return (h >>> 0) / 4294967296;
}

// A closed ring around a point, for a circle on the map
export function ringAround(point, radiusKm, steps = 48) {
    const ring = [];

    for (let i = 0; i <= steps; i++) {
        const angle = i / steps * 2 * Math.PI;
        const next = moveKm(point, Math.sin(angle) * radiusKm, Math.cos(angle) * radiusKm);

        ring.push([next.lon, next.lat]);
    }

    return ring;
}
