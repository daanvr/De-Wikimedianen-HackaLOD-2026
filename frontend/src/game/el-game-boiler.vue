<script setup>
    // The boiler: a pressure gauge, a fire door that glows with the pressure, and a shovel.
    // Tap the shovel (or press space or the up arrow) to throw coal on the fire.
    import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
    import { OVERHEAT_PRESSURE, PRESSURE_FLOOR } from './physics.js';

    // The needle sweeps from -120 to 120 degrees
    const SWEEP = 240;
    const SHOVEL_KEYS = new Set([' ', 'ArrowUp', 'w', 'W']);

    const emit = defineEmits(['shovel']);

    const props = defineProps({
        pressure : {
            type : Number,
            required : true
        },
        isVenting : {
            type : Boolean,
            default : false
        }
    });

    const swing = ref(0);

    const needle = computed(() => -SWEEP / 2 + SWEEP * props.pressure);
    const isHot = computed(() => props.pressure > OVERHEAT_PRESSURE);
    // From a dull red to a bright yellow
    const glow = computed(() => {
        const level = Math.max(0, (props.pressure - PRESSURE_FLOOR) / (1 - PRESSURE_FLOOR));
        const green = Math.round(70 + 150 * level);
        const blue = Math.round(30 + 60 * level * level);

        return `rgb(255, ${green}, ${blue})`;
    });

    function arc(from, to, radius) {
        const a = (-SWEEP / 2 + SWEEP * from - 90) * Math.PI / 180;
        const b = (-SWEEP / 2 + SWEEP * to - 90) * Math.PI / 180;
        const large = (to - from) * SWEEP > 180 ? 1 : 0;

        return `M${Math.cos(a) * radius},${Math.sin(a) * radius} A${radius},${radius} 0 ${large} 1 ${Math.cos(b) * radius},${Math.sin(b) * radius}`;
    }

    function onKey(event) {
        if (event.type !== 'keydown' || event.repeat || !SHOVEL_KEYS.has(event.key) || event.target.closest?.('input, textarea, button')) {
            return;
        }

        event.preventDefault();
        throwCoal();
    }

    function throwCoal() {
        // A new key restarts the swing animation
        swing.value++;
        emit('shovel');
    }

    const ticks = Array.from({
        length : 11
    }, (_, i) => -SWEEP / 2 + SWEEP * i / 10);

    onMounted(() => {
        window.addEventListener('keydown', onKey);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKey);
    });
</script>

