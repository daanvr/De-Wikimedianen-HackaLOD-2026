// The Siboga on the explore map as a small physical model, drawn on a canvas over the map.
// The ship trails the timeline with inertia, follows the route by distance travelled (so it
// takes the same curve at every playing speed), heels and pitches on damped springs, rides
// the swell, sets and trims its schooner sails to the monsoon and puffs steam from its
// funnel. It keeps the same size in pixels at every zoom, as the marker before it did.
import { pointAt } from './data.js';

const DEG = Math.PI / 180;
const EARTH_KM = 40075.016;
// Size of the MapLibre world in pixels at zoom 0
const WORLD_PX = 512;
// Route kilometres per second at 1×, as on the timeline
const PLAY_KM_PER_SECOND = 12;
// Hull length in pixels: one and a half times the hull of the old marker
const LENGTH = 60;
// Seconds the ship lags behind the timeline; also how long it takes to gather way and to stop
const INERTIA = 1.2;
// A jump on the timeline longer than this is not sailed but made at once
const SNAP_KM = 1500;
// Heel and pitch are drawn larger than they are, or they would hardly show from above
const LEAN_EXAGGERATION = 1.6;
// A slight oblique view, so masts, funnel and sails show their height
const TILT = 0.3;
// Shadows fall to the lower right, per unit of height
const SUN = [0.42, 0.55];
const WIND_STRENGTH = 0.6;
const ROLL_FREQUENCY = 0.55;
const ROLL_DAMPING = 0.16;
const WIND_HEEL = 5;

// Heights and places on the ship, in hull lengths; x runs to the bow, y to starboard
const DECK = 0.1;
const HOUSE_TOP = DECK + 0.045;
const FUNNEL_X = -0.02;
const FUNNEL_RADIUS = 0.03;
const FUNNEL_TOP = 0.3;
const FORE_MAST = 0.2;
const MAIN_MAST = -0.25;
const MAST_TOP = 0.5;
const SAIL_FOOT = DECK + 0.03;

const INK = '#1B2433';
const PAPER = '#FBF8F1';
const SPAR = '#3A2E22';
const CANVAS = 'rgba(247, 241, 226, 0.95)';
const SHADOW = 'rgba(8, 26, 44, ';

// Rough monsoon of the archipelago per month: where the wind comes from, and how steady it is
const MONSOON = {
    1 : [290, 1],
    2 : [290, 1],
    3 : [285, 0.9],
    4 : [200, 0.45],
    5 : [125, 0.75],
    6 : [115, 1],
    7 : [115, 1],
    8 : [115, 1],
    9 : [120, 0.9],
    10 : [150, 0.5],
    11 : [260, 0.55],
    12 : [290, 0.9]
};

function bearingBetween(lonA, latA, lonB, latB) {
    return Math.atan2((lonB - lonA) * Math.cos((latA + latB) / 2 * DEG), latB - latA) / DEG;
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}

function drawBox(ctx, at, box, colors, lineWidth) {
    rectPath(ctx, at, box.x0, box.x1, box.half, box.z0);
    ctx.fillStyle = colors[0];
    ctx.fill();
    rectPath(ctx, at, box.x0, box.x1, box.half, box.z1);
    ctx.fillStyle = colors[1];
    ctx.fill();
    ctx.lineWidth = lineWidth;
    ctx.strokeStyle = INK;
    ctx.stroke();
}

// A black cylinder with the ochre band of the drawing in the dive
function drawFunnel(ctx, at) {
    const width = FUNNEL_RADIUS * 2 * LENGTH;
    const height = FUNNEL_TOP - HOUSE_TOP;

    ctx.lineCap = 'round';
    ctx.lineWidth = width + 1.2;
    ctx.strokeStyle = INK;
    line(ctx, at, [FUNNEL_X, 0, HOUSE_TOP], [FUNNEL_X, 0, FUNNEL_TOP]);
    ctx.lineWidth = width;
    ctx.strokeStyle = '#2B2B2E';
    line(ctx, at, [FUNNEL_X, 0, HOUSE_TOP], [FUNNEL_X, 0, FUNNEL_TOP]);
    ctx.lineCap = 'butt';
    ctx.strokeStyle = '#B8862E';
    line(ctx, at, [FUNNEL_X, 0, HOUSE_TOP + height * 0.72], [FUNNEL_X, 0, HOUSE_TOP + height * 0.84]);

    const [x, y] = at(FUNNEL_X, 0, FUNNEL_TOP);

    ctx.fillStyle = '#0E0E10';
    ctx.beginPath();
    ctx.arc(x, y, width * 0.36, 0, Math.PI * 2);
    ctx.fill();
}

