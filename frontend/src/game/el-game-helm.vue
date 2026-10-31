<script setup>
    // The ship's wheel: grab and turn it, or hold the arrow keys. Let go and it springs back to the
    // middle with a little overshoot, so the ship never stays on one heading by itself.
    import { onBeforeUnmount, onMounted, ref } from 'vue';

    // Half a turn of the wheel is full rudder
    const FULL_TURN = 180;
    const KEY_SPEED = 260;
    // Spring back: stiffness and damping, a little under critical so it swings past the middle once
    const STIFFNESS = 32;
    const DAMPING = 8;
    const SPOKES = 8;
    const KEY_DIRECTIONS = {
        ArrowLeft : -1,
        a : -1,
        A : -1,
        ArrowRight : 1,
        d : 1,
        D : 1
    };

    const emit = defineEmits(['turn']);

    const root = ref(null);
    const angle = ref(0);

    let velocity = 0;
    let frame = null;
    let last = 0;
    let grab = null;
    let keyDirection = 0;
    const keys = new Set();

    const spokes = Array.from({
        length : SPOKES
    }, (_, i) => i * 360 / SPOKES);

    function centerAngle(event) {
        const box = root.value.getBoundingClientRect();

        return Math.atan2(event.clientY - (box.top + box.height / 2), event.clientX - (box.left + box.width / 2)) * 180 / Math.PI;
    }

    function clamp(value) {
        return Math.max(-FULL_TURN, Math.min(FULL_TURN, value));
    }

    function onKey(event) {
        const direction = KEY_DIRECTIONS[event.key];

        if (!direction || event.target.closest?.('input, textarea')) {
            return;
        }

        event.preventDefault();

        if (event.type === 'keydown') {
            keys.add(event.key);
        } else {
            keys.delete(event.key);
        }

        keyDirection = Math.sign([...keys].reduce((sum, key) => sum + KEY_DIRECTIONS[key], 0));
    }

    function onPointerDown(event) {
        root.value.setPointerCapture(event.pointerId);
        grab = {
            id : event.pointerId,
            pointer : centerAngle(event),
            wheel : angle.value
        };
        velocity = 0;
    }

    function onPointerMove(event) {
        if (!grab || event.pointerId !== grab.id) {
            return;
        }

        let delta = centerAngle(event) - grab.pointer;

        // Unwrap, so a turn past the left of the wheel does not jump a full circle
        delta = ((delta + 540) % 360) - 180;
        grab.wheel = clamp(grab.wheel + delta);
        grab.pointer = centerAngle(event);
        angle.value = grab.wheel;
    }

    function onPointerUp(event) {
        if (grab && event.pointerId === grab.id) {
            grab = null;
        }
    }

    function tick(now) {
        const dt = Math.min(0.05, (now - last) / 1000 || 0);

        last = now;

        if (!grab) {
            if (keyDirection) {
                angle.value = clamp(angle.value + keyDirection * KEY_SPEED * dt);
                velocity = 0;
            } else {
                velocity += (-STIFFNESS * angle.value - DAMPING * velocity) * dt;
                angle.value += velocity * dt;

                if (Math.abs(angle.value) < 0.05 && Math.abs(velocity) < 0.05) {
                    angle.value = 0;
                    velocity = 0;
                }
            }
        }

        emit('turn', angle.value / FULL_TURN);
        frame = requestAnimationFrame(tick);
    }

    onMounted(() => {
        window.addEventListener('keydown', onKey);
        window.addEventListener('keyup', onKey);
        frame = requestAnimationFrame(tick);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKey);
        window.removeEventListener('keyup', onKey);
        cancelAnimationFrame(frame);
    });
</script>

<template>
    <div
        ref="root"
        class="el-game-helm"
        role="slider"
        aria-label="Stuurwiel"
        aria-valuemin="-1"
        aria-valuemax="1"
        v-bind:aria-valuenow="(angle / 180).toFixed(2)"
        v-on:pointerdown="onPointerDown($event)"
        v-on:pointermove="onPointerMove($event)"
        v-on:pointerup="onPointerUp($event)"
        v-on:pointercancel="onPointerUp($event)">
        <svg
            viewBox="-60 -60 120 120"
            aria-hidden="true">
            <g v-bind:transform="`rotate(${angle})`">
                <g
                    v-for="spoke in spokes"
                    v-bind:key="spoke"
                    v-bind:transform="`rotate(${spoke})`">
                    <path
                        class="handle"
                        d="M-3,-39 L-4,-50 Q-4.5,-56 0,-57 Q4.5,-56 4,-50 L3,-39 Z" />
                    <rect
                        class="spoke"
                        x="-2.2"
                        y="-40"
                        width="4.4"
                        height="30" />
                </g>
                <circle
                    class="rim"
                    r="36"
                    stroke-width="7" />
                <circle
                    class="rim-line"
                    r="36" />
                <circle
                    class="hub"
                    r="11" />
                <circle
                    class="hub-pin"
                    r="3.4" />
                <path
                    class="top-mark"
                    d="M-3,-42 L3,-42 L0,-36 Z" />
            </g>
        </svg>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-helm {
        width: 14rem;
        height: 14rem;
        touch-action: none;
        cursor: grab;
        user-select: none;
        -webkit-user-select: none;
        filter: drop-shadow(2px 4px 4px rgba(8, 26, 44, 0.45));

        &:active {
            cursor: grabbing;
        }

        svg {
            display: block;
            width: 100%;
            height: 100%;
            overflow: visible;
        }
    }

    .handle {
        fill: #9A6634;
        stroke: #5E3B1A;
        stroke-width: 1;
    }

    .spoke {
        fill: #8A5A2B;
        stroke: #5E3B1A;
        stroke-width: 0.8;
    }

    .rim {
        fill: none;
        stroke: #8A5A2B;
    }

    .rim-line {
        fill: none;
        stroke: #5E3B1A;
        stroke-width: 0.8;
        stroke-dasharray: 2 5;
    }

    .hub {
        fill: #B8862E;
        stroke: #6E4F18;
        stroke-width: 1.2;
    }

    .hub-pin {
        fill: #6E4F18;
    }

    .top-mark {
        fill: #F2DCCD;
    }
</style>
