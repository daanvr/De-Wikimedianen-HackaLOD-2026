// Mission cards: a crew member asks for a specimen you do not have yet, somewhere you can get to.
// The target lies at a fair distance, in the water, and a search over the water grid checks that
// a route by sea is not much longer than the straight line.
import { SEA_LABELS } from '@/services/sea-chart.js';
import { groupName } from '@/explorer/groups.js';
import { distanceKm, moveKm, random } from './geo.js';
import { MISSION_TEMPLATES, RARITY_PHRASES, fill } from './texts.js';

const MIN_KM = 150;
const MAX_KM = 400;
// When the album asks for a group, anything from close by to far away will do
const SEEK_MIN_KM = 30;
const SEEK_MAX_KM = 900;
const MAX_DETOUR = 1.8;
const TARGET_RADIUS_KM = 25;
const CANDIDATES = 14;
const SEARCH_MARGIN = 30;
const ALGAE = new Set(['Roodwieren', 'Bruinwieren', 'Groenwieren', 'Blauwalgen']);
const GIVERS = ['weber', 'versluys', 'nierstrasz', 'schmidt'];
const WEIGHTS = {
    common : 1,
    uncommon : 1.5,
    rare : 2.2,
    nameBearer : 2.2
};

// A small binary heap of [cost, index], for the route search
function createHeap() {
    const items = [];

    function pop() {
        const top = items[0];
        const last = items.pop();

        if (items.length) {
            items[0] = last;

            let i = 0;

            for (;;) {
                const left = i * 2 + 1;
                const right = left + 1;
                let smallest = i;

                if (left < items.length && items[left][0] < items[smallest][0]) {
                    smallest = left;
                }

                if (right < items.length && items[right][0] < items[smallest][0]) {
                    smallest = right;
                }

                if (smallest === i) {
                    break;
                }

                [items[i], items[smallest]] = [items[smallest], items[i]];
                i = smallest;
            }
        }

        return top;
    }

    function push(item) {
        items.push(item);

        let i = items.length - 1;

        while (i > 0) {
            const parent = (i - 1) >> 1;

            if (items[parent][0] <= items[i][0]) {
                break;
            }

            [items[i], items[parent]] = [items[parent], items[i]];
            i = parent;
        }
    }

    return {
        get size() {
            return items.length;
        },
        pop,
        push
    };
}

function nearestWaterCell(grid, point) {
    const index = grid.indexOf(point);

    if (index < 0) {
        return -1;
    }

    if (grid.water[index]) {
        return index;
    }

    const column = index % grid.columns;
    const row = Math.floor(index / grid.columns);

    for (let radius = 1; radius <= 4; radius++) {
        for (let dy = -radius; dy <= radius; dy++) {
            for (let dx = -radius; dx <= radius; dx++) {
                const c = column + dx;
                const r = row + dy;

                if (c >= 0 && r >= 0 && c < grid.columns && r < grid.rows && grid.water[r * grid.columns + c]) {
                    return r * grid.columns + c;
                }
            }
        }
    }

    return -1;
}

// Length in km of the shortest route over water cells, or Infinity when there is none
export function seaRouteKm(grid, from, to) {
    const start = nearestWaterCell(grid, from);
    const goal = nearestWaterCell(grid, to);

    if (start < 0 || goal < 0) {
        return Infinity;
    }

    const columns = grid.columns;
    const minColumn = Math.max(0, Math.min(start % columns, goal % columns) - SEARCH_MARGIN);
    const maxColumn = Math.min(columns - 1, Math.max(start % columns, goal % columns) + SEARCH_MARGIN);
    const minRow = Math.max(0, Math.min(Math.floor(start / columns), Math.floor(goal / columns)) - SEARCH_MARGIN);
    const maxRow = Math.min(grid.rows - 1, Math.max(Math.floor(start / columns), Math.floor(goal / columns)) + SEARCH_MARGIN);
    const costs = new Map([[start, 0]]);
    const heap = createHeap();
    const goalPoint = grid.centerOf(goal % columns, Math.floor(goal / columns));

    heap.push([distanceKm(grid.centerOf(start % columns, Math.floor(start / columns)), goalPoint), start]);

    while (heap.size) {
        const [, index] = heap.pop();
        const cost = costs.get(index);

        if (index === goal) {
            return cost;
        }

        const column = index % columns;
        const row = Math.floor(index / columns);
        const here = grid.centerOf(column, row);

        for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {
                const c = column + dx;
                const r = row + dy;

                if ((!dx && !dy) || c < minColumn || c > maxColumn || r < minRow || r > maxRow) {
                    continue;
                }

                const next = r * columns + c;

                if (!grid.water[next]) {
                    continue;
                }

                const there = grid.centerOf(c, r);
                const nextCost = cost + distanceKm(here, there);

                if (nextCost < (costs.get(next) ?? Infinity)) {
                    costs.set(next, nextCost);
                    // A* with the straight line to the goal as estimate
                    heap.push([nextCost + distanceKm(there, goalPoint), next]);
                }
            }
        }
    }

    return Infinity;
}

function seaName(point) {
    let best = null;
    let bestDistance = Infinity;

    for (const label of SEA_LABELS) {
        const distance = distanceKm(point, label);

        if (distance < bestDistance) {
            best = label;
            bestDistance = distance;
        }
    }

    return best && bestDistance < 500 ? `de ${best.text}` : 'deze buurt';
}

// A new mission near the ship, optionally for one group; null when nothing reachable is left
export function createMission({ ship, specimens, collected, grid, group = null, missingGroups, seed }) {
    const minKm = group ? SEEK_MIN_KM : MIN_KM;
    const maxKm = group ? SEEK_MAX_KM : MAX_KM;
    const candidates = [];

    for (const specimen of specimens) {
        if (collected.has(specimen.id) || (group && specimen.group !== group)) {
            continue;
        }

        const distance = distanceKm(ship, specimen.place);

        if (distance < minKm || distance > maxKm) {
            continue;
        }

        const wanted = missingGroups?.has(specimen.group) ? 2 : 1;
        // Closer is a little more likely, so missions do not always send you across the sea
        const score = random(specimen.id, seed) * WEIGHTS[specimen.rarity] * wanted * (1.4 - distance / maxKm);

        candidates.push([score, specimen, distance]);
    }

    candidates.sort((a, b) => b[0] - a[0]);

    for (const [, specimen, distance] of candidates.slice(0, CANDIDATES)) {
        const route = seaRouteKm(grid, ship, specimen.place);

        if (route > distance * MAX_DETOUR + 30) {
            continue;
        }

        const angle = random(specimen.id, seed + 1) * 2 * Math.PI;
        const offset = random(specimen.id, seed + 2) * TARGET_RADIUS_KM * 0.55;
        const center = moveKm(specimen.place, Math.sin(angle) * offset, Math.cos(angle) * offset);
        const giver = ALGAE.has(specimen.group) ? 'anna' : GIVERS[Math.floor(random(specimen.id, seed + 3) * GIVERS.length)];
        const template = MISSION_TEMPLATES[Math.floor(random(specimen.id, seed + 4) * MISSION_TEMPLATES.length)];

        return {
            specimenId : specimen.id,
            group : specimen.group,
            rarity : specimen.rarity,
            center,
            radiusKm : TARGET_RADIUS_KM,
            giver,
            text : fill(template, {
                sea : seaName(center),
                rarity : RARITY_PHRASES[specimen.rarity],
                group : groupName(specimen.group).toLowerCase()
            })
        };
    }

    return null;
}
