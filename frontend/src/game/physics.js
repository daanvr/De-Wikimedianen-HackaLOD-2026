// The ship of the game: a boiler that drives the speed, a rudder that turns the heading, and
// coasts the ship bounces off. A pure step function, so the numbers are easy to tune.
import { moveKm } from './geo.js';

// Boiler pressure from 0 to 1: it drops by itself, but never below the floor, so the ship always moves
export const PRESSURE_FLOOR = 0.25;
const PRESSURE_DECAY = 0.05;
export const SHOVEL_PRESSURE = 0.12;
// Above this pressure for too long, the safety valve blows and the pressure drops
export const OVERHEAT_PRESSURE = 0.92;
const OVERHEAT_SECONDS = 1.2;
const VALVE_PRESSURE = 0.5;

// Speed in kilometres per second of play, at the floor and at full pressure
const MIN_SPEED = 8;
const MAX_SPEED = 45;
// Seconds the ship takes to get most of the way to a new speed
const SPEED_LAG = 1.6;

// Degrees per second at full rudder, reached from this speed on; slower ships turn slower
const TURN_RATE = 50;
const TURN_SPEED = 16;

// Part of the speed the ship keeps when it bounces off a coast
const BOUNCE_KEEP = 0.85;
const BOUNCE_COOLDOWN = 0.6;

export function createShip(start) {
    return {
        lon : start.lon,
        lat : start.lat,
        heading : start.heading ?? 90,
        speed : MIN_SPEED,
        pressure : PRESSURE_FLOOR,
        overheat : 0,
        bounceTimer : 0
    };
}

// Adds a shovel of coal to the boiler
export function shovel(ship) {
    ship.pressure = Math.min(1, ship.pressure + SHOVEL_PRESSURE);
}

// Advances the ship by dt seconds; wheel is the helm from -1 (port) to 1 (starboard).
// Returns the events of this step: 'valve' when the safety valve blows, 'bump' on a coast.
export function step(ship, wheel, dt, land) {
    const events = [];

    // Boiler
    ship.pressure = Math.max(PRESSURE_FLOOR, ship.pressure - PRESSURE_DECAY * dt);

    if (ship.pressure > OVERHEAT_PRESSURE) {
        ship.overheat += dt;

        if (ship.overheat > OVERHEAT_SECONDS) {
            ship.pressure = VALVE_PRESSURE;
            ship.overheat = 0;
            events.push('valve');
        }
    } else {
        ship.overheat = 0;
    }

    // Speed follows the pressure, with some inertia
    const level = (ship.pressure - PRESSURE_FLOOR) / (1 - PRESSURE_FLOOR);
    const target = MIN_SPEED + (MAX_SPEED - MIN_SPEED) * level;

    ship.speed += (target - ship.speed) * (1 - Math.exp(-dt / SPEED_LAG));

    // Rudder
    const steering = Math.min(1, ship.speed / TURN_SPEED);

    ship.heading = (ship.heading + wheel * TURN_RATE * steering * dt + 360) % 360;
    ship.bounceTimer = Math.max(0, ship.bounceTimer - dt);

    // Movement, bouncing off the land
    const radians = ship.heading * Math.PI / 180;
    const east = Math.sin(radians);
    const north = Math.cos(radians);
    const next = moveKm(ship, east * ship.speed * dt, north * ship.speed * dt);

    if (!land || !land.isLand(next)) {
        ship.lon = next.lon;
        ship.lat = next.lat;

        return events;
    }

    const normal = land.normalAt(next) ?? {
        east : -east,
        north : -north
    };
    const dot = east * normal.east + north * normal.north;

    if (dot < 0) {
        const bounced = {
            east : east - 2 * dot * normal.east,
            north : north - 2 * dot * normal.north
        };

        ship.heading = (Math.atan2(bounced.east, bounced.north) * 180 / Math.PI + 360) % 360;
    }

    ship.speed *= BOUNCE_KEEP;

    // Push the ship back into open water
    const pushed = moveKm(ship, normal.east * 0.4, normal.north * 0.4);
    const water = land.isLand(pushed) ? land.nearestWater(pushed) : pushed;

    if (water) {
        ship.lon = water.lon;
        ship.lat = water.lat;
    }

    if (!ship.bounceTimer) {
        ship.bounceTimer = BOUNCE_COOLDOWN;
        events.push('bump');
    }

    return events;
}