<template>
    <div
        class="el-game-boiler"
        v-bind:is-hot="isHot ? '' : null"
        v-bind:is-venting="isVenting ? '' : null">
        <svg
            class="gauge"
            viewBox="-40 -40 80 80"
            role="meter"
            aria-label="Stoomdruk"
            aria-valuemin="0"
            aria-valuemax="1"
            v-bind:aria-valuenow="pressure.toFixed(2)">
            <circle
                class="gauge__case"
                r="38" />
            <circle
                class="gauge__face"
                r="33" />
            <path
                class="gauge__zone gauge__zone--good"
                v-bind:d="arc(PRESSURE_FLOOR, OVERHEAT_PRESSURE, 27)" />
            <path
                class="gauge__zone gauge__zone--hot"
                v-bind:d="arc(OVERHEAT_PRESSURE, 1, 27)" />
            <line
                v-for="tick in ticks"
                v-bind:key="tick"
                class="gauge__tick"
                x1="0"
                y1="-31"
                x2="0"
                y2="-26"
                v-bind:transform="`rotate(${tick})`" />
            <text
                class="gauge__label"
                y="16"
                text-anchor="middle">stoom</text>
            <g
                class="gauge__needle"
                v-bind:style="{ transform : `rotate(${needle}deg)` }">
                <path d="M-1.6,4 L0,-28 L1.6,4 Z" />
            </g>
            <circle
                class="gauge__pin"
                r="3" />
        </svg>

        <button
            class="shovel"
            type="button"
            aria-label="Kolen scheppen (spatie)"
            title="Kolen scheppen (spatie)"
            v-on:click="throwCoal()">
            <span
                class="door"
                v-bind:style="{ '--glow' : glow }"></span>
            <svg
                v-bind:key="swing"
                class="shovel__icon"
                v-bind:swinging="swing ? '' : null"
                viewBox="0 0 40 40"
                aria-hidden="true">
                <path
                    class="shovel__handle"
                    d="M30 4 L19 22" />
                <path
                    class="shovel__blade"
                    d="M14 19 L25 25 L20 34 Q14 37 9 33 Q6 28 9 24 Z" />
                <circle
                    class="shovel__coal"
                    cx="15"
                    cy="27"
                    r="2.6" />
                <circle
                    class="shovel__coal"
                    cx="19.5"
                    cy="29"
                    r="2.1" />
            </svg>
            <span class="shovel__label">Kolen!</span>
        </button>

        <div
            v-if="isVenting"
            class="steam"
            aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-boiler {
        position: relative;
        display: flex;
        align-items: flex-end;
        gap: 0.8rem;
        user-select: none;
        -webkit-user-select: none;
    }

    .gauge {
        width: 8.4rem;
        height: 8.4rem;
        filter: drop-shadow(2px 4px 4px rgba(8, 26, 44, 0.45));
    }

    .gauge__case {
        fill: #B8862E;
        stroke: #6E4F18;
        stroke-width: 1.5;
    }

    .gauge__face {
        fill: var(--c-paper);
        stroke: #6E4F18;
        stroke-width: 0.8;
    }

    .gauge__zone {
        fill: none;
        stroke-width: 4;
    }

    .gauge__zone--good {
        stroke: var(--c-seaweed);
        opacity: 0.7;
    }

    .gauge__zone--hot {
        stroke: #C0392B;
    }

    .gauge__tick {
        stroke: var(--c-ink);
        stroke-width: 1;
    }

    .gauge__label {
        font-family: var(--font-header);
        font-size: 6px;
        font-style: italic;
        fill: var(--c-ink-soft);
    }

    .gauge__needle {
        transition: transform 0.18s cubic-bezier(0.3, 1.6, 0.5, 1);

        path {
            fill: var(--c-terracotta-dark);
        }
    }

    .gauge__pin {
        fill: #6E4F18;
    }

    [is-hot] .gauge {
        animation: shake 0.12s linear infinite;
    }

    .shovel {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        width: 9.6rem;
        height: 9.6rem;
        padding: 0 0 0.8rem;
        border: 3px solid #6E4F18;
        border-radius: 1.4rem;
        background: #2B2622;
        color: var(--c-paper);
        box-shadow: 2px 4px 8px rgba(8, 26, 44, 0.45);
        cursor: pointer;
        overflow: hidden;
        touch-action: manipulation;

        &:active {
            transform: scale(0.96);
        }
    }

    // The fire behind the door
    .door {
        position: absolute;
        left: 1rem;
        right: 1rem;
        top: 1rem;
        height: 4.4rem;
        border-radius: 2.2rem 2.2rem 0.4rem 0.4rem;
        background: radial-gradient(circle at 50% 90%, var(--glow), rgba(120, 30, 10, 0.9) 75%);
        box-shadow: 0 0 1.6rem var(--glow);
        transition: background 0.3s, box-shadow 0.3s;
    }

    .shovel__icon {
        position: absolute;
        left: 50%;
        top: 1.6rem;
        width: 5.2rem;
        height: 5.2rem;
        margin-left: -2.6rem;
        transform-origin: 75% 10%;

        &[swinging] {
            animation: swing 0.32s ease-out;
        }
    }

    .shovel__handle {
        stroke: #C9A26B;
        stroke-width: 3;
        stroke-linecap: round;
    }

    .shovel__blade {
        fill: #8D99A6;
        stroke: #3C444D;
        stroke-width: 1;
    }

    .shovel__coal {
        fill: #1B1B1B;
    }

    .shovel__label {
        position: relative;
        font-family: var(--font-header);
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }

    .steam {
        position: absolute;
        left: 2.4rem;
        bottom: 7rem;
        pointer-events: none;

        span {
            position: absolute;
            width: 3rem;
            height: 3rem;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.85);
            filter: blur(4px);
            animation: steam 1s ease-out infinite;

            &:nth-child(2) {
                animation-delay: 0.25s;
            }

            &:nth-child(3) {
                animation-delay: 0.5s;
            }
        }
    }

    @keyframes swing {
        0% {
            transform: rotate(0deg) translateY(0);
        }

        45% {
            transform: rotate(-28deg) translateY(-0.6rem);
        }

        100% {
            transform: rotate(0deg) translateY(0);
        }
    }

    @keyframes shake {
        0%,
        100% {
            transform: translate(0, 0);
        }

        50% {
            transform: translate(1px, -1px);
        }
    }

    @keyframes steam {
        0% {
            opacity: 0.9;
            transform: translate(0, 0) scale(0.5);
        }

        100% {
            opacity: 0;
            transform: translate(1rem, -6rem) scale(2.2);
        }
    }
</style>
