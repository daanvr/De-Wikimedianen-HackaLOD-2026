<script setup>
    import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { stationIndexAt } from './data.js';

    // The strip is laid out by distance along the route
    const PX_PER_KM = 0.6;
    // Height of the strip above and below the sea surface, in pixels
    const SURFACE_Y = 40;
    const DEPTH_HEIGHT = 70;
    const MAX_DEPTH = 7200;
    const MAX_DOTS = 5;
    const MAX_FLIGHTS = 24;
    const MONTHS = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];

    const emit = defineEmits(['update:position', 'select', 'open-net']);

    const props = defineProps({
        stations : {
            type : Array,
            required : true
        },
        line : {
            type : Array,
            required : true
        },
        length : {
            type : Number,
            required : true
        },
        // Kilometres along the route
        position : {
            type : Number,
            default : 0
        },
        total : {
            type : Number,
            default : 0
        }
    });

    const root = ref(null);
    const track = ref(null);
    const net = ref(null);
    const flights = ref(null);
    const width = ref(390);
    const isBumping = ref(false);

    const dots = new Map();

    let tween = null;
    let bumpTimer = null;
    let resizeObserver = null;

    const half = computed(() => width.value / 2);
    const stripWidth = computed(() => Math.ceil(props.length * PX_PER_KM + width.value));
    const current = computed(() => stationIndexAt(props.stations, props.position));
    const collected = computed(() => props.stations[current.value]?.collected ?? 0);
    const share = computed(() => props.total ? collected.value / props.total : 0);
    const fillY = computed(() => (40 - 31 * share.value).toFixed(1));

    // A column for every sounding: the depth measured in 1899
    const soundings = computed(() => props.stations
        .filter((station) => station.diepte_m !== null)
        .map((station) => ({
            station,
            left : xOf(station.km),
            height : Math.max(2, depthPixels(station.diepte_m))
        })));

    // Dots above the surface where the ship brought specimens up
    const finds = computed(() => props.stations
        .filter((station) => station.specimens.length)
        .map((station) => ({
            station,
            left : xOf(station.km),
            dots : Math.min(MAX_DOTS, station.specimens.length),
            hasNameBearer : station.specimens.some((specimen) => specimen.isNameBearer),
            label : `Station ${station.nummer}: ${station.specimens.length} specimens`
        })));

    const months = computed(() => {
        const seen = new Set();
        const result = [];

        for (const station of props.stations) {
            const key = station.datum?.slice(0, 7);

            if (key && !seen.has(key)) {
                seen.add(key);
                result.push({
                    key,
                    left : xOf(station.km),
                    label : `${MONTHS[Number(key.slice(5, 7)) - 1]} ${key.slice(0, 4)}`
                });
            }
        }

        return result;
    });

    // Today's depth of the sea along the route
    const todayPath = computed(() => props.line
        .map(([km, , , depth], i) => `${i ? 'L' : 'M'}${xOf(km).toFixed(1)} ${(SURFACE_Y + depthPixels(Math.max(0, depth))).toFixed(1)}`)
        .join(''));

    function bump() {
        clearTimeout(bumpTimer);
        isBumping.value = false;

        requestAnimationFrame(() => {
            isBumping.value = true;
            bumpTimer = setTimeout(() => {
                isBumping.value = false;
            }, 260);
        });
    }

    function centerOf(element, origin) {
        const box = element.getBoundingClientRect();

        return {
            x : Math.max(0, Math.min(origin.width, box.left + box.width / 2 - origin.left)),
            y : box.top + box.height / 2 - origin.top
        };
    }

    function depthPixels(depth) {
        return Math.sqrt(Math.min(depth, MAX_DEPTH) / MAX_DEPTH) * DEPTH_HEIGHT;
    }

    // Small dots fly from a station into the net, or back out when scrubbing back
    function fly(station, isReturning, budget) {
        const source = dots.get(station.index);

        if (!source || !net.value || !flights.value) {
            return 0;
        }

        const origin = root.value.getBoundingClientRect();
        const stationPoint = centerOf(source, origin);
        const netPoint = centerOf(net.value, origin);
        const count = Math.min(budget, station.specimens.length, 8);

        for (let k = 0; k < count; k++) {
            const from = isReturning ? netPoint : stationPoint;
            const to = isReturning ? stationPoint : netPoint;
            const middle = {
                x : (from.x + to.x) / 2 + (Math.random() - 0.5) * 60,
                y : Math.min(from.y, to.y) - 60 - Math.random() * 50
            };
            const dot = document.createElement('span');

            dot.className = station.specimens[k]?.isNameBearer ? 'flight flight--type' : 'flight';
            flights.value.appendChild(dot);

            const animation = dot.animate([
                {
                    transform : `translate(${from.x}px, ${from.y}px) scale(1)`
                },
                {
                    transform : `translate(${middle.x}px, ${middle.y}px) scale(1.7)`,
                    offset : 0.45
                },
                {
                    transform : `translate(${to.x}px, ${to.y}px) scale(0.5)`,
                    opacity : 0.4
                }
            ], {
                duration : 620 + k * 50,
                delay : k * 45,
                easing : 'cubic-bezier(0.3, 0.6, 0.35, 1)',
                fill : 'backwards'
            });

            animation.onfinish = () => {
                dot.remove();

                if (!isReturning) {
                    bump();
                }
            };
        }

        return count;
    }

    function next() {
        const target = props.stations.find((station) => station.km > props.position + 0.5);

        if (target) {
            scrollToKm(target.km);
        }
    }

    function onScroll() {
        if (track.value) {
            emit('update:position', Math.max(0, Math.min(props.length, track.value.scrollLeft / PX_PER_KM)));
        }
    }

    function scrollToKm(km, duration = null) {
        if (!track.value) {
            return;
        }

        const start = track.value.scrollLeft;
        const end = km * PX_PER_KM;
        const time = duration ?? Math.min(1400, 450 + Math.abs(end - start) * 0.25);
        const startedAt = performance.now();

        cancelAnimationFrame(tween);

        if (!time) {
            track.value.scrollLeft = end;
            return;
        }

        function step(now) {
            const progress = Math.min(1, (now - startedAt) / time);
            const eased = progress < 0.5 ? 4 * progress ** 3 : 1 - (-2 * progress + 2) ** 3 / 2;

            track.value.scrollLeft = start + (end - start) * eased;

            if (progress < 1) {
                tween = requestAnimationFrame(step);
            }
        }

        tween = requestAnimationFrame(step);
    }

    function setDot(index, element) {
        if (element) {
            dots.set(index, element);
        } else {
            dots.delete(index);
        }
    }

    // A finger or wheel on the strip takes over from a running animation
    function stopTween() {
        cancelAnimationFrame(tween);
    }

    function xOf(km) {
        return half.value + km * PX_PER_KM;
    }

    watch(current, (now, before) => {
        if (before === undefined || now === before) {
            return;
        }

        const isReturning = now < before;
        const [from, to] = isReturning ? [now + 1, before] : [before + 1, now];
        let budget = MAX_FLIGHTS;

        for (let i = Math.max(0, from); i <= to && budget > 0; i++) {
            const station = props.stations[i];

            if (station?.specimens.length) {
                budget -= fly(station, isReturning, budget);
            }
        }
    });

    // Position changed from outside, for example a station picked on the map
    watch(() => props.position, (position) => {
        if (track.value && Math.abs(track.value.scrollLeft / PX_PER_KM - position) > 1) {
            scrollToKm(position);
        }
    });

    onMounted(() => {
        resizeObserver = new ResizeObserver(() => {
            width.value = track.value.clientWidth;
            nextTick(() => scrollToKm(props.position, 0));
        });
        resizeObserver.observe(track.value);
        width.value = track.value.clientWidth;
        nextTick(() => scrollToKm(props.position, 0));
    });

    onBeforeUnmount(() => {
        cancelAnimationFrame(tween);
        clearTimeout(bumpTimer);
        resizeObserver?.disconnect();
    });