function drawLifeboat(ctx, at, x, y, lineWidth) {
    const z = DECK + 0.025;
    const half = 0.05;
    const width = 0.018;

    ctx.beginPath();
    ctx.moveTo(...at(x + half, y, z));
    ctx.quadraticCurveTo(...at(x, y + width * 2, z), ...at(x - half, y, z));
    ctx.quadraticCurveTo(...at(x, y - width * 2, z), ...at(x + half, y, z));
    ctx.fillStyle = PAPER;
    ctx.fill();
    ctx.lineWidth = lineWidth * 0.6;
    ctx.strokeStyle = INK;
    ctx.stroke();
}

// Half the beam at u, which runs from 1 at the sharp bow to -1 at the round stern
function halfBeam(u) {
    return u > 0 ? 0.085 * Math.pow(1 - u * u, 0.55) : 0.085 * Math.pow(1 - Math.pow(-u, 3.2), 0.38);
}

function hullPath(ctx, at, z, inset = 0, steps = 16) {
    const reach = 0.5 - inset * 1.6;

    ctx.beginPath();

    for (let i = 0; i <= steps; i++) {
        const u = 1 - 2 * i / steps;
        const [x, y] = at(u * reach, Math.max(0, halfBeam(u) - inset), z);

        if (i) {
            ctx.lineTo(x, y);
        } else {
            ctx.moveTo(x, y);
        }
    }

    for (let i = steps; i >= 0; i--) {
        const u = 1 - 2 * i / steps;

        ctx.lineTo(...at(u * reach, -Math.max(0, halfBeam(u) - inset), z));
    }

    ctx.closePath();
}

function lerp(a, b, t) {
    return a + (b - a) * t;
}

function line(ctx, at, from, to) {
    ctx.beginPath();
    ctx.moveTo(...at(...from));
    ctx.lineTo(...at(...to));
    ctx.stroke();
}

function midpoint(a, b, offset) {
    return [(a[0] + b[0]) / 2 + offset[0], (a[1] + b[1]) / 2 + offset[1], (a[2] + b[2]) / 2];
}

// Moves a position by screen pixels to the east and north at a zoom level
function offsetBy(lon, lat, east, north, zoom) {
    const pxPerDegree = WORLD_PX * 2 ** zoom / 360;

    return [lon + east / pxPerDegree, lat + north * Math.cos(lat * DEG) / pxPerDegree];
}

function pxPerKm(lat, zoom) {
    return WORLD_PX * 2 ** zoom / (EARTH_KM * Math.cos(lat * DEG));
}

function rectPath(ctx, at, x0, x1, half, z) {
    ctx.beginPath();
    ctx.moveTo(...at(x0, -half, z));
    ctx.lineTo(...at(x1, -half, z));
    ctx.lineTo(...at(x1, half, z));
    ctx.lineTo(...at(x0, half, z));
    ctx.closePath();
}

// Critically damped spring towards a moving target, as SmoothDamp in Unity: the ship
// gathers way slowly and comes to rest slowly, with a lag of about `time` seconds
function smoothDamp(current, target, velocity, time, dt) {
    const omega = 2 / time;
    const x = omega * dt;
    const decay = 1 / (1 + x + 0.48 * x * x + 0.235 * x * x * x);
    const change = current - target;
    const temp = (velocity + omega * change) * dt;

    return [target + (change + temp) * decay, (velocity - omega * temp) * decay];
}

function smoothstep(edge0, edge1, value) {
    const t = clamp((value - edge0) / (edge1 - edge0), 0, 1);

    return t * t * (3 - 2 * t);
}

// A vector to the east and north on the map, as screen x and y for a map bearing and pitch
function toScreen(east, north, view) {
    const cos = Math.cos(view.bearing * DEG);
    const sin = Math.sin(view.bearing * DEG);

    return [east * cos - north * sin, -(north * cos + east * sin) * Math.cos(view.pitch * DEG)];
}

// A sail as path commands in ship coordinates, so that the ship and its shadow share it
function tracePath(ctx, at, commands) {
    ctx.beginPath();

    for (const [command, ...points] of commands) {
        const screen = points.flatMap((point) => at(...point));

        if (command === 'M') {
            ctx.moveTo(...screen);
        } else if (command === 'L') {
            ctx.lineTo(...screen);
        } else {
            ctx.quadraticCurveTo(...screen);
        }
    }

    ctx.closePath();
}

// Angle difference in degrees, between -180 and 180
function wrap(degrees) {
    return ((degrees % 360) + 540) % 360 - 180;
}

