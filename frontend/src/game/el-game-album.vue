<script setup>
    // The collection of the game: specimens per group, the stations you passed as stamps in a log,
    // and the badges. A collected specimen opens the specimen page of the explore mode, with a note
    // that its place in the game is made up and where it was really collected.
    import { computed, ref, watch } from 'vue';
    import { formatDate } from '@/services/format.js';
    import ElExplorerBadge from '@/explorer/el-explorer-badge.vue';
    import ElExplorerIcon from '@/explorer/el-explorer-icon.vue';
    import ElExplorerSpecimen from '@/explorer/el-explorer-specimen.vue';
    import { groupName } from '@/explorer/groups.js';
    import { RARITIES, RARITY_ORDER } from './rarity.js';

    // Empty places shown per group, as a hint of how much there is still to find
    const EMPTY_TILES = 12;

    const emit = defineEmits(['close', 'seek']);

    const props = defineProps({
        specimens : {
            type : Array,
            required : true
        },
        // Id of a specimen to time it was caught
        collected : {
            type : Object,
            required : true
        },
        visited : {
            type : Array,
            required : true
        },
        achievements : {
            type : Array,
            required : true
        },
        focus : {
            type : Number,
            default : null
        }
    });

    const tab = ref('specimens');
    const openGroup = ref(null);
    const rarityFilter = ref(null);
    const selected = ref(null);

    const groups = computed(() => {
        const byGroup = new Map();

        for (const specimen of props.specimens) {
            if (!byGroup.has(specimen.group)) {
                byGroup.set(specimen.group, {
                    group : specimen.group,
                    name : groupName(specimen.group),
                    total : 0,
                    caught : []
                });
            }

            const entry = byGroup.get(specimen.group);

            entry.total++;

            if (props.collected[specimen.id] && (!rarityFilter.value || specimen.rarity === rarityFilter.value)) {
                entry.caught.push(specimen);
            }
        }

        return [...byGroup.values()]
            .map((entry) => ({
                ...entry,
                caught : entry.caught.sort((a, b) => RARITY_ORDER.indexOf(b.rarity) - RARITY_ORDER.indexOf(a.rarity) || props.collected[b.id] - props.collected[a.id])
            }))
            .sort((a, b) => b.caught.length - a.caught.length || a.name.localeCompare(b.name, 'nl'));
    });

    const rarityCounts = computed(() => {
        const counts = Object.fromEntries(RARITY_ORDER.map((rarity) => [rarity, 0]));

        for (const specimen of props.specimens) {
            if (props.collected[specimen.id]) {
                counts[specimen.rarity]++;
            }
        }

        return counts;
    });

    const realPlace = computed(() => {
        const specimen = selected.value;

        if (!specimen) {
            return '';
        }

        const date = specimen.date ? `op ${formatDate(specimen.date)}` : 'op een onbekende dag';

        if (specimen.station) {
            return `${date} bij station ${specimen.station.nummer}`;
        }

        return specimen.locality ? `${date}, vindplaats volgens het record: “${specimen.locality}”` : date;
    });

    function caughtAt(specimen) {
        return new Date(props.collected[specimen.id]).toLocaleString('nl-NL', {
            day : 'numeric',
            month : 'long',
            hour : '2-digit',
            minute : '2-digit'
        });
    }

    function toggleGroup(group) {
        openGroup.value = openGroup.value === group ? null : group;
    }

    function toggleRarity(rarity) {
        rarityFilter.value = rarityFilter.value === rarity ? null : rarity;
    }

    watch(() => props.focus, (id) => {
        const specimen = props.specimens.find((item) => item.id === id);

        if (specimen) {
            tab.value = 'specimens';
            openGroup.value = specimen.group;
            selected.value = specimen;
        }
    }, {
        immediate : true
    });
</script>

