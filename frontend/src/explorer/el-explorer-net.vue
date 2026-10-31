<script setup>
    import { computed } from 'vue';
    import { formatDate } from '@/services/format.js';
    import ElIcon from '@/components/el-icon.vue';
    import ElExplorerBadge from './el-explorer-badge.vue';
    import ElExplorerIcon from './el-explorer-icon.vue';
    import ElExplorerLikeness from './el-explorer-likeness.vue';

    const emit = defineEmits(['close', 'select-specimen', 'select-station']);

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
        total : {
            type : Number,
            default : 0
        }
    });

    // Stations passed so far that yielded specimens, the latest first
    const catches = computed(() => props.stations
        .filter((station) => station.km <= props.position + 0.01 && station.specimens.length)
        .reverse());

    const count = computed(() => catches.value.reduce((sum, station) => sum + station.specimens.length, 0));
</script>

<template>
    <section
        class="el-explorer-net"
        aria-label="Het netje">
        <header class="head">
            <div class="head__text">
                <h2 class="title">Het netje: {{ count }}</h2>
                <p class="meta">van de {{ total }} specimens met een zeker station</p>
            </div>

            <button
                type="button"
                class="close"
                aria-label="Netje sluiten"
                v-on:click="emit('close')">
                <el-icon
                    name="close"
                    v-bind:size="20" />
            </button>
        </header>

        <div class="list">
            <p
                v-if="!catches.length"
                class="empty">Nog niets gevangen. Sleep de tijdlijn om te varen.</p>

            <section
                v-for="station in catches"
                v-bind:key="station.index"
                class="catch">
                <button
                    type="button"
                    class="catch__head"
                    v-on:click="emit('select-station', station)">
                    <span class="catch__station">Station {{ station.nummer }}</span>
                    <span class="catch__date">{{ formatDate(station.datum) }}</span>
                </button>

                <div class="grid">
                    <button
                        v-for="specimen in station.specimens"
                        v-bind:key="specimen.id"
                        type="button"
                        class="tile"
                        v-on:click="emit('select-specimen', specimen)">
                        <span class="tile__icon">
                            <img
                                v-if="specimen.thumb"
                                alt=""
                                loading="lazy"
                                v-bind:src="specimen.thumb">
                            <el-explorer-icon
                                v-else
                                v-bind:group="specimen.group"
                                v-bind:size="32" />
                            <el-explorer-badge
                                v-if="specimen.isNameBearer"
                                class="tile__badge"
                                v-bind:size="22" />
                            <el-explorer-likeness
                                v-if="specimen.illustration"
                                class="tile__likeness"
                                v-bind:illustration="specimen.illustration" />
                        </span>
                        <em class="tile__name">{{ specimen.name }}</em>
                    </button>
                </div>
            </section>
        </div>
    </section>
</template>

<style lang="scss" scoped>
    .el-explorer-net {
        position: absolute;
        inset: 0;
        z-index: 7;
        display: flex;
        flex-direction: column;
        background: var(--c-paper);
        animation: rise 0.4s cubic-bezier(0.2, 0.7, 0.2, 1) backwards;

        @media (min-width: 900px) {
            left: auto;
            top: 1.2rem;
            right: 1.2rem;
            bottom: 1.2rem;
            width: var(--sheet-width);
            border-radius: 12px;
            box-shadow: var(--shadow-card);
        }
    }

    .head {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        padding: 1.4rem 1.2rem 1.2rem 1.8rem;
        border-bottom: 1px solid var(--c-rule);
    }

    .head__text {
        flex: 1;
    }

    .title {
        margin: 0;
        font-weight: 400;
        font-size: 2.6rem;
    }

    .meta {
        margin: 0;
        font-size: 1.4rem;
        color: var(--c-ink-soft);
    }

    .close {
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

    .list {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        padding: 1.2rem 1.8rem 3.2rem;
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    .empty {
        margin: 2rem 0;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .catch {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }

    .catch__head {
        display: flex;
        align-items: baseline;
        gap: 0.8rem;
        min-height: 4.4rem;
        padding: 0;
        border: 0;
        background: transparent;
        text-align: left;
        cursor: pointer;
    }

    .catch__station {
        font-size: 1.8rem;
    }

    .catch__date {
        font-size: 1.4rem;
        color: var(--c-ink-soft);
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
    }

    .tile {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        padding: 0;
        border: 0;
        background: transparent;
        text-align: left;
        cursor: pointer;
    }

    .tile__icon {
        position: relative;
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        background: var(--c-plate);
        color: var(--c-ink-soft);
    }

    .tile__icon img {
        width: 100%;
        height: 100%;
        border-radius: 6px;
        object-fit: cover;
    }

    .tile__badge {
        position: absolute;
        top: 0.4rem;
        right: 0.4rem;
    }

    .tile__likeness {
        position: absolute;
        left: 0.4rem;
        bottom: 0.4rem;
    }

    .tile__name {
        font-size: 1.3rem;
        line-height: 1.25;
    }

    @keyframes rise {
        from {
            transform: translateY(6rem);
            opacity: 0;
        }
    }
</style>
