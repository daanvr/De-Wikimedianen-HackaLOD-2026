<script setup>
    // Everything on top of the map that is not a control: the net with the score, the mission card,
    // the compass arrow, buttons for sound and help, and short messages. Catches fly into the net.
    import { computed, onBeforeUnmount, ref, watch } from 'vue';
    import ElIcon from '@/components/el-icon.vue';
    import ElExplorerIcon from '@/explorer/el-explorer-icon.vue';
    import { RARITIES } from './rarity.js';

    const emit = defineEmits(['album', 'info', 'mute', 'skip', 'toast']);

    const props = defineProps({
        score : {
            type : Number,
            required : true
        },
        collected : {
            type : Number,
            required : true
        },
        total : {
            type : Number,
            required : true
        },
        discovered : {
            type : Number,
            default : 0
        },
        mission : {
            type : Object,
            default : null
        },
        compass : {
            type : Object,
            default : null
        },
        isMuted : {
            type : Boolean,
            default : false
        },
        toasts : {
            type : Array,
            default : () => []
        }
    });

    // A new mission shows its card for a while, then folds into a small arrow with the distance
    const MISSION_OPEN_MS = 7000;

    const root = ref(null);
    const net = ref(null);
    const isBumping = ref(false);
    const isMissionOpen = ref(false);

    const scoreText = computed(() => props.score.toLocaleString('nl-NL'));
    const discoveredText = computed(() => `${Math.floor(props.discovered * 100)}%`);

    let bumpTimer = null;
    let foldTimer = null;

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

    // A dot flies from a point on the screen into the net, with the points it is worth
    function fly(from, rarity) {
        if (!net.value || !root.value) {
            return;
        }

        const origin = root.value.getBoundingClientRect();
        const box = net.value.getBoundingClientRect();
        const to = {
            x : box.left + box.width / 2 - origin.left,
            y : box.top + box.height / 2 - origin.top
        };
        const middle = {
            x : (from.x + to.x) / 2 + (Math.random() - 0.5) * 80,
            y : Math.min(from.y, to.y) - 40 - Math.random() * 40
        };
        const dot = document.createElement('span');
        const label = document.createElement('span');

        dot.className = 'flight';
        dot.style.background = RARITIES[rarity].color;
        root.value.appendChild(dot);
        dot.animate([
            {
                transform : `translate(${from.x}px, ${from.y}px) scale(1.4)`
            },
            {
                transform : `translate(${middle.x}px, ${middle.y}px) scale(2)`,
                offset : 0.45
            },
            {
                transform : `translate(${to.x}px, ${to.y}px) scale(0.6)`,
                opacity : 0.5
            }
        ], {
            duration : 700,
            easing : 'cubic-bezier(0.3, 0.6, 0.35, 1)'
        }).onfinish = () => {
            dot.remove();
            bump();
        };

        label.className = 'points';
        label.textContent = `+${RARITIES[rarity].points}`;
        label.style.color = rarity === 'common' ? '#FBF8F1' : RARITIES[rarity].color;
        label.style.left = `${from.x}px`;
        label.style.top = `${from.y}px`;
        root.value.appendChild(label);
        label.addEventListener('animationend', () => label.remove());
    }

    function openMission() {
        isMissionOpen.value = true;
        clearTimeout(foldTimer);
        foldTimer = setTimeout(() => {
            isMissionOpen.value = false;
        }, MISSION_OPEN_MS);
    }

    watch(() => props.mission?.text, (text, previous) => {
        if (text && text !== previous) {
            openMission();
        }
    }, {
        immediate : true
    });

    onBeforeUnmount(() => {
        clearTimeout(foldTimer);
        clearTimeout(bumpTimer);
    });

    defineExpose({
        fly
    });
</script>

