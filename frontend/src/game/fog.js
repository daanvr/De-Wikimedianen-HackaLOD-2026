// The fog of the undiscovered sea: an old paper chart over the research area that the ship wipes
// open as it sails. One canvas in Web Mercator, about 3 km per pixel, that the map draws as an
// image above the sea. What was discovered is remembered per cell of the water grid.
import paperUrl from '@/explorer/media/paper.png';
import { EAST, NORTH, SOUTH, WEST, distanceKm, mercatorY, random } from './geo.js';

const WIDTH = 1400;
export const REVEAL_KM = 110;
// Fully clear within this part of the radius, fading out beyond it
const SOFT_EDGE = 0.55;
// Only wipe again after the ship has moved this far
const STEP_KM = 4;
const KM_PER_DEGREE = 111.32;

function loadImage(url) {
    return new Promise((resolve) => {
        const image = new Image();

        image.onload = () => resolve(image);
        image.onerror = () => resolve(null);
        image.src = url;
    });
}

function drawRose(context, x, y, size) {
    context.save();
    context.translate(x, y);
    context.strokeStyle = 'rgba(110, 98, 72, 0.5)';
    context.fillStyle = 'rgba(169, 81, 47, 0.35)';
    context.lineWidth = 1;
    context.beginPath();
    context.arc(0, 0, size, 0, 2 * Math.PI);
    context.stroke();

    for (let i = 0; i < 8; i++) {
        const length = i % 2 ? size * 0.55 : size * 1.15;

        context.rotate(Math.PI / 4);
        context.beginPath();
        context.moveTo(0, -length);
        context.lineTo(size * 0.14, 0);
        context.lineTo(-size * 0.14, 0);
        context.closePath();

        if (i % 2) {
            context.stroke();
        } else {
            context.fill();
        }
    }

    context.restore();
}

// Paper, little waves, a few compass roses and the words of the old map makers
function drawPaper(context, width, height, paper) {
    context.globalCompositeOperation = 'source-over';
    context.fillStyle = '#EAE0C6';
    context.fillRect(0, 0, width, height);

    if (paper) {
        context.globalAlpha = 0.55;
        context.fillStyle = context.createPattern(paper, 'repeat');
        context.fillRect(0, 0, width, height);
        context.globalAlpha = 1;
    }

    context.strokeStyle = 'rgba(110, 98, 72, 0.32)';
    context.lineWidth = 1;

    for (let i = 0; i < 700; i++) {
        const x = random(i, 1) * width;
        const y = random(i, 2) * height;

        context.beginPath();
        context.moveTo(x, y);
        context.quadraticCurveTo(x + 3, y - 3, x + 6, y);
        context.quadraticCurveTo(x + 9, y + 3, x + 12, y);
        context.stroke();
    }

    drawRose(context, width * 0.18, height * 0.3, 34);
    drawRose(context, width * 0.62, height * 0.78, 28);
    drawRose(context, width * 0.86, height * 0.22, 30);

    context.fillStyle = 'rgba(110, 98, 72, 0.6)';
    context.font = 'italic 22px "Old Standard TT", Georgia, serif';
    context.textAlign = 'center';

    for (const [x, y, angle] of [[0.35, 0.55, -0.08], [0.75, 0.45, 0.06], [0.12, 0.85, 0.04], [0.5, 0.12, -0.05]]) {
        context.save();
        context.translate(width * x, height * y);
        context.rotate(angle);
        context.fillText('Terra incognita', 0, 0);
        context.restore();
    }

    // A double frame along the edge of the chart
    context.strokeStyle = 'rgba(94, 59, 26, 0.7)';
    context.lineWidth = 6;
    context.strokeRect(3, 3, width - 6, height - 6);
    context.lineWidth = 1.5;
    context.strokeRect(12, 12, width - 24, height - 24);
}