<template>
    <div class="el-game-album">
        <header class="head">
            <h2 class="title">Mijn verzameling</h2>
            <button
                class="close"
                type="button"
                aria-label="Terug naar zee"
                v-on:click="emit('close')">Terug naar zee</button>
        </header>

        <nav
            class="tabs"
            role="tablist">
            <button
                v-for="[key, label] in [['specimens', 'Specimens'], ['logbook', 'Logboek'], ['badges', 'Insignes']]"
                v-bind:key="key"
                class="tab"
                type="button"
                role="tab"
                v-bind:aria-selected="tab === key ? 'true' : 'false'"
                v-on:click="tab = key">{{ label }}</button>
        </nav>

        <div class="body">
            <template v-if="tab === 'specimens'">
                <div class="rarities">
                    <button
                        v-for="rarity in RARITY_ORDER"
                        v-bind:key="rarity"
                        class="rarity"
                        type="button"
                        v-bind:is-active="rarityFilter === rarity ? '' : null"
                        v-bind:style="{ '--ring' : RARITIES[rarity].color }"
                        v-on:click="toggleRarity(rarity)">
                        <span class="rarity__dot"></span>
                        {{ RARITIES[rarity].label }}
                        <strong>{{ rarityCounts[rarity] }}</strong>
                        <small>· {{ RARITIES[rarity].points }} pt</small>
                    </button>
                </div>

                <section
                    v-for="entry in groups"
                    v-bind:key="entry.group"
                    class="group"
                    v-bind:is-open="openGroup === entry.group ? '' : null">
                    <button
                        class="group__head"
                        type="button"
                        v-on:click="toggleGroup(entry.group)">
                        <el-explorer-icon
                            class="group__icon"
                            v-bind:group="entry.group"
                            v-bind:size="26" />
                        <span class="group__name">{{ entry.name }}</span>
                        <span class="group__count">{{ entry.caught.length.toLocaleString('nl-NL') }} / {{ entry.total.toLocaleString('nl-NL') }}</span>
                        <span class="group__bar">
                            <span v-bind:style="{ width : `${Math.max(entry.caught.length ? 2 : 0, entry.caught.length / entry.total * 100)}%` }"></span>
                        </span>
                    </button>

                    <div
                        v-if="openGroup === entry.group"
                        class="tiles">
                        <button
                            v-for="specimen in entry.caught"
                            v-bind:key="specimen.id"
                            class="tile"
                            type="button"
                            v-bind:style="{ '--ring' : RARITIES[specimen.rarity].color }"
                            v-bind:data-rarity="specimen.rarity"
                            v-bind:title="specimen.name"
                            v-on:click="selected = specimen">
                            <img
                                v-if="specimen.image"
                                v-bind:src="specimen.image.src"
                                alt=""
                                loading="lazy">
                            <el-explorer-icon
                                v-else
                                v-bind:group="specimen.group"
                                v-bind:size="30" />
                            <el-explorer-badge
                                v-if="specimen.isNameBearer"
                                class="tile__badge"
                                v-bind:size="18" />
                            <span class="tile__name">{{ specimen.name }}</span>
                        </button>
                        <span
                            v-for="n in Math.min(EMPTY_TILES, entry.total - entry.caught.length)"
                            v-bind:key="`empty-${n}`"
                            class="tile tile--empty"
                            aria-hidden="true">?</span>
                        <p class="tiles__more">
                            <span v-if="entry.total > entry.caught.length">Nog {{ (entry.total - entry.caught.length).toLocaleString('nl-NL') }} te vinden.</span>
                            <span v-else>Alles gevonden!</span>
                            <button
                                v-if="entry.total > entry.caught.length"
                                class="seek"
                                type="button"
                                v-on:click="emit('seek', entry.group)">Zoek er een</button>
                        </p>
                    </div>
                </section>
            </template>

            <template v-else-if="tab === 'logbook'">
                <p
                    v-if="!visited.length"
                    class="empty">Nog geen stations bezocht. Vaar langs een boei op de kaart: daar werkte de Siboga in 1899 en 1900.</p>
                <ol
                    v-else
                    class="log">
                    <li
                        v-for="station in visited"
                        v-bind:key="station.nummer"
                        class="stamp">
                        <span class="stamp__seal">
                            <small>Station</small>
                            <strong>{{ station.nummer }}</strong>
                        </span>
                        <span class="stamp__text">
                            <strong>{{ formatDate(station.datum) }}</strong>
                            <span v-if="station.werkzaamheden">{{ station.werkzaamheden }}</span>
                            <span
                                v-if="station.diepte_m"
                                class="stamp__depth">Diepte {{ station.diepte_m.toLocaleString('nl-NL') }} m{{ station.bodem ? ` · ${station.bodem}` : '' }}</span>
                        </span>
                        <img
                            v-if="station.photo"
                            class="stamp__photo"
                            v-bind:src="station.photo.thumb"
                            v-bind:alt="station.photo.caption">
                    </li>
                </ol>
            </template>

            <div
                v-else
                class="badges">
                <div
                    v-for="achievement in achievements"
                    v-bind:key="achievement.id"
                    class="medal"
                    v-bind:is-earned="achievement.earned ? '' : null">
                    <span class="medal__coin">{{ achievement.earned ? '★' : '?' }}</span>
                    <strong>{{ achievement.title }}</strong>
                    <span>{{ achievement.text }}</span>
                </div>
            </div>
        </div>

        <div
            v-if="selected"
            class="detail">
            <p class="detail__note">
                In het spel ving je dit specimen op {{ caughtAt(selected) }}. Die plek is verzonnen. Echt verzameld {{ realPlace }}.
            </p>
            <div class="detail__page">
                <el-explorer-specimen
                    v-bind:specimen="selected"
                    v-on:close="selected = null" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-album {
        position: absolute;
        inset: 0;
        z-index: 15;
        display: flex;
        flex-direction: column;
        background: var(--c-paper);
        animation: rise 0.25s ease-out;
    }

    .head {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.6rem 8rem 0.8rem 1.6rem;
    }

    .title {
        flex: 1;
        margin: 0;
        font-family: var(--font-header);
        font-size: 2.6rem;
        color: var(--c-marine);
    }

    .close {
        padding: 0.6rem 1.2rem;
        border: 1px solid var(--c-marine);
        border-radius: 2rem;
        background: none;
        color: var(--c-marine);
        font: inherit;
        font-size: 1.4rem;
        cursor: pointer;
    }

    .tabs {
        display: flex;
        gap: 0.4rem;
        padding: 0 1.6rem;
        border-bottom: 1px solid var(--c-rule);
    }

    .tab {
        padding: 0.8rem 1.2rem;
        border: 0;
        border-bottom: 3px solid transparent;
        background: none;
        color: var(--c-ink-soft);
        font: inherit;
        font-size: 1.6rem;
        cursor: pointer;

        &[aria-selected="true"] {
            border-bottom-color: var(--c-terracotta);
            color: var(--c-ink);
            font-weight: 600;
        }
    }

    .body {
        flex: 1;
        overflow-y: auto;
        padding: 1.2rem 1.6rem 4rem;
        font-size: 1.5rem;
    }

    .rarities {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-bottom: 1.2rem;
    }

    .rarity {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1rem;
        border: 1px solid var(--c-frame);
        border-radius: 2rem;
        background: none;
        font: inherit;
        font-size: 1.4rem;
        cursor: pointer;

        &[is-active] {
            border-color: var(--c-ink);
            background: var(--c-plate);
        }

        small {
            color: var(--c-ink-soft);
        }
    }

    .rarity__dot {
        width: 1.2rem;
        height: 1.2rem;
        border: 3px solid var(--ring);
        border-radius: 50%;
        background: var(--c-paper);
        box-shadow: 0 0 0 1px rgba(27, 36, 51, 0.3);
    }

    .group {
        border-bottom: 1px solid var(--c-rule);
    }

    .group__head {
        display: grid;
        grid-template-columns: auto 1fr auto;
        align-items: center;
        gap: 0.4rem 1rem;
        width: 100%;
        padding: 1rem 0;
        border: 0;
        background: none;
        color: var(--c-ink);
        font: inherit;
        text-align: left;
        cursor: pointer;
    }

    .group__icon {
        grid-row: span 2;
        color: var(--c-marine);
    }

    .group__count {
        color: var(--c-ink-soft);
        font-variant-numeric: tabular-nums;
    }

    .group__bar {
        grid-column: 2 / span 2;
        height: 0.5rem;
        border-radius: 0.3rem;
        background: var(--c-plate);
        overflow: hidden;

        span {
            display: block;
            height: 100%;
            background: var(--c-terracotta-light);
        }
    }

    .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(8.4rem, 1fr));
        gap: 0.8rem;
        padding: 0.4rem 0 1.4rem;
    }

    .tile {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        aspect-ratio: 1;
        padding: 0.4rem;
        border: 3px solid var(--ring);
        border-radius: 0.8rem;
        background: var(--c-plate);
        color: var(--c-marine);
        font: inherit;
        cursor: pointer;
        overflow: hidden;

        &[data-rarity="common"] {
            border: 1px solid var(--c-frame);
        }

        img {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
    }

    .tile--empty {
        border: 1px dashed var(--c-frame);
        background: none;
        color: var(--c-frame);
        font-family: var(--font-header);
        font-size: 2.4rem;
        cursor: default;
    }

    .tile__badge {
        position: absolute;
        top: 0.3rem;
        right: 0.3rem;
    }

    .tile__name {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 0.2rem 0.4rem;
        background: rgba(251, 248, 241, 0.9);
        color: var(--c-ink);
        font-size: 1.05rem;
        font-style: italic;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tiles__more {
        grid-column: 1 / -1;
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 0;
        color: var(--c-ink-soft);
    }

    .seek {
        padding: 0.4rem 1rem;
        border: 0;
        border-radius: 2rem;
        background: var(--c-terracotta);
        color: var(--c-paper);
        font: inherit;
        font-size: 1.4rem;
        cursor: pointer;
    }

    .empty {
        color: var(--c-ink-soft);
    }

    .log {
        margin: 0;
        padding: 0;
        list-style: none;
    }

    .stamp {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        padding: 1rem 0;
        border-bottom: 1px solid var(--c-rule);
    }

    .stamp__seal {
        flex: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 6.4rem;
        height: 6.4rem;
        border: 2px solid var(--c-terracotta);
        border-radius: 50%;
        color: var(--c-terracotta);
        font-family: var(--font-header);
        line-height: 1;
        transform: rotate(-8deg);
        box-shadow: inset 0 0 0 3px var(--c-paper), inset 0 0 0 4px var(--c-terracotta-light);

        small {
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        strong {
            font-size: 2rem;
        }
    }

    .stamp__text {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        font-size: 1.4rem;
    }

    .stamp__depth {
        color: var(--c-ink-soft);
    }

    .stamp__photo {
        flex: none;
        width: 6.4rem;
        height: 6.4rem;
        border-radius: 0.4rem;
        object-fit: cover;
        filter: sepia(0.2);
    }

    .badges {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
        gap: 1rem;
    }

    .medal {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.4rem;
        padding: 1.2rem 0.8rem;
        border-radius: 0.8rem;
        background: var(--c-plate);
        color: var(--c-ink-soft);
        text-align: center;
        font-size: 1.3rem;
        opacity: 0.6;

        strong {
            color: var(--c-ink);
            font-family: var(--font-header);
            font-size: 1.5rem;
        }

        &[is-earned] {
            opacity: 1;
        }
    }

    .medal__coin {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 5.2rem;
        height: 5.2rem;
        border-radius: 50%;
        background: #C9C1AE;
        color: var(--c-paper);
        font-size: 2.4rem;

        [is-earned] & {
            background: radial-gradient(circle at 35% 30%, #F1D58A, #B8862E 60%, #8A6420);
            box-shadow: 0 2px 4px rgba(8, 26, 44, 0.3);
        }
    }

    .detail {
        position: absolute;
        inset: 0;
        z-index: 2;
        display: flex;
        flex-direction: column;
        background: var(--c-scrim);
    }

    .detail__note {
        margin: 0;
        padding: 1.2rem 8rem 1.2rem 1.6rem;
        background: var(--c-terracotta-soft);
        font-size: 1.4rem;
        line-height: 1.4;
    }

    .detail__page {
        position: relative;
        flex: 1;
    }

    @keyframes rise {
        from {
            opacity: 0;
            transform: translateY(2rem);
        }
    }
</style>
