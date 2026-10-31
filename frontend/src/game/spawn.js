// Where every specimen floats in the game. Made up, but close to where it could have been:
// around its station if it has one, around the place in its record if that has one, and
// otherwise around where the Siboga was on the day it was collected. The same specimen always
// gets the same place. See docs/spelmodus.md.
import { pointAt } from '@/explorer/data.js';
import { EAST, NORTH, SOUTH, WEST, moveKm, random } from './geo.js';

const STATION_SPREAD_KM = 15;
const ORIGIN_SPREAD_KM = 15;
const DAY_SPREAD_KM = 60;
const TRIES = 8;

function dayOf(date) {
    return date ? Date.parse(`${date.slice(0, 10)}T00:00:00Z`) : NaN;
}

function isInside(point) {
    return point.lon > WEST && point.lon < EAST && point.lat > SOUTH && point.lat < NORTH;
}

// Route km of the ship on a day: a station of that day, or between the stations before and after
function kmOnDay(anchors, day, seed) {
    const same = anchors.filter((anchor) => anchor.from <= day && day <= anchor.to);

    if (same.length) {
        return same[Math.floor(random(seed, 7) * same.length)].km;
    }

    let before = null;
    let after = null;

    for (const anchor of anchors) {
        if (anchor.to < day) {
            before = anchor;
        } else if (anchor.from > day && !after) {
            after = anchor;
        }
    }

    if (!before || !after) {
        return (before ?? after).km;
    }

    const fraction = (day - before.to) / (after.from - before.to);

    return before.km + (after.km - before.km) * fraction;
}

function scatter(base, spreadKm, seed, land) {
    for (let attempt = 0; attempt < TRIES; attempt++) {
        const angle = random(seed, attempt * 2) * 2 * Math.PI;
        const distance = Math.sqrt(random(seed, attempt * 2 + 1)) * spreadKm;
        const point = moveKm(base, Math.sin(angle) * distance, Math.cos(angle) * distance);

        if (isInside(point) && !land.isLand(point)) {
            return point;
        }
    }

    return land.nearestWater(base, 120) ?? base;
}

export function placeSpecimens(specimens, stations, line, land) {
    const anchors = stations
        .filter((station) => station.datum)
        .map((station) => ({
            from : dayOf(station.datum),
            to : station.tot ? dayOf(station.tot) : dayOf(station.datum),
            km : station.km
        }))
        .sort((a, b) => a.from - b.from);

    for (const specimen of specimens) {
        const seed = specimen.id;
        let base = null;
        let spread = DAY_SPREAD_KM;

        if (specimen.station) {
            base = {
                lon : specimen.station.lon,
                lat : specimen.station.lat
            };
            spread = STATION_SPREAD_KM;
        } else if (specimen.origin && isInside(specimen.origin)) {
            base = specimen.origin;
            spread = ORIGIN_SPREAD_KM;
        } else {
            const day = dayOf(specimen.date);
            const km = Number.isNaN(day) ? random(seed, 9) * line[line.length - 1][0] : kmOnDay(anchors, day, seed);

            base = pointAt(line, km);
        }

        specimen.place = scatter(base, spread, seed, land);
        specimen.phase = random(seed, 99) * 2 * Math.PI;
    }
}