export async function createFog(grid) {
    const top = mercatorY(NORTH);
    const bottom = mercatorY(SOUTH);
    const height = Math.round(WIDTH * (bottom - top) / ((EAST - WEST) / 360));
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const revealed = new Uint8Array(grid.columns * grid.rows);
    const cellRadius = Math.ceil(REVEAL_KM / (KM_PER_DEGREE * 0.1)) + 1;
    let revealedWater = 0;
    let last = null;

    canvas.width = WIDTH;
    canvas.height = height;

    const [paper] = await Promise.all([
        loadImage(paperUrl),
        document.fonts?.ready
    ]);

    drawPaper(context, WIDTH, height, paper);

    function clearCircle(point, radiusKm, isSoft) {
        const x = (point.lon - WEST) / (EAST - WEST) * WIDTH;
        const y = (mercatorY(point.lat) - top) / (bottom - top) * height;
        const kmPerPixel = (EAST - WEST) * KM_PER_DEGREE * Math.cos(point.lat * Math.PI / 180) / WIDTH;
        const radius = radiusKm / kmPerPixel;

        context.globalCompositeOperation = 'destination-out';

        if (isSoft) {
            const gradient = context.createRadialGradient(x, y, radius * SOFT_EDGE, x, y, radius);

            gradient.addColorStop(0, 'rgba(0, 0, 0, 1)');
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
            context.fillStyle = gradient;
        } else {
            context.fillStyle = '#000';
        }

        context.beginPath();
        context.arc(x, y, radius, 0, 2 * Math.PI);
        context.fill();
        context.globalCompositeOperation = 'source-over';
    }

    function markCell(index) {
        if (index < 0 || revealed[index]) {
            return;
        }

        revealed[index] = 1;
        revealedWater += grid.water[index];
    }

    // Wipes the fog open around the ship; returns true when the canvas changed
    function reveal(point) {
        if (last && distanceKm(last, point) < STEP_KM) {
            return false;
        }

        last = {
            lon : point.lon,
            lat : point.lat
        };
        clearCircle(point, REVEAL_KM, true);

        const center = grid.indexOf(point);

        if (center < 0) {
            return true;
        }

        const column = center % grid.columns;
        const row = Math.floor(center / grid.columns);

        for (let dy = -cellRadius; dy <= cellRadius; dy++) {
            for (let dx = -cellRadius; dx <= cellRadius; dx++) {
                const c = column + dx;
                const r = row + dy;

                if (c < 0 || r < 0 || c >= grid.columns || r >= grid.rows) {
                    continue;
                }

                // Count a cell once the clear part of the circle covers it
                if (distanceKm(point, grid.centerOf(c, r)) < REVEAL_KM * 0.8) {
                    markCell(r * grid.columns + c);
                }
            }
        }

        return true;
    }

    // The discovered cells as base64, one bit per cell
    function encode() {
        const bytes = new Uint8Array(Math.ceil(revealed.length / 8));

        revealed.forEach((value, i) => {
            if (value) {
                bytes[i >> 3] |= 1 << (i & 7);
            }
        });

        let text = '';

        for (const byte of bytes) {
            text += String.fromCharCode(byte);
        }

        return btoa(text);
    }

    function restore(encoded) {
        if (!encoded) {
            return;
        }

        try {
            const text = atob(encoded);

            for (let i = 0; i < revealed.length; i++) {
                if (text.charCodeAt(i >> 3) & (1 << (i & 7))) {
                    markCell(i);

                    const point = grid.centerOf(i % grid.columns, Math.floor(i / grid.columns));

                    clearCircle(point, 9, false);
                }
            }
        } catch (error) {
            console.warn('Could not restore the discovered sea');
        }
    }

    // Covers the whole sea again, for a new voyage
    function reset() {
        revealed.fill(0);
        revealedWater = 0;
        last = null;
        drawPaper(context, WIDTH, height, paper);
    }

    // Part of the water of the research area that has been discovered, from 0 to 1
    function share() {
        return grid.waterCount ? revealedWater / grid.waterCount : 0;
    }

    return {
        canvas,
        encode,
        reset,
        restore,
        reveal,
        share
    };
}