// Where the wind comes from on a date (YYYY-MM-DD), and how hard it blows
export function monsoonAt(date) {
    const [from, steadiness] = MONSOON[Number(date?.slice(5, 7))] ?? MONSOON[3];

    return {
        from,
        strength : WIND_STRENGTH * steadiness
    };
}

export default class Ship {
    constructor(line, { waves = 0.6 } = {}) {
        this.line = line;
        this.routeLength = line[line.length - 1][0];
        this.waves = waves;
        this.direction = 1;
        this.reverseTime = 0;
        // Speed and acceleration scaled to 0…1 and -1…1, as the effects use them
        this.speed = 0;
        this.acceleration = 0;
        this.yawRate = 0;
        this.yawSway = 0;
        this.roll = 0;
        this.rollRate = 0;
        this.pitch = 0;
        this.pitchRate = 0;
        this.heave = 0;
        this.windFrom = 285;
        this.windStrength = WIND_STRENGTH;
        this.windAngle = 0;
        this.sailSet = 0;
        this.sailFill = 0;
        this.sailForce = 0;
        this.luff = 0;
        this.boom = 0;
        this.boomRate = 0;
        this.boomSide = 1;
        this.throttle = 0;
        this.time = 0;
        this.odometer = 0;
        this.lastWake = 0;
        this.nextPuff = 0;
        this.nextRipple = 0;
        this.puffs = [];
        this.wake = [];
        this.ripples = [];
        this.place(0);
    }

    // View: project(lon, lat) to [x, y] in CSS pixels, and the bearing, pitch and zoom of the map
    draw(ctx, view) {
        const [cx, cy] = view.project(this.position.lon, this.position.lat);
        const at = this.frame(cx, cy, view, false);
        const shade = this.frame(cx, cy, view, true);

        this.drawRipples(ctx, view);
        this.drawWake(ctx, view);
        this.drawShip(ctx, at, shade);
        this.drawPuffs(ctx, view);
    }

    // The Dutch navy pennant on the mainmast, streaming with the wind the ship feels
    drawPennant(ctx, at) {
        const to = (this.windAngle + 180) * DEG;
        const apparentX = Math.cos(to) * this.windStrength - this.speed * 1.2;
        const apparentY = Math.sin(to) * this.windStrength;
        const strength = Math.min(1, Math.hypot(apparentX, apparentY));
        const angle = Math.atan2(apparentY, apparentX);
        const steps = 9;
        const points = [];

        for (let i = 0; i <= steps; i++) {
            const u = i / steps;
            const wave = Math.sin(this.time * (6 + 6 * strength) - u * 7) * 0.02 * u;
            const along = u * 0.2 * (0.55 + 0.45 * strength);

            points.push(at(
                MAIN_MAST + Math.cos(angle) * along - Math.sin(angle) * wave,
                Math.sin(angle) * along + Math.cos(angle) * wave,
                MAST_TOP - u * 0.06 * (1 - strength)
            ));
        }

        ctx.lineCap = 'round';

        for (let i = 0; i < steps; i++) {
            ctx.strokeStyle = ['#AE1C28', '#FFFFFF', '#21468B'][Math.floor(i / steps * 3)];
            ctx.lineWidth = Math.max(1, LENGTH / 40 * (1 - i / steps * 0.6));
            ctx.beginPath();
            ctx.moveTo(...points[i]);
            ctx.lineTo(...points[i + 1]);
            ctx.stroke();
        }
    }

