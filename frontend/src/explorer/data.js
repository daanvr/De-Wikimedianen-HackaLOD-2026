// Loads and joins the data of the explore mode: the gold set of Siboga specimens,
// the route with all stations and today's depth, and what the pipeline added per
// specimen (a local image and every identification). See docs/ontdekmodus.md.
import { mediaUrl } from '@/services/data.js';

const GOLD_URL = '/datasets/siboga-goud.json';
const ROUTE_URL = '/datasets/route-stations.json';
const EXTRA_URL = '/data/explorer.json';
const NATURALIS_URL = 'https://bioportal.naturalis.nl/specimen/';

async function fetchJson(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Could not load ${url}: HTTP ${response.status}`);
    }

    return response.json();
}

// The extra data is optional: without it there are no photos and only the identifications of the dataset
async function fetchExtra() {
    try {
        return await fetchJson(EXTRA_URL);
    } catch (error) {
        console.warn(`No explorer data from the pipeline: ${error.message}`);

        return {
            specimens : {}
        };
    }
}

function rows(table) {
    return table.rijen.map((row) => Object.fromEntries(table.velden.map((field, i) => [field, row[i]])));
}

function evidence(value, lists) {
    if (!value) {
        return null;
    }

    const [field, text, match] = value;

    return {
        field : lists.bewijs_veld[field],
        text : lists.bewijs_tekst[text],
        match
    };
}

// Identifications from the GBIF record, plus redeterminations the dataset read from the label text;
// without a GBIF record, the names from the dataset
function identificationsOf(row, extra, people) {
    if (extra?.identifications?.length) {
        const known = new Set(extra.identifications.flatMap((identification) => identification.by));
        const later = people(row.hergedetermineerd).filter((name) => !known.has(name));

        return [
            ...extra.identifications,
            ...later.map((name) => ({
                name : null,
                by : [name],
                date : null,
                remarks : 'Herdeterminatie, genoemd op het etiket',
                current : false
            }))
        ];
    }

    const result = [];

    if (row.gedetermineerd?.length) {
        result.push({
            name : row.wetenschappelijke_naam,
            by : people(row.gedetermineerd),
            date : null,
            current : !row.hergedetermineerd?.length
        });
    }

    if (row.hergedetermineerd?.length) {
        result.push({
            name : row.wetenschappelijke_naam,
            by : people(row.hergedetermineerd),
            date : null,
            current : true
        });
    }

    return result;
}

function buildSpecimen(row, context) {
    const { extras, gold, lists, museums, names, station } = context;
    const museum = museums[row.museum] ?? null;
    const isNaturalis = museum?.organisatie === 'Naturalis Biodiversity Center' && row.catalogus;
    const people = (list) => (list ?? []).map((i) => names[i]?.naam).filter(Boolean);
    const extra = extras[String(row.gbif)] ?? null;
    const dataset = gold.datasets.rijen[row.dataset];

    return {
        id : row.gbif,
        name : lists.soort[row.soort],
        scientificName : row.wetenschappelijke_naam,
        family : lists.familie[row.familie] ?? null,
        group : lists.groep[row.groep] ?? 'onbekend',
        museum,
        date : row.datum,
        // Collectors as the GBIF record writes them; without pipeline data, the names of the dataset
        collectors : extra?.recordedBy ?? people(row.verzameld),
        year : row.jaar,
        typeRank : row.type_rang,
        typeStatus : row.typestatus === null ? null : lists.typestatus[row.typestatus],
        typeNote : row.type_opmerking,
        // Alone (holotype and the like) or together with others (syntype) the specimen fixes the name
        isNameBearer : row.type_rang === 1 || row.type_rang === 2,
        identifications : identificationsOf(row, extra, people),
        catalog : row.catalogus,
        locality : row.vindplaats,
        license : lists.licentie[row.licentie] ?? null,
        dataset : dataset ? Object.fromEntries(gold.datasets.velden.map((field, i) => [field, dataset[i]])) : null,
        evidence : evidence(row.bewijs_station, lists),
        image : extra?.image ? {
            ...extra.image,
            src : mediaUrl(extra.image.src)
        } : null,
        gbifUrl : gold.url.gbif + row.gbif,
        naturalisUrl : isNaturalis ? NATURALIS_URL + encodeURIComponent(row.catalogus) : null,
        station
    };
}

export async function loadExplorer() {
    const [gold, route, extra] = await Promise.all([
        fetchJson(GOLD_URL),
        fetchJson(ROUTE_URL),
        fetchExtra()
    ]);
    const lists = gold.lijsten;
    const museums = rows(gold.musea);
    const names = rows(gold.namen);
    const goldStations = rows(gold.stations);
    const stationExtras = extra.stations ?? {};
    const stations = rows(route.stations).map((station, index) => {
        // The image of the station on Wikidata, mostly a photograph from the expedition
        const photo = stationExtras[station.nummer]?.image ?? null;

        return {
            ...station,
            index,
            photo : photo ? {
                ...photo,
                src : mediaUrl(photo.src),
                thumb : mediaUrl(photo.thumb ?? photo.src)
            } : null,
            specimens : [],
            collected : 0
        };
    });
    const byNumber = new Map(stations.map((station) => [station.nummer, station]));
    const specimens = [];

    for (const row of rows(gold.specimens)) {
        const goldStation = row.station === null ? null : goldStations[row.station];
        const station = goldStation ? byNumber.get(goldStation.nummer) : null;

        if (!station) {
            continue;
        }

        const specimen = buildSpecimen(row, {
            extras : extra.specimens ?? {},
            gold,
            lists,
            museums,
            names,
            station
        });

        station.specimens.push(specimen);
        specimens.push(specimen);
    }

    let total = 0;

    // Running total of specimens up to and including each station; stations are in route order
    for (const station of stations) {
        total += station.specimens.length;
        station.collected = total;
    }

    const line = route.lijn.rijen;

    return {
        stations,
        specimens,
        total,
        line,
        length : line[line.length - 1][0],
        wikidataUrl : gold.url.wikidata
    };
}

// Index of the first line point at or after a route km
export function lineIndexAt(line, km) {
    let low = 0;
    let high = line.length - 1;

    while (low < high) {
        const middle = (low + high) >> 1;

        if (line[middle][0] < km) {
            low = middle + 1;
        } else {
            high = middle;
        }
    }

    return low;
}

// Position and heading of the ship at a route km
export function pointAt(line, km) {
    const index = Math.max(1, lineIndexAt(line, km));
    const [kmA, lonA, latA] = line[index - 1];
    const [kmB, lonB, latB] = line[index];
    const fraction = kmB > kmA ? Math.max(0, Math.min(1, (km - kmA) / (kmB - kmA))) : 0;

    return {
        lon : lonA + (lonB - lonA) * fraction,
        lat : latA + (latB - latA) * fraction,
        bearing : Math.atan2(lonB - lonA, latB - latA) * 180 / Math.PI
    };
}

// Stable pseudo random number in [0, 1) for a seed, so specimens keep their place
export function seeded(seed) {
    const x = Math.sin(seed * 12.9898) * 43758.5453;

    return x - Math.floor(x);
}

// Index of the last station the ship has passed at a route km, or -1 before the first
export function stationIndexAt(stations, km) {
    let low = 0;
    let high = stations.length - 1;
    let result = -1;

    while (low <= high) {
        const middle = (low + high) >> 1;

        if (stations[middle].km <= km + 0.01) {
            result = middle;
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }

    return result;
}
