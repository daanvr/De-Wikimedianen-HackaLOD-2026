// The ship model of the explore mode, steered by the game instead of by the timeline. The game
// gives the position, heading and speed from its own physics; the model adds what it does in the
// explore mode on top: heel and pitch, the swell, sails trimmed to the monsoon, steam and wake.
// See explorer/ship.js.
import Ship from '@/explorer/ship.js';
import { distanceKm } from './geo.js';

const EARTH_KM = 40075.016;
// Size of the MapLibre world in pixels at zoom 0
const WORLD_PX = 512;
// The game sails faster than the timeline; this maps its speeds on the 0…1 the effects use
const SPEED_SCALE = 30;
// Speed changes in km/s per second that count as hard acceleration, for the bow and the smoke
const ACCELERATION_SCALE = 18;
// Further than this in one frame is a jump (a loaded game, a test), not sailing
const JUMP_KM = 200;

function pxPerKm(lat, zoom) {
    return WORLD_PX * 2 ** zoom / (EARTH_KM * Math.cos(lat * Math.PI / 180));
}

// Angle difference in degrees, between -180 and 180
function wrap(degrees) {
    return ((degrees % 360) + 540) % 360 - 180;
}

export default class GameShip extends Ship {
    constructor(start) {
        // The model wants a route; a route of one point will do, as the game steers the ship itself
        super([[0, start.lon, start.lat, 0], [1, start.lon, start.lat, 0]]);
        this.position = {
            lon : start.lon,
            lat : start.lat
        };
        this.heading = start.heading ?? 90;
        this.targetHeading = this.heading;
    }

    // One frame: the state of the game ship ({ lon, lat, heading, speed }), the zoom of the map and
    // the wind ({ from, strength }, see monsoonAt in explorer/ship.js)
    follow(state, dt, zoom, wind) {
        const kmPerPx = 1 / pxPerKm(state.lat, zoom);
        const travelled = distanceKm(this.position, state);
        const oldKm = this.km;
        const before = this.velocity;
        const turn = wrap(state.heading - this.heading);

        this.time += dt;

        if (travelled > JUMP_KM) {
            this.wake.length = 0;
            this.puffs.length = 0;
        }

        // The distance sailed stands in for the route kilometres of the explore mode
        this.km += Math.min(travelled, JUMP_KM);
        this.position = {
            lon : state.lon,
            lat : state.lat
        };
        this.velocity = state.speed;
        this.speed = 1 - Math.exp(-state.speed / SPEED_SCALE);
        this.acceleration += (Math.tanh((this.velocity - before) / dt / ACCELERATION_SCALE) - this.acceleration) * Math.min(1, dt * 5);
        this.heading = state.heading;
        this.targetHeading = state.heading;
        this.yawRate += (turn / dt - this.yawRate) * Math.min(1, dt * 8);
        this.yawSway = this.waves * (1.5 * Math.sin(this.time * 0.5) + 0.7 * Math.sin(this.time * 0.83 + 1)) * (1 - this.speed);

        this.updateWind(dt, wind);
        this.updateSails(dt);
        this.updateMotion(dt);
        this.updateSteam(dt, zoom);
        this.updateWater(dt, zoom, oldKm, kmPerPx);
    }
}
