<script setup>
    import { computed, onBeforeUnmount, ref, watch } from 'vue';
    import { stationIndexAt } from './data.js';
    import ElExplorerLikeness from './el-explorer-likeness.vue';

    // When the ship sails past a station, the photos of what was found there bob past just above the
    // timeline, a bit faster than the timeline moves, and are gone again. Throttled, so a fast scrub or a
    // high playing speed does not flood the screen.
    const PER_STATION = 6;
    const MAX_VISIBLE = 8;
    // Above this speed only one photo per station comes by, and at most one group per interval
    const FAST_KM_PER_SECOND = 100;
    const FAST_INTERVAL = 700;
    // Same scale as the timeline strip
    const PX_PER_KM = 0.6;
    const MIN_PX_PER_SECOND = 70;
    const SIZE = 56;
    // The photos leave one after the other with this much room between them, also across stations
    const SPACING = SIZE * 1.3;

    const emit = defineEmits(['select-specimen']);

    const props = defineProps({
        stations : {
            type : Array,
            required : true
        },
        // Kilometres along the route
        position : {
            type : Number,
            default : 0
        },
        // Off while flying to a station or diving
        isActive : {
            type : Boolean,
            default : true
        }
    });

    const root = ref(null);
    const items = ref([]);

    const current = computed(() => stationIndexAt(props.stations, props.position));
    const reducesMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

    let nextId = 0;
    let lastPosition = null;
    let lastTime = 0;
    let kmPerSecond = 0;
    let lastFastGroup = 0;
    // When the next photo may leave, so a new group queues behind the last one instead of overlapping
    let nextFree = 0;
    const timers = new Set();

    function launch(station) {
        const now = performance.now();
        const isFast = kmPerSecond > FAST_KM_PER_SECOND;

        if (isFast && now - lastFastGroup < FAST_INTERVAL) {
            return;
        }

        const room = MAX_VISIBLE - items.value.length;
        const withPhoto = station.specimens.filter((specimen) => specimen.thumb);
        const count = Math.min(room, isFast ? 1 : PER_STATION, withPhoto.length);

        if (count <= 0) {
            return;
        }

        if (isFast) {
            lastFastGroup = now;
        }

        const width = root.value?.clientWidth ?? 390;
        // The timeline moves left by the sailing speed; the photos go a little faster than that
        const pxPerSecond = Math.max(MIN_PX_PER_SECOND, kmPerSecond * PX_PER_KM * 1.4);
        const distance = width / 2 + SIZE * 2;
        const duration = Math.min(9000, Math.max(2600, distance / pxPerSecond * 1000));
        const gap = SPACING / (distance / duration);

        withPhoto.slice(0, count).forEach((specimen) => {
            const start = Math.max(now, nextFree);
            const delay = start - now;

            nextFree = start + gap;

            const item = {
                id : nextId++,
                specimen,
                style : {
                    left : `${width / 2}px`,
                    '--distance' : `${-distance}px`,
                    '--duration' : `${duration}ms`,
                    '--delay' : `${delay}ms`,
                    '--bob' : `${1800 + (specimen.id % 7) * 160}ms`,
                    '--lift' : `${(specimen.id % 5) * 6}px`
                }
            };

            items.value = [...items.value, item];

            // Safety net in case animationend never fires (hidden tab, removed element)
            const timer = setTimeout(() => remove(item.id), duration + delay + 500);

            timers.add(timer);
        });
    }

    function remove(id) {
        items.value = items.value.filter((item) => item.id !== id);
    }

    watch(() => props.position, (position) => {
        const now = performance.now();

        if (lastPosition !== null && now > lastTime) {
            const measured = Math.abs(position - lastPosition) / ((now - lastTime) / 1000);

            // Smoothed, so a single jump does not count as sailing fast
            kmPerSecond = kmPerSecond * 0.7 + measured * 0.3;
        }

        lastPosition = position;
        lastTime = now;
    });

    watch(current, (now, before) => {
        // Only when sailing forward past one or more stations, not when scrubbing back
        if (!props.isActive || reducesMotion || before === undefined || now <= before) {
            return;
        }

        for (let i = before + 1; i <= now; i++) {
            const station = props.stations[i];

            if (station?.specimens.length) {
                launch(station);
            }
        }
    });

    watch(() => props.isActive, (isActive) => {
        if (!isActive) {
            items.value = [];
        }
    });

    onBeforeUnmount(() => timers.forEach((timer) => clearTimeout(timer)));
</script>

<template>
    <div
        ref="root"
        class="el-explorer-parade"
        aria-hidden="true">
        <button
            v-for="item in items"
            v-bind:key="item.id"
            type="button"
            class="item"
            tabindex="-1"
            v-bind:style="item.style"
            v-on:animationend.self="remove(item.id)"
            v-on:click="emit('select-specimen', item.specimen)">
            <span class="bob">
                <img
                    class="photo"
                    alt=""
                    v-bind:src="item.specimen.thumb">
                <el-explorer-likeness
                    v-if="item.specimen.illustration"
                    class="likeness"
                    v-bind:illustration="item.specimen.illustration" />
            </span>
        </button>
    </div>
</template>

<style lang="scss" scoped>
    .el-explorer-parade {
        position: absolute;
        left: 0;
        right: 0;
        height: 13rem;
        overflow: hidden;
        pointer-events: none;
    }

    .item {
        position: absolute;
        // Above the hint that sits on top of the timeline
        bottom: 4.6rem;
        width: 5.6rem;
        height: 5.6rem;
        margin-left: -2.8rem;
        padding: 0;
        border: 0;
        background: none;
        cursor: pointer;
        pointer-events: auto;
        opacity: 0;
        animation: pass var(--duration) linear var(--delay) both;
    }

    .bob {
        position: relative;
        display: block;
        width: 100%;
        height: 100%;
        animation: bob var(--bob) ease-in-out infinite alternate;
    }

    .photo {
        display: block;
        width: 100%;
        height: 100%;
        border: 2px solid var(--c-paper);
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 3px 8px rgba(8, 26, 44, 0.45);
    }

    .likeness {
        position: absolute;
        left: 50%;
        bottom: -0.8rem;
        translate: -50% 0;
    }

    @keyframes pass {
        0% {
            opacity: 0;
            transform: translateX(0) scale(0.6);
        }

        10% {
            opacity: 1;
            transform: translateX(calc(var(--distance) * 0.1)) scale(1);
        }

        85% {
            opacity: 1;
        }

        100% {
            opacity: 0;
            transform: translateX(var(--distance)) scale(0.9);
        }
    }

    @keyframes bob {
        from {
            transform: translateY(calc(-0.4rem - var(--lift))) rotate(-4deg);
        }

        to {
            transform: translateY(calc(0.4rem - var(--lift))) rotate(4deg);
        }
    }
</style>
