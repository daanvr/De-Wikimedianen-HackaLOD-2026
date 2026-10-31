<script setup>
    // The dive from the dive prototype: the waterline rises over the tilted map, the Siboga
    // lies half under water, and scrolling goes down the water column to the sea floor.
    import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
    import { formatDate } from '@/services/format.js';
    import ElIcon from '@/components/el-icon.vue';
    import ElExplorerBadge from './el-explorer-badge.vue';
    import ElExplorerIcon from './el-explorer-icon.vue';
    import { seeded } from './data.js';
    import { GEAR, GEAR_DRAWINGS, PHOTO_CREDIT, gearsOf } from './gear.js';
    import { BOTTOM_GROUPS, groupName } from './groups.js';
    import paperTexture from './media/paper.png';
    import washTexture from './media/wash.png';

    // Waterline after the dive, and the waterline below which scrolling up surfaces, as share of the height
    const WATERLINE = 0.42;
    const SURFACE_AT = 0.86;
    // y of the waterline in the ship drawing's viewBox
    const SHIP_WATERLINE = 140;
    const ENTER_MS = 1900;

    // Water colour by depth in metres: turquoise at the surface, ink blue in the deep, never black
    const SEA_COLOURS = [
        [0, '#A9D6CF'],
        [15, '#86C0C2'],
        [50, '#62A3B4'],
        [150, '#42839F'],
        [400, '#2D6286'],
        [1000, '#204769'],
        [2500, '#17314F'],
        [5000, '#0F2139'],
        [7000, '#0B182B']
    ];

    const ZONES = [
        {
            depth : 0,
            label : 'Zonlichtzone',
            sub : 'licht genoeg voor wieren en koraal'
        },
        {
            depth : 200,
            label : 'Schemerzone',
            sub : 'het laatste zonlicht verdwijnt'
        },
        {
            depth : 1000,
            label : 'Middernachtzone',
            sub : 'volledig donker en koud'
        },
        {
            depth : 4000,
            label : 'Diepzeevlakte',
            sub : 'abyssale zone'
        }
    ];

    const RULER_DEPTHS = [2, 5, 10, 20, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000];
    const BOTTOM_ROW = 6;
    const PORTHOLES = Array.from({ length : 11 }, (_, i) => 92 + i * 22);
    const WINDOWS = Array.from({ length : 6 }, (_, i) => 138 + i * 20);

    const emit = defineEmits(['surface', 'select-specimen']);

    const props = defineProps({
        station : {
            type : Object,
            required : true
        },
        wikidataUrl : {
            type : String,
            default : 'https://www.wikidata.org/wiki/'
        }
    });

    const root = ref(null);
    const scroller = ref(null);
    const air = ref(null);
    const width = ref(390);
    const height = ref(700);
    const reading = ref(0);
    const openGear = ref(null);
    const seen = ref(new Set());

    let isArmed = false;
    let animation = null;
    let observer = null;
    let resizeObserver = null;

    const textures = {
        '--paper-texture' : `url(${paperTexture})`,
        '--wash-texture' : `url(${washTexture})`
    };

    const gears = computed(() => gearsOf(props.station.werkzaamheden));
    const isGearDepth = computed(() => props.station.diepte_soort === 'gear_depth');

    // The sounding, unless the line never reached the bottom; then the deeper of line and today's depth
    const depth = computed(() => {
        const sounding = props.station.diepte_m;

        if (sounding && !isGearDepth.value) {
            return sounding;
        }

        return Math.max(sounding ?? 0, props.station.diepte_vandaag_m ?? 0, 20);
    });

    // Depth scale: y grows with the square root of depth, so a 9 m reef and a 5 km trench both fit
    const k = computed(() => Math.max(70, height.value * 0.62 / Math.sqrt(depth.value)));
    const bedY = computed(() => yAt(depth.value));

    const seaBackground = computed(() => {
        const stops = [];

        for (const [z, colour] of SEA_COLOURS) {
            const y = yAt(z);

            stops.push(`${colour} ${Math.round(y)}px`);

            if (y > bedY.value) {
                break;
            }
        }

        return `linear-gradient(to bottom, ${stops.join(', ')})`;
    });

    const wavesPath = computed(() => {
        const period = 36;
        let d = 'M0 12';

        for (let x = 0; x < width.value * 2; x += period) {
            d += ` q${period / 4} -7 ${period / 2} 0 t${period / 2} 0`;
        }

        return d;
    });

    const ruler = computed(() => {
        const ticks = [];
        let lastY = -Infinity;

        for (const z of RULER_DEPTHS) {
            const y = yAt(z);

            if (z >= depth.value * 0.97 || y - lastY < 60 || y < 70) {
                continue;
            }

            ticks.push({
                z,
                top : y,
                label : `${z.toLocaleString('nl-NL')} m`
            });
            lastY = y;
        }

        return ticks;
    });

    const zones = computed(() => ZONES
        .filter((zone) => zone.depth < depth.value * 0.8)
        .map((zone) => ({
            ...zone,
            top : Math.max(yAt(zone.depth) + 24, 96)
        })));

    const ship = computed(() => {
        const shipWidth = Math.min(width.value * 0.86, 400);
        const scale = shipWidth / 400;
        const left = width.value * 0.1;

        return {
            width : shipWidth,
            scale,
            left,
            top : -SHIP_WATERLINE * scale,
            derrick : [left + 14 * scale, (56 - SHIP_WATERLINE) * scale],
            stern : [left + 370 * scale, (110 - SHIP_WATERLINE) * scale]
        };
    });

    // The gear of this station, where it hangs, and the cables to the ship
    const rigging = computed(() => {
        const w = width.value;
        const items = [];
        const cables = [];
        const station = props.station;

        gears.value.filter((key) => GEAR[key].place === 'bottom').forEach((key, i) => {
            const drawing = GEAR_DRAWINGS[key];
            const gearWidth = Math.min(w * (i ? 0.42 : 0.6), i ? 170 : 240);
            const gearHeight = gearWidth * drawing.height / drawing.width;
            const left = i ? w * 0.04 : w * 0.36;
            const lift = station.niet_op_bodem ? bedY.value * 0.15 : 0;
            const top = bedY.value - gearHeight * 0.92 + (key === 'dreg' ? gearHeight * 0.2 : 0) - lift;
            const attach = [left + drawing.attach[0] * gearWidth / drawing.width, top + drawing.attach[1] * gearWidth / drawing.width];

            items.push({
                key,
                left,
                top,
                width : gearWidth,
                drawing
            });
            cables.push({
                d : cablePath(ship.value.derrick, attach),
                weight : 1.6
            });
        });

        gears.value.filter((key) => GEAR[key].place === 'middle').forEach((key, i) => {
            const range = station.net_bereik_m;
            const netDepth = range ? Math.min(range[1], depth.value) : Math.min(depth.value * 0.45, 250);
            const gearWidth = 54;
            const x = w * (0.66 + i * 0.16);
            const top = Math.max(yAt(netDepth), 90);

            items.push({
                key,
                left : x - gearWidth / 2,
                top,
                width : gearWidth,
                drawing : GEAR_DRAWINGS[key]
            });
            cables.push({
                d : `M${x} ${-20 * ship.value.scale} V${top}`,
                weight : 1.1
            });
        });

        gears.value.filter((key) => GEAR[key].place === 'surface').forEach((key, i) => {
            const drawing = GEAR_DRAWINGS[key];
            const gearWidth = 110;
            const left = w - gearWidth - 10;
            const top = Math.max(yAt(4 + i * 6), 60) + i * 46;
            const attach = [left + drawing.attach[0] * gearWidth / drawing.width, top + drawing.attach[1] * gearWidth / drawing.width];

            items.push({
                key,
                left,
                top,
                width : gearWidth,
                drawing
            });
            cables.push({
                d : cablePath(ship.value.stern, attach),
                weight : 0.9
            });
        });

        return {
            items,
            cables,
            hand : gears.value.includes('rif') ? {
                left : w * 0.52,
                top : Math.max(yAt(1), 56)
            } : null
        };
    });

    const lead = computed(() => {
        const x = width.value * 0.9;

        return {
            x,
            line : `M${x} ${-10 * ship.value.scale} V${bedY.value - 14}`,
            weight : `M${x - 4} ${bedY.value - 16} h8 l2 14 h-12 Z`
        };
    });

    const soundingLabel = computed(() => {
        const station = props.station;

        if (station.diepte_m === null) {
            return 'geen loding';
        }

        if (isGearDepth.value) {
            return `lijn op ${Math.round(station.diepte_m)} m, geen bodem`;
        }

        const printed = /^\d+([.,]\d+)?$/.test(station.diepte_gedrukt ?? '') ? station.diepte_gedrukt : Math.round(station.diepte_m);

        return `gelood ${printed} m`;
    });

    // Where each specimen of this station is drawn. Only bottom life caught with bottom gear lies
    // on the bottom; a net with a known range holds its catch in that range; the rest is placed at random.
    const placed = computed(() => {
        const station = props.station;
        const w = width.value;
        const onBottomGear = station.tuig === 'bodem' && !station.niet_op_bodem;
        const range = station.tuig === 'netten' ? station.net_bereik_m : null;
        const bottom = station.specimens.filter((specimen) => onBottomGear && BOTTOM_GROUPS.has(specimen.group));
        const floating = station.specimens.filter((specimen) => !bottom.includes(specimen));
        const result = [];

        bottom.slice(0, BOTTOM_ROW * 2).forEach((specimen, i) => {
            const row = Math.floor(i / BOTTOM_ROW);
            const inRow = Math.min(BOTTOM_ROW, bottom.length - row * BOTTOM_ROW);
            const column = i % BOTTOM_ROW;
            const size = specimen.image ? 64 : 46;

            result.push({
                specimen,
                place : 'bottom',
                size,
                left : 12 + (column + 0.5) / inRow * (w - 24) - size / 2 + (row % 2) * 14,
                top : bedY.value + 18 - row * 34 - seeded(specimen.id % 9973) * 6,
                motion : /wieren|algen/.test(specimen.group) ? 'sway' : 'none'
            });
        });

        const top = Math.max(yAt(2), 120);
        const floor = bedY.value - Math.min(150, (bedY.value - top) * 0.3);
        let lastY = -Infinity;

        floating
            .map((specimen) => {
                const r = seeded(specimen.id % 100003);
                const z = range
                    ? range[0] + r * (Math.min(range[1], depth.value) - range[0])
                    : (0.12 + r * 0.76) * depth.value;

                return {
                    specimen,
                    y : Math.min(floor, Math.max(top, yAt(z)))
                };
            })
            .sort((a, b) => a.y - b.y)
            .forEach(({ specimen, y }, i) => {
                const placedY = Math.max(y, lastY + 70);
                const size = specimen.image ? 72 : 48;

                if (placedY > floor) {
                    return;
                }

                lastY = placedY;
                result.push({
                    specimen,
                    place : range ? 'net' : 'random',
                    size,
                    left : (i % 2 ? w * 0.5 : w * 0.08) + seeded(specimen.id % 99991) * w * 0.08,
                    top : placedY - size / 2,
                    motion : 'drift'
                });
            });

        return result;
    });

    const places = computed(() => new Set(placed.value.map((item) => item.place)));

    const bedColours = computed(() => {
        const text = (props.station.bodem ?? '').toLowerCase();

        if (/coral/.test(text)) {
            return ['#E7CDB4', '#C99F7F'];
        }

        if (/sand/.test(text)) {
            return ['#DCC79C', '#B89B66'];
        }

        if (/stone|rock|gravel/.test(text)) {
            return ['#9B9184', '#6E665C'];
        }

        if (/globigerin|ooze|radiolar/.test(text)) {
            return ['#D8D0B8', '#A99F84'];
        }

        if (/mud|clay/.test(text)) {
            return ['#8F8A73', '#5F5B4A'];
        }

        return ['#A89A7C', '#776B52'];
    });

    const gearWords = computed(() => {
        const words = gears.value.map((key) => GEAR[key].name.toLowerCase());

        return words.length ? words.join(' en ') : 'het lood';
    });

    const dates = computed(() => {
        const { datum, tot } = props.station;

        if (!datum) {
            return '';
        }

        return tot && tot !== datum ? `${formatDate(datum)} – ${formatDate(tot)}` : formatDate(datum);
    });

    const log = computed(() => [
        ['Plaats', props.station.opmerkingen],
        ['Diepte', props.station.diepte_gedrukt],
        ['Bodem', props.station.bodem],
        ['Werkzaamheden', props.station.werkzaamheden],
        ['Noten', props.station.noten]
    ].filter(([, value]) => value));

    function animateScroll(to, duration, done) {
        const from = scroller.value.scrollTop;
        const startedAt = performance.now();

        cancelAnimationFrame(animation);

        function step(now) {
            const t = Math.min(1, (now - startedAt) / duration);
            const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

            scroller.value.scrollTop = from + (to - from) * eased;

            if (t < 1) {
                animation = requestAnimationFrame(step);
            } else {
                done?.();
            }
        }

        animation = requestAnimationFrame(step);
    }

    function cablePath(from, to) {
        const dy = to[1] - from[1];
        const dx = to[0] - from[0];

        return `M${from[0]} ${from[1]} C${from[0]} ${from[1] + dy * 0.55} ${to[0] - dx * 0.25} ${to[1] - dy * 0.12} ${to[0]} ${to[1]}`;
    }

    function measure() {
        width.value = root.value.clientWidth;
        height.value = root.value.clientHeight;
    }

    function observeSpecimens() {
        observer?.disconnect();
        observer = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    seen.value = new Set([...seen.value, entry.target.dataset.id]);
                    observer.unobserve(entry.target);
                }
            }
        }, {
            root : scroller.value,
            threshold : 0.25
        });

        root.value.querySelectorAll('.specimen').forEach((element) => observer.observe(element));
    }

    function onScroll() {
        // A last scroll event can arrive while the dive is being taken down
        if (!air.value || !scroller.value) {
            return;
        }

        const airHeight = air.value.offsetHeight;
        const y = scroller.value.scrollTop + height.value * 0.5 - airHeight;

        reading.value = Math.max(0, Math.min(depth.value, depthAt(y)));

        if (isArmed && airHeight - scroller.value.scrollTop > height.value * SURFACE_AT) {
            isArmed = false;
            emit('surface');
        }
    }

    function surface() {
        isArmed = false;
        animateScroll(0, Math.min(2600, 900 + scroller.value.scrollTop / 4), () => emit('surface'));
    }

    function depthAt(y) {
        return Math.pow(Math.max(0, y) / k.value, 2);
    }

    function yAt(z) {
        return k.value * Math.sqrt(Math.max(0, z));
    }

    onMounted(async () => {
        measure();
        resizeObserver = new ResizeObserver(measure);
        resizeObserver.observe(root.value);
        await nextTick();
        scroller.value.scrollTop = 0;
        observeSpecimens();
        animateScroll(air.value.offsetHeight - height.value * WATERLINE, ENTER_MS, () => {
            isArmed = true;
        });
    });

    onBeforeUnmount(() => {
        cancelAnimationFrame(animation);
        observer?.disconnect();
        resizeObserver?.disconnect();
    });
