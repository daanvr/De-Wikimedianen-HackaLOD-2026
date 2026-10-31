// The ship of the explore mode and the game, seen from above with the bow to the east
import maplibregl from 'maplibre-gl';

export const BOAT_SVG = `
    <svg width="72" height="36" viewBox="-46 -23 92 46">
        <path d="M-27,0 L-44,-7 M-27,0 L-44,7" stroke="#FBF8F1" stroke-width="1.4" fill="none" opacity="0.7"/>
        <path d="M-25,0 C-21,-6 8,-7 26,0 C8,7 -21,6 -25,0 Z" fill="#FBF8F1" stroke="#1B2433" stroke-width="1.3"/>
        <path d="M-9,-6 L-9,6 M8,-5 L8,5" stroke="#1B2433" stroke-width="1.3" fill="none"/>
        <circle r="2.4" fill="#A9512F"/>
    </svg>`;

export function createBoat() {
    const element = document.createElement('div');

    element.className = 'boat';
    element.setAttribute('aria-hidden', 'true');
    element.innerHTML = BOAT_SVG;

    return new maplibregl.Marker({
        element,
        rotationAlignment : 'map',
        pitchAlignment : 'map'
    });
}

// Runs a camera method of the map and resolves when the map has stopped moving
export function move(map, method, options) {
    return new Promise((resolve) => {
        map.once('moveend', resolve);
        map[method](options);
    });
}