</script>

<template>
    <div
        ref="root"
        class="el-explorer-timeline">
        <button
            ref="net"
            type="button"
            class="net"
            v-bind:is-bumping="isBumping ? '' : null"
            v-bind:aria-label="`Het netje: ${collected} van ${total} specimens. Bekijk wat erin zit.`"
            v-on:click="emit('open-net')">
            <span class="net__bar">
                <span
                    class="net__progress"
                    v-bind:style="{ width : `${share * 100}%` }"></span>
            </span>

            <svg
                class="net__bag"
                viewBox="0 0 44 44"
                aria-hidden="true">
                <defs>
                    <clipPath id="explorer-net-bag">
                        <path d="M7 9 C7 22 13 37 22 40 C31 37 37 22 37 9 Z" />
                    </clipPath>
                </defs>
                <rect
                    x="0"
                    width="44"
                    height="44"
                    fill="#D88A63"
                    clip-path="url(#explorer-net-bag)"
                    v-bind:y="fillY" />
                <path
                    d="M7 9 C7 22 13 37 22 40 C31 37 37 22 37 9"
                    fill="none"
                    stroke="#1B2433"
                    stroke-width="1.4" />
                <path
                    d="M12 9 L22 40 M17 9 L24 39 M27 9 L22 40 M32 9 L20 39 M8 17 H36 M10 25 H34 M14 33 H30"
                    fill="none"
                    stroke="#1B2433"
                    stroke-width="0.7"
                    opacity="0.55" />
                <ellipse
                    cx="22"
                    cy="9"
                    rx="15"
                    ry="3.5"
                    fill="#FBF8F1"
                    stroke="#1B2433"
                    stroke-width="1.4" />
            </svg>

            <span class="net__count">{{ collected }}</span>
        </button>

        <div class="panel">
            <div
                ref="track"
                class="track"
                tabindex="0"
                aria-label="Tijdlijn van de reis, op afstand. Sleep om te varen."
                v-on:scroll.passive="onScroll()"
                v-on:pointerdown="stopTween()"
                v-on:wheel.passive="stopTween()">
                <div
                    class="strip"
                    v-bind:style="{ width : `${stripWidth}px` }">
                    <span class="surface"></span>

                    <svg
                        class="today"
                        aria-hidden="true"
                        v-bind:width="stripWidth"
                        v-bind:height="SURFACE_Y + DEPTH_HEIGHT + 2">
                        <path v-bind:d="todayPath" />
                    </svg>

                    <button
                        v-for="column in soundings"
                        v-bind:key="`s${column.station.index}`"
                        type="button"
                        class="sounding"
                        v-bind:style="{ left : `${column.left}px` }"
                        v-bind:is-past="column.station.index <= current ? '' : null"
                        v-bind:aria-label="`Station ${column.station.nummer}, gelood ${Math.round(column.station.diepte_m)} m`"
                        v-on:click="emit('select', column.station)">
                        <span
                            class="column"
                            v-bind:style="{ height : `${column.height}px` }"></span>
                    </button>

                    <button
                        v-for="find in finds"
                        v-bind:key="`f${find.station.index}`"
                        v-bind:ref="(element) => setDot(find.station.index, element)"
                        type="button"
                        class="finds"
                        v-bind:style="{ left : `${find.left}px` }"
                        v-bind:is-past="find.station.index <= current ? '' : null"
                        v-bind:aria-label="find.label"
                        v-on:click="emit('select', find.station)">
                        <span
                            v-for="n in find.dots"
                            v-bind:key="n"
                            class="dot"></span>
                        <span
                            v-if="find.hasNameBearer"
                            class="star"
                            aria-hidden="true">★</span>
                    </button>

                    <span
                        v-for="month in months"
                        v-bind:key="month.key"
                        class="month"
                        v-bind:style="{ left : `${month.left}px` }">{{ month.label }}</span>
                </div>
            </div>

            <span
                class="needle"
                aria-hidden="true"></span>

            <button
                type="button"
                class="next"
                aria-label="Naar het volgende station"
                v-on:click="next()">
                <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    aria-hidden="true">
                    <path d="M9 5l7 7-7 7" />
                </svg>
            </button>
        </div>

        <div
            ref="flights"
            class="flights"
            aria-hidden="true"></div>
    </div>
