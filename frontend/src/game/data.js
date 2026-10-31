// Loads the data of the game: every specimen of the gold set (not only the ones that are certainly
// from one station, as in the explore mode), the stations and the route. Uses the loaders of the
// explore mode, so a specimen in the game is the same object as one in the explore mode.
import { mediaUrl } from '@/services/data.js';
import { buildSpecimen, fetchExtra, fetchJson, rows } from '@/explorer/data.js';

const GOLD_URL = '/datasets/siboga-goud.json';
const ROUTE_URL = '/datasets/route-stations.json';

export async function loadGame() {
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
        const photo = stationExtras[station.nummer]?.image ?? null;

        return {
            ...station,
            index,
            photo : photo ? {
                ...photo,
                src : mediaUrl(photo.src),
                thumb : mediaUrl(photo.thumb ?? photo.src)
            } : null,
            specimens : []
        };
    });
    const byNumber = new Map(stations.map((station) => [station.nummer, station]));
    const specimens = rows(gold.specimens).map((row) => {
        const goldStation = row.station === null ? null : goldStations[row.station];
        const station = goldStation ? byNumber.get(goldStation.nummer) ?? null : null;
        const specimen = buildSpecimen(row, {
            extras : extra.specimens ?? {},
            gold,
            lists,
            museums,
            names,
            station
        });

        // Where the record itself says it was found, if it says so
        specimen.origin = row.lat === null || row.lon === null ? null : {
            lat : row.lat,
            lon : row.lon
        };

        station?.specimens.push(specimen);

        return specimen;
    });

    return {
        groups : [...new Set(specimens.map((specimen) => specimen.group))].sort(),
        line : route.lijn.rijen,
        specimens,
        stations
    };
}