</script>

<template>
    <section
        ref="root"
        class="el-explorer-dive"
        v-bind:style="textures"
        v-bind:aria-label="`Onder water bij station ${station.nummer}`">
        <svg
            class="defs"
            width="0"
            height="0"
            aria-hidden="true">
            <defs>
                <pattern
                    id="explorer-mesh"
                    width="7"
                    height="7"
                    patternUnits="userSpaceOnUse"
                    patternTransform="rotate(45)">
                    <path
                        d="M0 0 H7 M0 0 V7"
                        stroke="#3a3328"
                        stroke-width="0.6"
                        opacity="0.55" />
                </pattern>
                <filter
                    id="explorer-ink"
                    x="-5%"
                    y="-5%"
                    width="110%"
                    height="110%">
                    <feTurbulence
                        type="fractalNoise"
                        baseFrequency="0.04"
                        numOctaves="2"
                        seed="7" />
                    <feDisplacementMap
                        in="SourceGraphic"
                        scale="2.2" />
                </filter>
            </defs>
        </svg>

        <div
            ref="scroller"
            class="scroll"
            v-on:scroll.passive="onScroll()">
            <div
                ref="air"
                class="air"></div>

            <div
                class="sea"
                v-bind:style="{ paddingTop : `${bedY}px`, background : seaBackground }">
                <div
                    class="rays"
                    v-bind:style="{ height : `${Math.min(520, bedY)}px` }"></div>

                <div
                    v-if="bedY > yAt(250)"
                    class="snow"
                    v-bind:style="{ top : `${yAt(200)}px`, height : `${bedY - yAt(200)}px` }"></div>

                <svg
                    class="waves"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                    v-bind:viewBox="`0 0 ${width * 2} 22`"
                    v-bind:style="{ width : `${width * 2}px` }">
                    <path
                        fill="#A9D6CF"
                        v-bind:d="`${wavesPath} V22 H0 Z`" />
                    <path
                        fill="none"
                        stroke="#FBF6EA"
                        stroke-width="1.6"
                        opacity="0.8"
                        v-bind:d="wavesPath" />
                </svg>

                <div
                    class="ruler"
                    aria-hidden="true">
                    <span
                        v-for="tick in ruler"
                        v-bind:key="tick.z"
                        class="ruler__tick"
                        v-bind:style="{ top : `${tick.top}px` }">{{ tick.label }}</span>
                </div>

                <p
                    v-for="zone in zones"
                    v-bind:key="zone.label"
                    class="zone"
                    v-bind:style="{ top : `${zone.top}px` }">
                    {{ zone.label }}
                    <small>{{ zone.sub }}</small>
                </p>

                <div
                    class="ship"
                    aria-hidden="true"
                    v-bind:style="{ left : `${ship.left}px`, top : `${ship.top}px`, width : `${ship.width}px` }">
                    <svg viewBox="0 0 400 200">
                        <defs>
                            <clipPath id="explorer-ship-below">
                                <rect
                                    x="0"
                                    y="140"
                                    width="400"
                                    height="80" />
                            </clipPath>
                            <linearGradient
                                id="explorer-hull"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1">
                                <stop
                                    offset="0"
                                    stop-color="#FBF6EA" />
                                <stop
                                    offset="1"
                                    stop-color="#E4DCC8" />
                            </linearGradient>
                        </defs>
                        <g class="ship__body">
                            <g
                                fill="#9A9A9A"
                                opacity="0.28">
                                <ellipse
                                    cx="246"
                                    cy="22"
                                    rx="16"
                                    ry="10" />
                                <ellipse
                                    cx="276"
                                    cy="12"
                                    rx="22"
                                    ry="12" />
                                <ellipse
                                    cx="314"
                                    cy="8"
                                    rx="26"
                                    ry="11" />
                            </g>
                            <path
                                d="M110 8 L18 100 M110 8 L290 16 M290 16 L386 102 M110 10 L96 108 M110 10 L124 108 M290 18 L276 110 M290 18 L304 110"
                                stroke="#2A2620"
                                stroke-width="0.8"
                                fill="none"
                                opacity="0.8" />
                            <path
                                d="M110 108 V6 M290 110 V14"
                                stroke="#2A2620"
                                stroke-width="2.4"
                                stroke-linecap="round" />
                            <path
                                d="M92 30 H128 M96 50 H124 M290 40 L326 60"
                                stroke="#2A2620"
                                stroke-width="1.6"
                                stroke-linecap="round" />
                            <path
                                d="M205 94 L209 30 L232 30 L228 94 Z"
                                fill="#2B2B2E"
                                stroke="#1A1A1C"
                                stroke-width="1.2" />
                            <path
                                d="M208 42 L231 42"
                                stroke="#B8862E"
                                stroke-width="3" />
                            <rect
                                x="130"
                                y="92"
                                width="134"
                                height="17"
                                fill="#F1EADA"
                                stroke="#2A2620"
                                stroke-width="1.2" />
                            <rect
                                x="150"
                                y="80"
                                width="42"
                                height="12"
                                fill="#F1EADA"
                                stroke="#2A2620"
                                stroke-width="1.2" />
                            <rect
                                v-for="x in WINDOWS"
                                v-bind:key="`w${x}`"
                                y="97"
                                width="8"
                                height="5"
                                fill="#5C6B78"
                                v-bind:x="x" />
                            <path
                                d="M300 92 C304 102 336 102 340 92 Z"
                                fill="#E9DFC8"
                                stroke="#2A2620"
                                stroke-width="1.1" />
                            <path
                                d="M296 86 V96 M344 86 V96"
                                stroke="#2A2620"
                                stroke-width="1.4" />
                            <path
                                d="M18 100 C30 104 40 108 60 108 L340 110 C360 110 372 106 386 102 L380 128 C374 150 360 170 330 176 L60 176 C44 172 34 150 26 128 Z"
                                fill="url(#explorer-hull)" />
                            <path
                                d="M18 100 C30 104 40 108 60 108 L340 110 C360 110 372 106 386 102 L380 128 C374 150 360 170 330 176 L60 176 C44 172 34 150 26 128 Z"
                                fill="#8E3E26"
                                opacity="0.85"
                                clip-path="url(#explorer-ship-below)" />
                            <path
                                d="M22 108 C40 113 60 114 80 114 L340 116 C360 116 372 113 384 110"
                                stroke="#B8862E"
                                stroke-width="1.6"
                                fill="none" />
                            <circle
                                v-for="x in PORTHOLES"
                                v-bind:key="`p${x}`"
                                cy="122"
                                r="2.6"
                                fill="#2A2620"
                                v-bind:cx="x" />
                            <path
                                d="M18 100 C30 104 40 108 60 108 L340 110 C360 110 372 106 386 102 L380 128 C374 150 360 170 330 176 L60 176 C44 172 34 150 26 128 Z"
                                fill="none"
                                stroke="#2A2620"
                                stroke-width="1.6" />
                            <path
                                d="M60 106 L14 56"
                                stroke="#2A2620"
                                stroke-width="2.6"
                                stroke-linecap="round" />
                            <circle
                                cx="14"
                                cy="56"
                                r="2.6"
                                fill="#2A2620" />
                        </g>
                        <path
                            d="M18 100 C30 104 40 108 60 108 L340 110 C360 110 372 106 386 102 L380 128 C374 150 360 170 330 176 L60 176 C44 172 34 150 26 128 Z"
                            fill="#5D9FB0"
                            opacity="0.45"
                            clip-path="url(#explorer-ship-below)" />
                    </svg>
                </div>

                <svg
                    class="lines"
                    aria-hidden="true"
                    v-bind:width="width"
                    v-bind:height="bedY">
                    <path
                        v-for="(cable, i) in rigging.cables"
                        v-bind:key="i"
                        stroke="#1B1A18"
                        fill="none"
                        opacity="0.85"
                        v-bind:stroke-width="cable.weight"
                        v-bind:d="cable.d" />
                    <path
                        stroke="#FBF6EA"
                        stroke-width="0.8"
                        stroke-dasharray="5 4"
                        opacity="0.55"
                        v-bind:d="lead.line" />
                    <path
                        fill="#5A5248"
                        stroke="#1B1A18"
                        stroke-width="0.8"
                        v-bind:d="lead.weight" />
                </svg>

                <span
                    class="lead-label"
                    v-bind:style="{ top : `${bedY - 40}px`, right : `${width - lead.x + 8}px` }">{{ soundingLabel }}</span>

                <button
                    v-for="item in rigging.items"
                    v-bind:key="item.key"
                    type="button"
                    class="gear"
                    v-bind:style="{ left : `${item.left}px`, top : `${item.top}px`, width : `${item.width}px` }"
                    v-on:click="openGear = item.key">
                    <svg
                        filter="url(#explorer-ink)"
                        v-bind:viewBox="`0 0 ${item.drawing.width} ${item.drawing.height}`"
                        v-html="item.drawing.svg"></svg>
                    <span class="gear__tag">{{ GEAR[item.key].name }}</span>
                </button>

                <button
                    v-if="rigging.hand"
                    type="button"
                    class="gear gear--hand"
                    v-bind:style="{ left : `${rigging.hand.left}px`, top : `${rigging.hand.top}px` }"
                    v-on:click="openGear = 'rif'">
                    <span class="gear__tag">{{ GEAR.rif.name }} · met de hand</span>
                </button>

                <button
                    v-for="item in placed"
                    v-bind:key="item.specimen.id"
                    type="button"
                    class="specimen"
                    v-bind:data-id="item.specimen.id"
                    v-bind:place="item.place"
                    v-bind:motion="item.motion"
                    v-bind:is-seen="seen.has(String(item.specimen.id)) ? '' : null"
                    v-bind:has-image="item.specimen.image ? '' : null"
                    v-bind:aria-label="item.specimen.name"
                    v-bind:style="{ left : `${item.left}px`, top : `${item.top}px`, width : `${item.size}px`, height : `${item.size}px` }"
                    v-on:click="emit('select-specimen', item.specimen)">
                    <img
                        v-if="item.specimen.image"
                        class="specimen__image"
                        alt=""
                        loading="lazy"
                        v-bind:src="item.specimen.image.src">
                    <el-explorer-icon
                        v-else
                        v-bind:group="item.specimen.group"
                        v-bind:size="24" />
                    <el-explorer-badge
                        v-if="item.specimen.isNameBearer"
                        class="specimen__badge"
                        v-bind:size="22" />
                </button>

                <div
                    class="seabed"
                    v-bind:style="{ background : `linear-gradient(to bottom, ${bedColours[0]}, ${bedColours[1]} 260px, #3A3329)` }">
                    <svg
                        class="seabed__edge"
                        viewBox="0 0 400 60"
                        preserveAspectRatio="none"
                        aria-hidden="true">
                        <path
                            d="M0 30 C40 18 70 34 110 26 S190 14 230 28 S320 36 360 22 S395 26 400 28 V60 H0 Z"
                            v-bind:fill="bedColours[0]" />
                        <path
                            d="M0 30 C40 18 70 34 110 26 S190 14 230 28 S320 36 360 22 S395 26 400 28"
                            fill="none"
                            stroke="#3B342C"
                            stroke-width="1"
                            opacity="0.5" />
                    </svg>

                    <div class="bed-tag">
                        <p class="kicker">Bodem op {{ Math.round(depth).toLocaleString('nl-NL') }} m · notitie 1899</p>
                        <em>{{ station.bodem || 'Niet genoteerd.' }}</em>
                    </div>

                    <section class="card">
                        <p class="kicker">Met {{ gearWords }} naar boven</p>
                        <h3 class="card__title">De vangst van station {{ station.nummer }}</h3>

                        <p
                            v-if="!station.specimens.length"
                            class="card__note">Van dit station ligt, voor zover we zeker weten, niets in een museum.</p>

                        <template v-else>
                            <p class="card__note">
                                <template v-if="places.has('bottom')">Bodemleven, opgehaald met tuig over de bodem, ligt op de bodem. </template>
                                <template v-if="places.has('net')">Wat met een net is gevangen, zweeft binnen het netbereik. </template>
                                <template v-if="places.has('random')">Van de rest weten we niet op welke diepte het gevangen is; die plek is willekeurig.</template>
                            </p>

                            <div class="catch">
                                <button
                                    v-for="specimen in station.specimens"
                                    v-bind:key="specimen.id"
                                    type="button"
                                    class="catch__item"
                                    v-on:click="emit('select-specimen', specimen)">
                                    <span class="catch__visual">
                                        <img
                                            v-if="specimen.image"
                                            alt=""
                                            loading="lazy"
                                            v-bind:src="specimen.image.src">
                                        <el-explorer-icon
                                            v-else
                                            v-bind:group="specimen.group"
                                            v-bind:size="30" />
                                        <el-explorer-badge
                                            v-if="specimen.isNameBearer"
                                            class="catch__badge"
                                            v-bind:size="22" />
                                    </span>
                                    <em class="catch__name">{{ specimen.name }}</em>
                                    <span class="catch__meta">{{ groupName(specimen.group) }}</span>
                                </button>
                            </div>
                        </template>
                    </section>

                    <figure
                        v-if="station.photo"
                        class="card photo">
                        <p class="kicker">Foto bij dit station</p>
                        <a
                            class="photo__frame"
                            target="_blank"
                            rel="noopener"
                            v-bind:href="station.photo.sourceUrl">
                            <img
                                alt=""
                                loading="lazy"
                                v-bind:src="station.photo.src">
                        </a>
                        <figcaption>
                            <em class="photo__caption">{{ station.photo.caption }}</em>
                            <span class="photo__credit">
                                {{ [station.photo.credit, station.photo.license].filter(Boolean).join(' · ') }}
                                · <a
                                    target="_blank"
                                    rel="noopener"
                                    v-bind:href="station.photo.sourceUrl">Wikimedia Commons</a>
                            </span>
                        </figcaption>
                    </figure>

                    <section class="card">
                        <p class="kicker">Uit de stationslijst</p>
                        <dl class="log">
                            <template
                                v-for="[label, value] in log"
                                v-bind:key="label">
                                <dt>{{ label }}</dt>
                                <dd>{{ value }}</dd>
                            </template>
                        </dl>
                        <p
                            v-if="station.diepte_vandaag_m > 0 && !station.positie_geschat"
                            class="card__note">Diepte hier volgens metingen van nu (GEBCO 2024): {{ station.diepte_vandaag_m.toLocaleString('nl-NL') }} m.</p>

                        <p class="kicker">Bronnen</p>
                        <ul class="sources">
                            <li v-if="station.wikidata">
                                <a
                                    target="_blank"
                                    rel="noopener"
                                    v-bind:href="wikidataUrl + station.wikidata">Wikidata: station {{ station.nummer }}</a>
                            </li>
                            <li>
                                <a
                                    href="https://doi.org/10.5281/zenodo.23433434"
                                    target="_blank"
                                    rel="noopener">Stationslijst van de Siboga-expeditie</a>
                                (Fauconnier 2026, naar Weber 1902<template v-if="station.pagina">, p. {{ station.pagina }}</template>)
                            </li>
                        </ul>
                    </section>

                    <button
                        type="button"
                        class="up"
                        v-on:click="surface()">↑ Terug naar boven</button>
                </div>
            </div>
        </div>

        <div class="hud">
            <p class="hud__label">
                <strong>Station {{ station.nummer }}</strong>
                {{ dates }}
            </p>
            <p
                class="gauge"
                aria-live="off">
                <span class="gauge__value">{{ Math.round(reading).toLocaleString('nl-NL') }}</span>
                <span class="gauge__unit">m</span>
            </p>
            <button
                type="button"
                class="hud__surface"
                v-on:click="surface()">↑ Boven water</button>
        </div>

        <div
            v-if="openGear"
            class="sheet">
            <button
                type="button"
                class="sheet__backdrop"
                aria-label="Sluiten"
                v-on:click="openGear = null"></button>
            <article
                class="sheet__card"
                role="dialog"
                aria-modal="true"
                v-bind:aria-label="GEAR[openGear].name">
                <button
                    type="button"
                    class="sheet__close"
                    aria-label="Sluiten"
                    v-on:click="openGear = null">
                    <el-icon
                        name="close"
                        v-bind:size="20" />
                </button>
                <p class="kicker">Tuig · {{ GEAR[openGear].en }}</p>
                <h2 class="sheet__title">{{ GEAR[openGear].name }}</h2>
                <figure
                    v-if="GEAR[openGear].photo"
                    class="sheet__photo">
                    <img
                        alt=""
                        v-bind:src="GEAR[openGear].photo">
                    <figcaption>{{ GEAR[openGear].caption }} {{ PHOTO_CREDIT }}</figcaption>
                </figure>
                <p>{{ GEAR[openGear].text }}</p>
            </article>
        </div>
    </section>