</template>

<style lang="scss" scoped>
    .el-explorer-timeline {
        --c-brass: #B8862E;

        position: relative;
    }

    .net {
        position: absolute;
        right: 1.2rem;
        bottom: calc(100% + 1.2rem);
        z-index: 2;
        width: 6.8rem;
        height: 6.8rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.2rem;
        padding: 0;
        border: 0;
        border-radius: 50%;
        background: var(--c-paper);
        box-shadow: var(--shadow-float);
        cursor: pointer;
        transition: transform 0.18s ease-out;

        &[is-bumping] {
            transform: scale(1.12);
        }
    }

    .net__bar {
        width: 3.2rem;
        height: 3px;
        border-radius: 2px;
        background: var(--c-rule);
        overflow: hidden;
    }

    .net__progress {
        display: block;
        height: 100%;
        background: var(--c-terracotta);
        transition: width 0.2s ease-out;
    }

    .net__bag {
        width: 3.6rem;
        height: 3.6rem;

        rect {
            transition: y 0.25s ease-out;
        }
    }

    .net__count {
        position: absolute;
        top: -0.4rem;
        right: -0.4rem;
        min-width: 2.6rem;
        height: 2.6rem;
        padding: 0 0.6rem;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 1.3rem;
        background: var(--c-terracotta);
        color: var(--c-paper);
        font-size: 1.3rem;
        font-weight: 600;
    }

    .panel {
        position: relative;
        background: rgba(251, 248, 241, 0.94);
        box-shadow: var(--shadow-sheet);
    }

    .track {
        overflow-x: auto;
        overflow-y: hidden;
        scrollbar-width: none;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior-x: contain;

        &::-webkit-scrollbar {
            display: none;
        }

        &:focus-visible {
            outline-offset: -3px;
        }
    }

    .strip {
        position: relative;
        height: 13.2rem;
    }

    .surface {
        position: absolute;
        left: 0;
        right: 0;
        top: 39px;
        height: 2px;
        background: #6FB0C2;
    }

    .today {
        position: absolute;
        left: 0;
        top: 0;
        pointer-events: none;

        path {
            fill: none;
            stroke: var(--c-marine);
            stroke-width: 1.2;
            stroke-linejoin: round;
            opacity: 0.7;
        }
    }

    .sounding {
        position: absolute;
        top: 41px;
        bottom: 2.4rem;
        width: 12px;
        margin-left: -6px;
        padding: 0;
        border: 0;
        background: transparent;
        cursor: pointer;

        &:hover .column {
            background: var(--c-terracotta);
        }
    }

    .column {
        position: absolute;
        top: 0;
        left: 50%;
        width: 2px;
        margin-left: -1px;
        border-radius: 0 0 1px 1px;
        background: #4387A8;
        opacity: 0.4;

        [is-past] > & {
            opacity: 1;
        }
    }

    .finds {
        position: absolute;
        bottom: calc(100% - 37px);
        min-width: 16px;
        min-height: 16px;
        display: flex;
        flex-direction: column-reverse;
        align-items: center;
        gap: 1px;
        padding: 0;
        border: 0;
        background: transparent;
        transform: translateX(-50%);
        cursor: pointer;
    }

    .dot {
        width: 6px;
        height: 6px;
        box-sizing: border-box;
        border-radius: 50%;
        background: var(--c-terracotta-light);
        border: 1px solid var(--c-terracotta);

        [is-past] > & {
            background: transparent;
            border-color: var(--c-handle);
        }
    }

    .star {
        font-size: 1.1rem;
        line-height: 1;
        color: var(--c-brass);
    }

    .month {
        position: absolute;
        bottom: 0.6rem;
        padding-left: 0.4rem;
        border-left: 1px solid var(--c-frame);
        font-family: var(--font-header);
        font-size: 1.1rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--c-ink-soft);
        white-space: nowrap;
        pointer-events: none;
    }

    .needle {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 50%;
        width: 2px;
        margin-left: -1px;
        background: var(--c-terracotta);
        pointer-events: none;

        &::before {
            content: "";
            position: absolute;
            top: 0;
            left: -5px;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 8px solid var(--c-terracotta);
        }
    }

    .next {
        position: absolute;
        right: 0.8rem;
        top: 50%;
        width: 4.4rem;
        height: 4.4rem;
        margin-top: -2.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--c-frame);
        border-radius: 50%;
        background: var(--c-paper);
        color: var(--c-marine);
        box-shadow: 0 1px 4px rgba(8, 26, 44, 0.2);
        cursor: pointer;

        path {
            fill: none;
            stroke: currentColor;
            stroke-width: 2;
            stroke-linecap: round;
        }
    }

    .flights {
        position: absolute;
        inset: 0;
        z-index: 3;
        pointer-events: none;

        :deep(.flight) {
            position: absolute;
            left: -5px;
            top: -5px;
            width: 10px;
            height: 10px;
            box-sizing: border-box;
            border-radius: 50%;
            background: var(--c-terracotta-light);
            border: 1.5px solid var(--c-paper);
            box-shadow: 0 1px 3px rgba(8, 26, 44, 0.35);
        }

        :deep(.flight--type) {
            background: var(--c-brass);
        }
    }
</style>