    drawPuffs(ctx, view) {
        const lift = Math.max(TILT, Math.sin(view.pitch * DEG));

        for (const puff of this.puffs) {
            const age = this.time - puff.born;
            const fraction = age / puff.life;
            const [bx, by] = view.project(puff.lon, puff.lat);
            const [dx, dy] = toScreen(puff.east * age, puff.north * age, view);
            const radius = puff.size + puff.grow * age;
            const x = bx + dx + Math.sin(age * 1.7 + puff.seed) * radius * 0.15;
            const y = by + dy - (puff.z + puff.rise * age) * lift;
            const value = Math.round(lerp(puff.shade, 236, fraction));
            const alpha = puff.alpha * Math.pow(1 - fraction, 1.6) * Math.min(1, age * 8);

            ctx.fillStyle = `rgba(${value}, ${value}, ${value + 4}, ${alpha * 0.5})`;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = `rgba(${value}, ${value}, ${value + 4}, ${alpha})`;
            ctx.beginPath();
            ctx.arc(x, y, radius * 0.62, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Rings on the water around a ship that lies still on the swell
    drawRipples(ctx, view) {
        const squash = Math.cos(view.pitch * DEG);

        ctx.lineWidth = 1;

        for (const ripple of this.ripples) {
            const age = (this.time - ripple.born) / 2.6;
            const [x, y] = view.project(ripple.lon, ripple.lat);
            const radius = (0.5 + age * 0.45) * LENGTH;

            ctx.save();
            ctx.translate(x, y);
            ctx.scale(1, squash);
            ctx.rotate((ripple.heading - 90 - view.bearing) * DEG);
            ctx.strokeStyle = `rgba(251, 248, 241, ${0.4 * (1 - age) * Math.min(1, age * 6)})`;
            ctx.beginPath();
            ctx.ellipse(0, 0, radius, radius * 0.42, 0, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();
        }
    }

    drawShip(ctx, at, shade) {
        const lineWidth = Math.max(0.8, LENGTH / 55);
        const rig = this.rig();

        // Shadows on the water
        ctx.fillStyle = `${SHADOW}0.22)`;
        hullPath(ctx, shade, DECK);
        ctx.fill();
        ctx.strokeStyle = `${SHADOW}0.16)`;
        ctx.lineCap = 'round';
        ctx.lineWidth = lineWidth * 1.2;

        for (const mast of [FORE_MAST, MAIN_MAST]) {
            line(ctx, shade, [mast, 0, DECK], [mast, 0, MAST_TOP]);
        }

        ctx.fillStyle = `${SHADOW}0.1)`;

        for (const sail of rig.sails) {
            tracePath(ctx, shade, sail);
            ctx.fill();
        }

        ctx.strokeStyle = `${SHADOW}0.2)`;
        ctx.lineWidth = FUNNEL_RADIUS * 2 * LENGTH;
        line(ctx, shade, [FUNNEL_X, 0, HOUSE_TOP], [FUNNEL_X, 0, FUNNEL_TOP]);

        // Hull: the topsides show where the deck leans away from the waterline
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = INK;
        hullPath(ctx, at, 0);
        ctx.fillStyle = '#CFC6B1';
        ctx.fill();
        ctx.stroke();
        hullPath(ctx, at, DECK);
        ctx.fillStyle = PAPER;
        ctx.fill();
        ctx.stroke();
        hullPath(ctx, at, DECK, 0.012);
        ctx.fillStyle = '#E0CDA3';
        ctx.fill();

        ctx.strokeStyle = SPAR;
        ctx.lineWidth = lineWidth * 1.1;
        line(ctx, at, [0.45, 0, DECK], [0.68, 0, DECK + 0.025]);

        // Hatches, boats, and the deckhouse with the bridge
        for (const [x0, x1, half] of [[0.3, 0.37, 0.025], [-0.44, -0.38, 0.022]]) {
            drawBox(ctx, at, {
                x0,
                x1,
                half,
                z0 : DECK,
                z1 : DECK + 0.012
            }, ['#8F7A55', '#B39D74'], lineWidth * 0.6);
        }

        for (const side of [-1, 1]) {
            drawLifeboat(ctx, at, -0.33, side * 0.068, lineWidth);
        }

        drawBox(ctx, at, {
            x0 : -0.16,
            x1 : 0.13,
            half : 0.05,
            z0 : DECK,
            z1 : HOUSE_TOP
        }, ['#C9C0AA', '#F6F1E4'], lineWidth * 0.8);
        drawBox(ctx, at, {
            x0 : 0.06,
            x1 : 0.13,
            half : 0.068,
            z0 : HOUSE_TOP,
            z1 : HOUSE_TOP + 0.03
        }, ['#C9C0AA', PAPER], lineWidth * 0.8);
        drawFunnel(ctx, at);

        // Booms and furled sails, then the sails, the masts and yards, and the pennant on top
        ctx.lineCap = 'round';
        ctx.strokeStyle = SPAR;
        ctx.lineWidth = lineWidth * 1.1;

        for (const spar of rig.spars) {
            line(ctx, at, spar[0], spar[1]);
        }

        ctx.strokeStyle = '#E6DCC4';
        ctx.lineWidth = lineWidth * 2.4;

        for (const bundle of rig.furled) {
            line(ctx, at, bundle[0], bundle[1]);
        }

        ctx.lineWidth = lineWidth * 0.7;

        for (const sail of rig.sails) {
            tracePath(ctx, at, sail);
            ctx.fillStyle = CANVAS;
            ctx.fill();
            ctx.strokeStyle = '#7D705A';
            ctx.stroke();
        }

        ctx.strokeStyle = SPAR;
        ctx.lineWidth = Math.max(1, LENGTH / 50);

        for (const mast of [FORE_MAST, MAIN_MAST]) {
            line(ctx, at, [mast, 0, DECK], [mast, 0, MAST_TOP]);
        }

        ctx.lineWidth = lineWidth;

        for (const yard of rig.yards) {
            line(ctx, at, yard[0], yard[1]);
        }

        this.drawPennant(ctx, at);
    }

    // Only the churned water straight behind the screw, laid down by distance
    drawWake(ctx, view) {
        const maxDistance = 6 * LENGTH;

        for (const point of this.wake) {
            const distance = this.odometer - point.odometer;
            const [x, y] = view.project(point.lon, point.lat);
            const fade = point.strength * (1 - distance / maxDistance) * (1 - (this.time - point.born) / 12);
            const alpha = 0.28 * fade * (0.3 + point.churn);

            ctx.fillStyle = `rgba(251, 248, 241, ${Math.max(0, alpha)})`;
            ctx.beginPath();
            ctx.arc(x, y, 0.025 * LENGTH + 0.05 * distance, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    emitPuff(zoom) {
        const heading = this.heading * DEG;
        const forward = FUNNEL_X * LENGTH;
        const [lon, lat] = offsetBy(this.position.lon, this.position.lat, Math.sin(heading) * forward, Math.cos(heading) * forward, zoom);
        const to = (this.windFrom + 180) * DEG;
        const drift = this.windStrength * 0.5 * LENGTH;
        const jitter = 0.05 * LENGTH;
        const throttle = this.throttle;

        this.puffs.push({
            lon,
            lat,
            born : this.time,
            life : 1.8 + 2.8 * throttle,
            size : (0.025 + 0.03 * throttle) * LENGTH,
            grow : (0.06 + 0.09 * throttle) * LENGTH,
            rise : (0.12 + 0.1 * throttle) * LENGTH,
            z : FUNNEL_TOP * LENGTH,
            east : Math.sin(to) * drift + (Math.random() - 0.5) * jitter,
            north : Math.cos(to) * drift + (Math.random() - 0.5) * jitter,
            // Dark coal smoke when the ship gathers way, light when it idles
            shade : lerp(205, 70, clamp(throttle * 0.6 + this.acceleration * 1.2, 0, 1)),
            alpha : 0.35 + 0.45 * throttle,
            seed : Math.random() * Math.PI * 2
        });
    }

    // Projects ship coordinates (x to the bow, y to starboard, z up, in hull lengths) to the
    // screen. Height leans with heel and pitch, plus the oblique view or the tilt of the map;
    // for the shadow it falls along the sun. A tilted map shortens the ship front to back.
    frame(cx, cy, view, isShadow) {
        const rotation = (this.heading + this.yawSway - view.bearing) * DEG;
        const squash = Math.cos(view.pitch * DEG);
        const fx = Math.sin(rotation);
        const fy = -Math.cos(rotation) * squash;
        const sx = Math.cos(rotation);
        const sy = Math.sin(rotation) * squash;
        const roll = this.roll * LEAN_EXAGGERATION * DEG;
        const leanForward = -Math.sin(this.pitch * LEAN_EXAGGERATION * DEG);
        const leanSide = Math.sin(roll);
        const up = isShadow ? [SUN[0], SUN[1] * squash] : [0, -Math.max(TILT, Math.sin(view.pitch * DEG))];
        const zx = up[0] + leanForward * fx + leanSide * sx;
        const zy = up[1] + leanForward * fy + leanSide * sy;
        const beam = Math.cos(roll);
        const scale = LENGTH * (1 + 0.018 * this.heave);

        return (x, y, z) => [
            cx + (x * fx + y * beam * sx + z * zx) * scale,
            cy + (x * fy + y * beam * sy + z * zy) * scale
        ];
    }

    gaffSail(rig, mast, height, length, hasBoom, delta, lee, belly) {
        const set = this.sailSet;
        const top = SAIL_FOOT + height * Math.max(set, 0.08);
        const angle = delta * (hasBoom ? 1 : 1.08);
        const reach = length * (hasBoom ? 1 : Math.max(0.15, set));
        const tack = [mast, 0, SAIL_FOOT];
        const throat = [mast, 0, top];
        const clew = [mast - Math.cos(angle) * reach, Math.sin(angle) * reach, SAIL_FOOT + (hasBoom ? 0 : 0.03)];
        const twist = angle * 1.15;
        const peak = [mast - Math.cos(twist) * reach * 0.8, Math.sin(twist) * reach * 0.8, top + 0.03 * set];
        const normal = [lee * Math.sin(angle) * belly, lee * Math.cos(angle) * belly];

        if (hasBoom) {
            rig.spars.push([tack, [mast - Math.cos(angle) * length, Math.sin(angle) * length, SAIL_FOOT]]);
        }

        if (set < 0.06) {
            rig.furled.push(hasBoom ? [tack, clew] : [tack, [mast, 0, SAIL_FOOT + height * 0.6]]);

            return;
        }

        rig.spars.push([throat, peak]);
        rig.sails.push([
            ['M', tack],
            ['L', throat],
            ['L', peak],
            ['Q', midpoint(peak, clew, [normal[0] * 0.6, normal[1] * 0.6]), clew],
            ['Q', midpoint(clew, tack, normal), tack]
        ]);
    }

    // Bearing of the route around a km, over a stretch either way in the direction of sailing
    headingAt(km, span) {
        const behind = pointAt(this.line, clamp(km - this.direction * span, 0, this.routeLength));
        const ahead = pointAt(this.line, clamp(km + this.direction * span, 0, this.routeLength));

        if (Math.hypot(ahead.lon - behind.lon, ahead.lat - behind.lat) < 0.004) {
            return this.heading ?? 0;
        }

        return bearingBetween(behind.lon, behind.lat, ahead.lon, ahead.lat);
    }

    jib(rig, delta, lee, belly) {
        const set = this.sailSet;
        const tip = [0.67, 0, DECK + 0.025];

        if (set < 0.06) {
            rig.furled.push([tip, [0.5, 0, DECK + 0.02]]);

            return;
        }

        const angle = delta * 0.75;
        const reach = 0.34 * set;
        const head = [FORE_MAST, 0, SAIL_FOOT + 0.34 * set];
        const clew = [0.67 - Math.cos(angle) * reach, Math.sin(angle) * reach, DECK + 0.04];
        const normal = [lee * Math.sin(angle) * belly, lee * Math.cos(angle) * belly];

        rig.sails.push([
            ['M', tip],
            ['L', head],
            ['Q', midpoint(head, clew, normal), clew],
            ['L', tip]
        ]);
    }

    // Puts the ship at a km at once, at rest
    place(km) {
        const point = pointAt(this.line, clamp(km, 0, this.routeLength));

        this.km = clamp(km, 0, this.routeLength);
        this.velocity = 0;
        this.position = {
            lon : point.lon,
            lat : point.lat
        };
        this.heading = this.headingAt(this.km, 2);
        this.targetHeading = this.heading;
        this.yawRate = 0;
        this.wake.length = 0;
    }

    // Masts, spars and sails in ship coordinates: a schooner rig with a loose-footed foresail
    // brailed to its mast, a mainsail on a boom, a jib, and bare yards on the foremast
    rig() {
        const rig = {
            spars : [],
            yards : [],
            furled : [],
            sails : []
        };
        const delta = this.boom * DEG;
        const lee = Math.sign(this.boom) || this.boomSide;
        const belly = 0.015 + 0.07 * this.sailFill + this.luff * 0.035 * Math.sin(this.time * 19);
        const brace = delta * 0.6;

        this.gaffSail(rig, FORE_MAST, 0.3, 0.32, false, delta, lee, belly);
        this.gaffSail(rig, MAIN_MAST, 0.32, 0.28, true, delta, lee, belly);
        this.jib(rig, delta, lee, belly);

        for (const [z, half] of [[0.46, 0.1], [0.33, 0.14]]) {
            rig.yards.push([
                [FORE_MAST - Math.sin(brace) * half, Math.cos(brace) * half, z],
                [FORE_MAST + Math.sin(brace) * half, -Math.cos(brace) * half, z]
            ]);
        }

        return rig;
    }

    // The route around a km averaged over a stretch either way, so the ship glides over the
    // small zigzags of the line instead of jerking along them
    smoothPointAt(km, span) {
        const samples = 9;
        let lon = 0;
        let lat = 0;

        for (let i = 0; i < samples; i++) {
            const point = pointAt(this.line, clamp(km + span * (2 * i / (samples - 1) - 1), 0, this.routeLength));

            lon += point.lon;
            lat += point.lat;
        }

        return {
            lon : lon / samples,
            lat : lat / samples
        };
    }

    // One step of dt seconds towards a km on the route, at a zoom level, in a wind
    update(dt, targetKm, zoom, wind) {
        const kmPerPx = 1 / pxPerKm(this.position.lat, zoom);
        const oldKm = this.km;

        this.time += dt;

        if (Math.abs(targetKm - this.km) > SNAP_KM) {
            this.place(targetKm);
        }

        const before = this.velocity;

        [this.km, this.velocity] = smoothDamp(this.km, targetKm, this.velocity, INERTIA, dt);

        // A fast scrub drags the ship along on a leash of a few hull lengths on screen, instead of
        // leaving it far behind; and it never runs so fast that it would overshoot and turn back
        const maxLag = 2.5 * LENGTH * kmPerPx;
        const gap = targetKm - this.km;

        if (Math.abs(gap) > maxLag) {
            this.km = targetKm - Math.sign(gap) * maxLag;
        }

        const left = targetKm - this.km;
        const maxVelocity = 2 / INERTIA * Math.abs(left) + PLAY_KM_PER_SECOND * 0.05;

        if (Math.sign(this.velocity) === Math.sign(left) || Math.abs(left) < 0.01) {
            this.velocity = clamp(this.velocity, -maxVelocity, maxVelocity);
        }

        if (this.km <= 0 || this.km >= this.routeLength) {
            this.km = clamp(this.km, 0, this.routeLength);
            this.velocity = 0;
        }

        this.position = this.smoothPointAt(this.km, Math.max(0.5, 0.4 * LENGTH * kmPerPx));

        const speedKm = Math.abs(this.velocity);
        const along = (this.velocity - before) / dt * (Math.sign(this.velocity) || this.direction);

        this.speed = 1 - Math.exp(-speedKm / (2 * PLAY_KM_PER_SECOND));
        this.acceleration += (Math.tanh(along / (PLAY_KM_PER_SECOND * 1.5)) - this.acceleration) * Math.min(1, dt * 5);

        this.updateHeading(dt, speedKm, kmPerPx, Math.min(Math.abs(this.km - oldKm) / kmPerPx, 3 * LENGTH));
        this.updateWind(dt, wind);
        this.updateSails(dt);
        this.updateMotion(dt);
        this.updateSteam(dt, zoom);
        this.updateWater(dt, zoom, oldKm, kmPerPx);
    }

    // The bow follows the route by distance travelled rather than by time: the ship turns on a
    // circle of about half a hull length on screen, so it takes the same curve at 1× and at 16×
    // and never slides sideways. Turning round on the spot goes at a limited rate in time.
    updateHeading(dt, speedKm, kmPerPx, travelPx) {
        // Only a steady run the other way turns the ship round, not a trembling finger
        const isReversing = Math.sign(this.velocity) === -this.direction && speedKm > PLAY_KM_PER_SECOND * 0.25;

        this.reverseTime = isReversing ? this.reverseTime + dt : 0;

        if (this.reverseTime > 0.35) {
            this.direction = -this.direction;
            this.reverseTime = 0;
        }

        if (speedKm > PLAY_KM_PER_SECOND * 0.02) {
            this.targetHeading = this.headingAt(this.km, Math.max(1, 0.8 * LENGTH * kmPerPx));
        }

        const follow = 1 - Math.exp(-travelPx / (0.45 * LENGTH * (0.5 + 0.5 * INERTIA)));
        const difference = wrap(this.targetHeading - this.heading);
        const onTheSpot = (20 + 40 * this.speed) * dt;
        let step = difference * follow;

        step += clamp(difference - step, -onTheSpot, onTheSpot) * 0.5;
        this.heading = (this.heading + step + 360) % 360;
        this.yawRate += (step / dt - this.yawRate) * Math.min(1, dt * 8);
        // At rest the ship swings a little on the swell
        this.yawSway = this.waves * (1.5 * Math.sin(this.time * 0.5) + 0.7 * Math.sin(this.time * 0.83 + 1)) * (1 - this.speed);
    }

    // Heel, pitch and heave, each a damped spring towards what the turn, wind, swell and engine ask
    updateMotion(dt) {
        const t = this.time;
        // A ship heels out of a turn, and away from the wind in its sails
        const turnHeel = -9 * Math.tanh(this.yawRate / 90) * (0.35 + this.speed) / 1.35;
        const side = Math.sin(this.windAngle * DEG);
        const windHeel = -(WIND_HEEL * this.sailForce * Math.sign(side) * Math.pow(Math.abs(side), 0.6) + 1.2 * this.windStrength * side);
        const waveRoll = this.waves * (2.2 * Math.sin(t * 1.05) + 1.2 * Math.sin(t * 1.7 + 2.1));
        const roll = 2 * Math.PI * ROLL_FREQUENCY;

        this.rollRate += (roll ** 2 * (turnHeel + windHeel + waveRoll - this.roll) - 2 * ROLL_DAMPING * roll * this.rollRate) * dt;
        this.roll += this.rollRate * dt;

        // The bow lifts when the ship gathers way and dips when it brakes
        const wavePitch = this.waves * (1.1 * Math.sin(t * 1.4 + 0.7) + 0.5 * Math.sin(t * 2.3));
        const pitch = 2 * Math.PI * 0.8;

        this.pitchRate += (pitch ** 2 * (4.5 * this.acceleration + wavePitch - this.pitch) - 2 * 0.3 * pitch * this.pitchRate) * dt;
        this.pitch += this.pitchRate * dt;
        this.heave = this.waves * (Math.sin(t * 0.95) + 0.5 * Math.sin(t * 1.6 + 1.3));
    }

    // A steamer with sails only sets them with way on and the wind abeam or behind; the booms trim
    // to the wind and gybe across when it comes round the stern
    updateSails(dt) {
        const off = Math.abs(this.windAngle);
        const want = Number(this.speed > 0.05 && off > 70 && this.windStrength > 0.2);

        this.sailSet = clamp(this.sailSet + clamp(want - this.sailSet, -dt * 0.6, dt * 0.4), 0, 1);

        if (off < 165) {
            this.boomSide = this.windAngle > 0 ? -1 : 1;
        }

        const trim = clamp((off - 20) * 0.62, 3, 80);
        const target = this.boomSide * trim * Math.min(1, this.sailSet * 2.5);
        const frequency = 3.2;

        this.boomRate += (frequency ** 2 * (target - this.boom) - 2 * 0.42 * frequency * this.boomRate) * dt;
        this.boom = clamp(this.boom + this.boomRate * dt, -88, 88);
        this.sailFill = this.sailSet * this.windStrength * smoothstep(25, 70, off);
        this.luff = this.sailSet * (1 - smoothstep(18, 45, off)) * Math.max(0.3, this.windStrength);
        this.sailForce = this.sailFill * (off > 90 ? 1 - 0.35 * (off - 90) / 90 : 1);
    }

    // Puffs come faster and darker when the stoker works hard, and drift off with the wind
    updateSteam(dt, zoom) {
        const isWorking = this.speed > 0.03 || this.acceleration > 0.05;
        const target = (isWorking ? clamp(0.15 + 0.75 * this.speed + 0.9 * Math.max(0, this.acceleration), 0, 1) : 0.05) * (1 - 0.45 * this.sailForce);

        this.throttle += (target - this.throttle) * Math.min(1, dt * 3);
        this.nextPuff -= dt;

        if (this.nextPuff <= 0) {
            this.nextPuff = lerp(0.95, 0.2, this.throttle) * (0.85 + 0.3 * Math.random());
            this.emitPuff(zoom);
        }

        this.puffs = this.puffs.filter((puff) => this.time - puff.born < puff.life).slice(-90);
    }

    // The wake is laid down by distance, so it looks the same at every speed; at rest there are ripples
    updateWater(dt, zoom, oldKm, kmPerPx) {
        const travelled = Math.abs(this.km - oldKm) / kmPerPx;

        if (travelled < LENGTH * 3) {
            this.odometer += travelled;
        }

        if (this.odometer - this.lastWake >= 3 && this.speed > 0.02) {
            const heading = this.heading * DEG;
            const back = -0.48 * LENGTH;
            const [lon, lat] = offsetBy(this.position.lon, this.position.lat, Math.sin(heading) * back, Math.cos(heading) * back, zoom);

            this.wake.push({
                lon,
                lat,
                odometer : this.odometer,
                born : this.time,
                strength : this.speed,
                churn : this.throttle
            });
            this.lastWake = this.odometer;
        }

        this.wake = this.wake.filter((point) => this.odometer - point.odometer < 6 * LENGTH && this.time - point.born < 12);

        if (this.speed < 0.05 && this.waves > 0.05) {
            this.nextRipple -= dt;

            if (this.nextRipple <= 0) {
                this.nextRipple = (1.3 + Math.random() * 1.2) / Math.min(1.5, this.waves + 0.3);
                this.ripples.push({
                    lon : this.position.lon,
                    lat : this.position.lat,
                    heading : this.heading,
                    born : this.time
                });
            }
        }

        this.ripples = this.ripples.filter((ripple) => this.time - ripple.born < 2.6);
    }

    updateWind(dt, wind) {
        const rate = Math.min(1, dt * 0.8);

        this.windFrom = (this.windFrom + wrap(wind.from - this.windFrom) * rate + 360) % 360;
        this.windStrength += (wind.strength - this.windStrength) * rate;
        // 0 is wind from ahead, positive from starboard
        this.windAngle = wrap(this.windFrom - this.heading);
    }
}