</template>

<style lang="scss" scoped>
    .el-explorer-dive {
        position: absolute;
        inset: 0;
        z-index: 5;
        overflow: hidden;
    }

    .defs {
        position: absolute;
    }

    .kicker {
        margin: 0;
        font-family: var(--font-header);
        font-size: 1.1rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--c-ink-soft);
    }

    .scroll {
        position: absolute;
        inset: 0;
        overflow-y: auto;
        overflow-x: hidden;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;

        &::-webkit-scrollbar {
            display: none;
        }
    }

    .air {
        height: 100%;
    }

    .sea {
        position: relative;

        &::before,
        &::after {
            content: "";
            position: absolute;
            inset: 0;
            mix-blend-mode: multiply;
            pointer-events: none;
        }

        &::before {
            background: var(--wash-texture);
            background-size: 42rem;
            opacity: 0.55;
        }

        &::after {
            background: var(--paper-texture);
            opacity: 0.7;
        }
    }

    .waves {
        position: absolute;
        left: 0;
        top: -15px;
        height: 22px;
        z-index: 1;
        animation: waves 7s linear infinite;
    }

    .rays {
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        pointer-events: none;
        background:
            linear-gradient(100deg, transparent 18%, rgba(255, 255, 240, 0.22) 22%, transparent 27%),
            linear-gradient(80deg, transparent 52%, rgba(255, 255, 240, 0.16) 57%, transparent 63%),
            linear-gradient(95deg, transparent 72%, rgba(255, 255, 240, 0.18) 75%, transparent 80%);
        mask-image: linear-gradient(to bottom, #000, transparent);
        animation: rays 9s ease-in-out infinite alternate;
    }

    .snow {
        position: absolute;
        left: 0;
        right: 0;
        pointer-events: none;
        background-image:
            radial-gradient(circle, rgba(255, 255, 255, 0.55) 0 1px, transparent 1.6px),
            radial-gradient(circle, rgba(255, 255, 255, 0.35) 0 1px, transparent 1.4px);
        background-size: 53px 61px, 37px 43px;
        background-position: 0 0, 19px 23px;
        mask-image: linear-gradient(to bottom, transparent, #000 40rem);
    }

    .ship {
        position: absolute;
        z-index: 3;
        pointer-events: none;

        svg {
            display: block;
            width: 100%;
            height: auto;
            overflow: visible;
        }
    }

    .ship__body {
        transform-origin: 50% 70%;
        animation: bob 4s ease-in-out infinite;
    }

    .lines {
        position: absolute;
        left: 0;
        top: 0;
        z-index: 2;
        overflow: visible;
        pointer-events: none;
    }

    .lead-label {
        position: absolute;
        z-index: 2;
        font-family: var(--font-header);
        font-size: 1.2rem;
        letter-spacing: 0.06em;
        color: var(--c-paper);
        text-shadow: 0 1px 2px rgba(8, 26, 44, 0.6);
        white-space: nowrap;
    }

    .ruler {
        position: absolute;
        left: 0;
        top: 0;
        z-index: 2;
        pointer-events: none;
    }

    .ruler__tick {
        position: absolute;
        left: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transform: translateY(-50%);
        font-family: var(--font-header);
        font-size: 1.1rem;
        letter-spacing: 0.06em;
        color: rgba(251, 246, 234, 0.85);
        white-space: nowrap;

        &::before {
            content: "";
            width: 1.2rem;
            height: 1px;
            background: currentColor;
        }
    }

    .zone {
        position: absolute;
        right: 1.4rem;
        z-index: 2;
        max-width: 50%;
        margin: 0;
        text-align: right;
        font-family: var(--font-header);
        font-style: italic;
        font-size: 1.3rem;
        line-height: 1.25;
        color: rgba(251, 246, 234, 0.85);
        pointer-events: none;

        small {
            display: block;
            font-family: var(--font-text);
            font-size: 1.2rem;
            opacity: 0.85;
        }
    }

    .gear {
        position: absolute;
        z-index: 3;
        padding: 0;
        border: 0;
        background: none;
        overflow: visible;
        cursor: pointer;

        svg {
            display: block;
            width: 100%;
            height: auto;
            overflow: visible;
        }
    }

    .gear__tag,
    .bed-tag {
        padding: 0.2rem 0.9rem;
        background: var(--c-paper) var(--paper-texture);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        color: var(--c-ink);
    }

    .gear__tag {
        position: absolute;
        left: 50%;
        top: 100%;
        transform: translate(-50%, 6px) rotate(-2deg);
        font-family: var(--font-header);
        font-size: 1.2rem;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }

    .gear--hand {
        min-height: 4.4rem;

        .gear__tag {
            position: static;
            display: inline-block;
            transform: rotate(-2deg);
        }
    }

    .specimen {
        position: absolute;
        z-index: 4;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        border: 2px solid var(--c-paper);
        border-radius: 50%;
        background: var(--c-paper);
        color: var(--c-ink);
        box-shadow: 2px 5px 8px rgba(5, 20, 35, 0.4);
        cursor: pointer;
        opacity: 0;
        transform: translateY(26px) scale(0.9);
        transition: opacity 0.9s ease, transform 0.9s cubic-bezier(0.2, 0.8, 0.2, 1);

        &[place="bottom"] {
            translate: 0 -100%;
        }

        &[is-seen] {
            opacity: 1;
            transform: translateY(0) scale(1);
        }

        &[motion="drift"] {
            animation: drift 7s ease-in-out infinite;
        }

        &[motion="sway"] {
            animation: sway 5s ease-in-out infinite;
        }
    }

    .specimen__image {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
    }

    .specimen__badge {
        position: absolute;
        top: -0.6rem;
        right: -0.6rem;
    }

    .seabed {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        gap: 2rem;
        padding: 4.6rem 1.4rem 9.6rem;
    }

    .seabed__edge {
        position: absolute;
        left: 0;
        top: -30px;
        width: 100%;
        height: 60px;
    }

    .bed-tag {
        position: relative;
        margin: 0 0.2rem 1.4rem;
        padding: 0.8rem 1.2rem;
        transform: rotate(-1deg);
        font-size: 1.4rem;

        em {
            color: #6B5434;
        }
    }

    .card {
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        padding: 2rem 1.6rem 1.8rem;
        background: var(--c-paper) var(--paper-texture);
        box-shadow: var(--shadow-card);

        &::after {
            content: "";
            position: absolute;
            inset: 5px;
            border: 1px solid var(--c-frame);
            pointer-events: none;
        }
    }

    .card__title {
        margin: 0;
        font-weight: 400;
        font-size: 2.2rem;
    }

    .card__note {
        margin: 0;
        font-size: 1.4rem;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    // An old photograph, in a thin mount on the card
    .photo {
        margin: 0;

        figcaption {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }
    }

    .photo__frame {
        position: relative;
        z-index: 1;
        display: block;
        padding: 0.6rem;
        background: #FBF8F1;
        box-shadow: 0 1px 3px rgba(59, 52, 44, 0.35);

        img {
            display: block;
            width: 100%;
            height: auto;
        }
    }

    .photo__caption {
        font-size: 1.6rem;
    }

    .photo__credit {
        position: relative;
        z-index: 1;
        font-size: 1.2rem;
        color: var(--c-ink-soft);

        a {
            color: inherit;
        }
    }

    .catch {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1.4rem 1.2rem;
        margin-top: 0.6rem;
    }

    .catch__item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem;
        border: 0;
        background: none;
        text-align: center;
        cursor: pointer;
    }

    .catch__visual {
        position: relative;
        width: 8.4rem;
        height: 8.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: var(--c-plate);
        color: var(--c-ink-soft);
        box-shadow: 1px 3px 4px rgba(60, 40, 10, 0.3);

        img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
        }
    }

    .catch__badge {
        position: absolute;
        top: 0;
        right: 0;
    }

    .catch__name {
        font-size: 1.4rem;
        line-height: 1.2;
    }

    .catch__meta {
        font-size: 1.2rem;
        color: var(--c-ink-soft);
    }

    .log {
        position: relative;
        z-index: 1;
        margin: 0 0 1rem;
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 0.4rem 1.2rem;
        font-size: 1.5rem;

        dt {
            color: var(--c-ink-soft);
        }

        dd {
            margin: 0;
            font-style: italic;
        }
    }

    .sources {
        position: relative;
        z-index: 1;
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        font-size: 1.5rem;
    }

    .up {
        align-self: center;
        min-height: 4.4rem;
        padding: 0 2rem;
        border: 1px solid rgba(251, 246, 234, 0.6);
        border-radius: 2.2rem;
        background: rgba(12, 30, 50, 0.5);
        color: var(--c-paper);
        font-family: var(--font-header);
        font-size: 1.3rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        cursor: pointer;
    }

    .hud {
        position: absolute;
        inset: 0;
        z-index: 6;
        pointer-events: none;
    }

    .hud__label {
        position: absolute;
        top: 1.2rem;
        left: 1.2rem;
        max-width: 60%;
        margin: 0;
        padding: 0.6rem 1.1rem 0.7rem;
        background: var(--c-paper) var(--paper-texture);
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
        transform: rotate(-1.2deg);
        font-size: 1.3rem;
        line-height: 1.25;

        strong {
            display: block;
            font-family: var(--font-header);
            font-weight: 400;
            font-size: 1.7rem;
        }
    }

    // Below the menu button of the app
    .gauge {
        position: absolute;
        top: 7.6rem;
        right: 1.6rem;
        display: flex;
        align-items: baseline;
        gap: 0.3rem;
        margin: 0;
        padding: 0.4rem 1.2rem 0.6rem;
        border-radius: 3px;
        background: rgba(12, 30, 50, 0.55);
        color: var(--c-paper);
        font-family: var(--font-header);
        backdrop-filter: blur(4px);
    }

    .gauge__value {
        min-width: 2.6em;
        text-align: right;
        font-size: 2.6rem;
        font-variant-numeric: tabular-nums;
    }

    .gauge__unit {
        font-size: 1.4rem;
    }

    .hud__surface {
        position: absolute;
        left: 50%;
        bottom: 1.6rem;
        min-height: 4.4rem;
        padding: 0 1.8rem;
        transform: translateX(-50%);
        border: 1px solid rgba(251, 246, 234, 0.6);
        border-radius: 2.2rem;
        background: rgba(12, 30, 50, 0.5);
        color: var(--c-paper);
        font-family: var(--font-header);
        font-size: 1.3rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        pointer-events: auto;
        backdrop-filter: blur(4px);
        cursor: pointer;
    }

    .sheet {
        position: absolute;
        inset: 0;
        z-index: 7;
        display: flex;
        align-items: flex-end;
        justify-content: center;
    }

    .sheet__backdrop {
        position: absolute;
        inset: 0;
        border: 0;
        background: rgba(12, 32, 52, 0.4);
        cursor: pointer;
    }

    .sheet__card {
        position: relative;
        width: 100%;
        max-width: var(--sheet-width);
        max-height: 80%;
        overflow-y: auto;
        padding: 2rem 1.8rem 2.6rem;
        background: var(--c-paper) var(--paper-texture);
        border-radius: 16px 16px 0 0;
        box-shadow: var(--shadow-sheet);
        animation: rise 0.35s cubic-bezier(0.2, 0.7, 0.2, 1);

        p {
            margin: 0 0 1rem;
        }
    }

    .sheet__close {
        position: absolute;
        top: 0.8rem;
        right: 0.8rem;
        width: 4.4rem;
        height: 4.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 0;
        background: transparent;
        color: var(--c-marine);
        cursor: pointer;
    }

    .sheet__title {
        margin: 0.2rem 0 1rem;
        font-weight: 400;
        font-size: 2.6rem;
    }

    .sheet__photo {
        margin: 0 0 1.2rem;

        img {
            display: block;
            width: 100%;
            border-radius: 4px;
        }

        figcaption {
            margin-top: 0.4rem;
            font-size: 1.2rem;
            color: var(--c-ink-soft);
        }
    }

    @keyframes waves {
        to {
            transform: translateX(-50%);
        }
    }

    @keyframes rays {
        from {
            opacity: 0.6;
            transform: translateX(-10px);
        }

        to {
            opacity: 1;
            transform: translateX(10px);
        }
    }

    @keyframes bob {
        0%,
        100% {
            transform: translateY(0) rotate(-0.6deg);
        }

        50% {
            transform: translateY(3px) rotate(0.6deg);
        }
    }

    @keyframes drift {
        0%,
        100% {
            translate: 0 0;
        }

        50% {
            translate: 0 -12px;
        }
    }

    @keyframes sway {
        0%,
        100% {
            rotate: -2deg;
        }

        50% {
            rotate: 2deg;
        }
    }

    @keyframes rise {
        from {
            transform: translateY(100%);
        }
    }
</style>