<template>
    <div
        ref="root"
        class="el-game-hud">
        <div class="stack">
            <div class="status">
                <button
                    ref="net"
                    class="net"
                    type="button"
                    v-bind:is-bumping="isBumping ? '' : null"
                    aria-label="Open je verzameling"
                    v-on:click="emit('album')">
                    <svg
                        viewBox="0 0 40 40"
                        aria-hidden="true">
                        <path
                            class="net__hoop"
                            d="M6 10 Q20 4 34 10" />
                        <path
                            class="net__bag"
                            d="M6 10 Q8 30 20 36 Q32 30 34 10" />
                        <path
                            class="net__mesh"
                            d="M10 12 L20 34 M16 10 L22 34 M24 10 L18 34 M30 12 L20 34 M8 18 Q20 22 32 18 M10 25 Q20 29 30 25" />
                    </svg>
                    <span class="net__count">{{ collected.toLocaleString('nl-NL') }}</span>
                </button>
                <div class="numbers">
                    <strong class="score">{{ scoreText }} <span>punten</span></strong>
                    <span class="sub">{{ collected.toLocaleString('nl-NL') }} van {{ total.toLocaleString('nl-NL') }} · {{ discoveredText }} zee ontdekt</span>
                </div>
            </div>

            <div
                v-if="mission && isMissionOpen"
                class="mission">
                <img
                    v-if="mission.person.portrait"
                    class="mission__portrait"
                    v-bind:src="mission.person.portrait"
                    alt="">
                <div class="mission__body">
                    <p class="mission__who">{{ mission.person.name }} · missie</p>
                    <p class="mission__text">{{ mission.text }}</p>
                    <div class="mission__meta">
                        <span
                            class="mission__arrow"
                            v-bind:style="{ transform : `rotate(${mission.bearing}deg)` }">↑</span>
                        <span>{{ mission.inside ? 'Je bent er! Zoek binnen de stippellijn.' : `${mission.distance} km` }}</span>
                        <button
                            class="mission__skip"
                            type="button"
                            v-on:click="emit('skip')">Andere missie</button>
                        <button
                            class="mission__fold"
                            type="button"
                            aria-label="Missie inklappen"
                            v-on:click="isMissionOpen = false">▴</button>
                    </div>
                </div>
            </div>

            <button
                v-else-if="mission"
                class="mission-pill"
                type="button"
                aria-label="Missie openklappen"
                v-on:click="openMission()">
                <img
                    v-if="mission.person.portrait"
                    class="mission-pill__portrait"
                    v-bind:src="mission.person.portrait"
                    alt="">
                <span
                    class="mission-pill__arrow"
                    v-bind:style="{ transform : `rotate(${mission.bearing}deg)` }">↑</span>
                <span>{{ mission.inside ? 'Hier!' : `${mission.distance} km` }}</span>
            </button>

            <div
                v-if="compass"
                class="compass"
                role="status"
                v-bind:is-far="compass.isFar ? '' : null">
                <strong>{{ compass.isFar ? 'Uit koers!' : 'Hier is weinig te vangen.' }}</strong>
                <span>Volg de pijl naar station {{ compass.station }} · {{ compass.distance }} km</span>
            </div>
        </div>

        <div
            v-if="compass"
            class="course"
            aria-hidden="true"
            v-bind:style="{ left : `${compass.x}px`, top : `${compass.y}px`, transform : `rotate(${compass.angle}deg)` }">
            <svg
                class="course__arrow"
                viewBox="0 0 60 48">
                <path d="M4 16 H32 V4 L56 24 L32 44 V32 H4 Z" />
            </svg>
        </div>

        <div class="tools">
            <button
                class="tool"
                type="button"
                v-bind:aria-label="isMuted ? 'Geluid aan' : 'Geluid uit'"
                v-bind:title="isMuted ? 'Geluid aan' : 'Geluid uit'"
                v-on:click="emit('mute')">
                <svg
                    viewBox="0 0 24 24"
                    aria-hidden="true">
                    <path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" />
                    <path
                        v-if="!isMuted"
                        d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11" />
                    <path
                        v-else
                        d="M16 9.5l5 5M21 9.5l-5 5" />
                </svg>
            </button>
            <button
                class="tool"
                type="button"
                aria-label="Uitleg"
                title="Uitleg"
                v-on:click="emit('info')">
                <el-icon
                    name="info"
                    v-bind:size="22" />
            </button>
        </div>

        <transition-group
            name="toast"
            tag="div"
            class="toasts">
            <button
                v-for="(toast, index) in toasts"
                v-bind:key="toast.id"
                class="toast"
                type="button"
                v-bind:data-kind="toast.kind"
                v-bind:is-behind="index < toasts.length - 1 ? '' : null"
                v-bind:style="{ '--depth' : toasts.length - 1 - index }"
                v-on:click="emit('toast', toast)">
                <img
                    v-if="toast.portrait"
                    class="toast__portrait"
                    v-bind:src="toast.portrait"
                    alt="">
                <span
                    v-else
                    class="toast__icon"
                    v-bind:style="{ borderColor : toast.color }">
                    <el-explorer-icon
                        v-if="toast.group"
                        v-bind:group="toast.group"
                        v-bind:size="22" />
                    <span v-else>{{ toast.emoji ?? '★' }}</span>
                </span>
                <span class="toast__text">
                    <strong>{{ toast.title }}</strong>
                    <span>{{ toast.text }}</span>
                </span>
                <img
                    v-if="toast.photo"
                    class="toast__photo"
                    v-bind:src="toast.photo"
                    alt="">
            </button>
        </transition-group>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-hud {
        position: absolute;
        inset: 0;
        z-index: 5;
        pointer-events: none;
        overflow: hidden;

        button {
            pointer-events: auto;
        }

        :deep(.flight) {
            position: absolute;
            left: -6px;
            top: -6px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid var(--c-paper);
            box-shadow: 0 1px 3px rgba(8, 26, 44, 0.4);
        }

        :deep(.points) {
            position: absolute;
            transform: translate(-50%, -50%);
            font-family: var(--font-header);
            font-size: 2rem;
            font-weight: 700;
            text-shadow: 0 1px 3px rgba(8, 26, 44, 0.8);
            animation: points 1s ease-out forwards;
        }
    }

    // Score, mission and compass in one column, left of the buttons under the menu
    .stack {
        position: absolute;
        top: 1.6rem;
        left: 1.6rem;
        right: 7.6rem;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.8rem;
    }

    .status {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .net {
        position: relative;
        width: 5.6rem;
        height: 5.6rem;
        padding: 0.6rem;
        border: 0;
        border-radius: 50%;
        background: rgba(251, 248, 241, 0.95);
        box-shadow: var(--shadow-float);
        cursor: pointer;
        transition: transform 0.2s;

        &[is-bumping] {
            transform: scale(1.15);
        }

        svg {
            width: 100%;
            height: 100%;
        }
    }

    .net__hoop {
        fill: none;
        stroke: #8A5A2B;
        stroke-width: 2.4;
        stroke-linecap: round;
    }

    .net__bag {
        fill: rgba(216, 138, 99, 0.25);
        stroke: var(--c-marine);
        stroke-width: 1.4;
    }

    .net__mesh {
        fill: none;
        stroke: var(--c-marine);
        stroke-width: 0.7;
        opacity: 0.6;
    }

    .net__count {
        position: absolute;
        right: -0.6rem;
        bottom: -0.4rem;
        min-width: 2.4rem;
        padding: 0 0.6rem;
        border-radius: 1.2rem;
        background: var(--c-terracotta);
        color: var(--c-paper);
        font-size: 1.3rem;
        font-weight: 600;
        line-height: 2.2rem;
    }

    .numbers {
        display: flex;
        flex-direction: column;
        padding: 0.4rem 1.2rem 0.5rem;
        border-radius: 0.8rem;
        background: rgba(27, 36, 51, 0.72);
        color: var(--c-paper);
    }

    .score {
        font-family: var(--font-header);
        font-size: 2.4rem;
        line-height: 1.1;

        span {
            font-size: 1.4rem;
            font-weight: 400;
        }
    }

    .sub {
        font-size: 1.3rem;
    }

    // Under the menu button of the app
    .tools {
        position: absolute;
        top: 7.6rem;
        right: 2rem;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }

    .tool {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 4.4rem;
        height: 4.4rem;
        padding: 0;
        border: 0;
        border-radius: 50%;
        background: rgba(251, 248, 241, 0.94);
        color: var(--c-ink);
        box-shadow: 0 1px 4px rgba(8, 26, 44, 0.3);
        cursor: pointer;

        svg {
            width: 2.2rem;
            height: 2.2rem;
            fill: none;
            stroke: currentColor;
            stroke-width: 1.7;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
    }

    .mission {
        display: flex;
        gap: 1rem;
        width: min(34rem, 100%);
        padding: 1rem 1.2rem;
        border-radius: 0.8rem;
        background: rgba(251, 248, 241, 0.95);
        box-shadow: var(--shadow-float);
        font-size: 1.4rem;
        line-height: 1.35;
        animation: drop 0.3s ease-out;
    }

    .mission__portrait {
        flex: none;
        width: 4.4rem;
        height: 4.4rem;
        border-radius: 50%;
        object-fit: cover;
        filter: sepia(0.25);
    }

    .mission__body {
        min-width: 0;

        p {
            margin: 0;
        }
    }

    .mission__who {
        font-size: 1.2rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--c-terracotta);
    }

    .mission__meta {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-top: 0.4rem;
        color: var(--c-ink-soft);
    }

    .mission__arrow {
        display: inline-block;
        font-weight: 700;
        color: var(--c-terracotta);
    }

    .mission__fold {
        padding: 0.2rem 0.8rem;
        border: 0;
        background: none;
        font: inherit;
        color: var(--c-ink-soft);
        cursor: pointer;
    }

    .mission-pill {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.3rem 1.2rem 0.3rem 0.3rem;
        border: 0;
        border-radius: 2.4rem;
        background: rgba(251, 248, 241, 0.95);
        box-shadow: var(--shadow-float);
        color: var(--c-ink);
        font: inherit;
        font-size: 1.5rem;
        font-weight: 600;
        cursor: pointer;
        animation: appear 0.3s ease-out;
    }

    .mission-pill__portrait {
        width: 3.6rem;
        height: 3.6rem;
        border-radius: 50%;
        object-fit: cover;
        filter: sepia(0.25);
    }

    .mission-pill__arrow {
        display: inline-block;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1;
        color: var(--c-terracotta);
        transition: transform 0.4s ease-out;
    }

    .mission__skip {
        margin-left: auto;
        padding: 0.2rem 0.6rem;
        border: 1px solid var(--c-frame);
        border-radius: 0.4rem;
        background: none;
        font: inherit;
        font-size: 1.2rem;
        color: var(--c-ink-soft);
        cursor: pointer;
    }

    // Off course: a clear bar under the mission, and the big arrow around the ship below
    .compass {
        display: flex;
        flex-direction: column;
        padding: 0.6rem 1.4rem 0.7rem;
        border-radius: 0.8rem;
        background: rgba(27, 36, 51, 0.88);
        box-shadow: var(--shadow-float);
        color: var(--c-paper);
        font-size: 1.4rem;
        line-height: 1.3;
        animation: appear 0.3s ease-out;

        strong {
            font-family: var(--font-header);
            font-size: 1.8rem;
        }

        &[is-far] {
            background: var(--c-terracotta);
            animation: appear 0.3s ease-out, glow 1.6s ease-in-out infinite;
        }
    }

    // A point at the ship that turns towards the station; the arrow sits on a circle around the ship
    .course {
        position: absolute;
        width: 0;
        height: 0;
        transition: transform 0.35s ease-out;
    }

    .course__arrow {
        position: absolute;
        left: 6.4rem;
        top: -2.8rem;
        width: 7rem;
        height: 5.6rem;
        overflow: visible;
        filter: drop-shadow(0 2px 4px rgba(8, 26, 44, 0.5));
        animation: nudge 1s ease-in-out infinite;

        path {
            fill: var(--c-terracotta);
            stroke: var(--c-paper);
            stroke-width: 3;
            stroke-linejoin: round;
        }
    }

    // A small pile: the newest message on top, the older ones peek out behind it
    .toasts {
        position: absolute;
        left: 50%;
        bottom: 18rem;
        display: grid;
        align-items: end;
        width: min(34rem, calc(100% - 3.2rem));
        transform: translateX(-50%);
    }

    .toast {
        grid-area: 1 / 1;
        z-index: calc(10 - var(--depth));
        display: flex;
        align-items: center;
        gap: 1rem;
        width: 100%;
        padding: 0.8rem 1.2rem;
        border: 0;
        border-radius: 0.8rem;
        background: rgba(251, 248, 241, 0.98);
        box-shadow: var(--shadow-float);
        color: var(--c-ink);
        font: inherit;
        font-size: 1.4rem;
        line-height: 1.3;
        text-align: left;
        cursor: pointer;
        transform: translateY(calc(var(--depth) * -0.9rem)) scale(calc(1 - var(--depth) * 0.06));
        transform-origin: 50% 0;
        transition: transform 0.3s ease-out, filter 0.3s;

        &[data-kind="achievement"] {
            background: #F6E7C1;
        }

        &[is-behind] {
            filter: brightness(0.9);
            pointer-events: none;
        }
    }

    .toast__icon {
        flex: none;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 3.6rem;
        height: 3.6rem;
        border: 3px solid #B8862E;
        border-radius: 50%;
        background: var(--c-paper);
        color: var(--c-marine);
        font-size: 1.8rem;
    }

    .toast__portrait {
        flex: none;
        width: 4.4rem;
        height: 4.4rem;
        border: 2px solid var(--c-paper);
        border-radius: 50%;
        object-fit: cover;
        filter: sepia(0.25);
        box-shadow: 0 1px 3px rgba(8, 26, 44, 0.35);
    }

    .toast__photo {
        flex: none;
        width: 5.6rem;
        height: 5.6rem;
        border-radius: 0.4rem;
        object-fit: cover;
        filter: sepia(0.15);
    }

    .toast__text {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;

        strong {
            font-family: var(--font-header);
        }
    }

    .toast-enter-active,
    .toast-leave-active {
        transition: opacity 0.3s, transform 0.3s;
    }

    .toast-enter-from,
    .toast-leave-to {
        opacity: 0;
        transform: translateY(1rem);
    }

    @keyframes points {
        0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.6);
        }

        20% {
            opacity: 1;
            transform: translate(-50%, -110%) scale(1.2);
        }

        100% {
            opacity: 0;
            transform: translate(-50%, -260%) scale(1);
        }
    }

    @keyframes drop {
        from {
            opacity: 0;
            transform: translateY(-0.8rem);
        }
    }

    @keyframes nudge {
        0%,
        100% {
            transform: translateX(0);
        }

        50% {
            transform: translateX(1.2rem);
        }
    }

    @keyframes glow {
        0%,
        100% {
            box-shadow: var(--shadow-float), 0 0 0 0 rgba(216, 138, 99, 0.7);
        }

        50% {
            box-shadow: var(--shadow-float), 0 0 0 0.8rem rgba(216, 138, 99, 0);
        }
    }

    @keyframes appear {
        from {
            opacity: 0;
        }
    }
</style>
