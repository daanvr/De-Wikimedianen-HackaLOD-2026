<script setup>
    import { computed, inject, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElIcon from '@/components/el-icon.vue';
    import ElMenu from '@/components/el-menu.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { mediaUrl } from '@/services/data.js';
    import { formatDate } from '@/services/format.js';

    const TYPE_ORDER = ['person', 'specimen', 'media', 'item', 'article', 'location', 'expedition', 'other'];
    const TYPE_ICONS = {
        person : 'person',
        specimen : 'specimen',
        media : 'image',
        location : 'location',
        item : 'item',
        article : 'book',
        expedition : 'anchor',
        other : 'info',
        station : 'station'
    };
    const STATION_LIMIT = 60;

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const query = ref('');
    const filter = ref(route.query.type ?? 'all');

    const types = computed(() => {
        const present = store.contentTypes;

        return TYPE_ORDER.filter((type) => present.includes(type))
            .concat(present.filter((type) => !TYPE_ORDER.includes(type)));
    });

    const chips = computed(() => [
        {
            id : 'all',
            label : t('filter_all')
        },
        ...types.value.map((type) => ({
            id : type,
            label : t('content_type_' + type)
        })),
        {
            id : 'station',
            label : t('content_type_station')
        }
    ]);

    function matches(text) {
        const needle = query.value.trim().toLowerCase();

        return !needle || text.toLowerCase().includes(needle);
    }

    const groups = computed(() => {
        const result = [];

        for (const type of types.value) {
            if (filter.value !== 'all' && filter.value !== type) {
                continue;
            }

            const items = store.recordList
                .filter((record) => (record.contentType || 'other') === type)
                .filter((record) => matches([record.label, record.title, record.description].filter(Boolean).join(' ')))
                .sort((a, b) => (a.label || a.title).localeCompare(b.label || b.title, 'nl'))
                .map((record) => ({
                    key : record.id,
                    to : `/records/${record.id}`,
                    name : record.label || record.title,
                    description : record.description,
                    image : record.image ? mediaUrl(record.image.src) : null,
                    isSpecimen : type === 'specimen'
                }));

            if (items.length) {
                result.push({
                    type,
                    label : t('content_type_' + type),
                    items
                });
            }
        }

        if (filter.value === 'all' || filter.value === 'station') {
            const stations = store.stations
                .filter((feature) => matches([
                    `${t('station')} ${feature.properties.station}`,
                    feature.properties.remarks ?? '',
                    feature.properties.bottom ?? ''
                ].join(' ')));
            const limit = filter.value === 'station' ? stations.length : STATION_LIMIT;

            if (stations.length) {
                result.push({
                    type : 'station',
                    label : t('content_type_station'),
                    more : Math.max(0, stations.length - limit),
                    items : stations.slice(0, limit).map((feature) => ({
                        key : 'station-' + feature.properties.station,
                        to : {
                            path : '/map',
                            query : {
                                station : feature.properties.station
                            }
                        },
                        name : `${t('station')} ${feature.properties.station}`,
                        description : [formatDate(feature.properties.start_date), feature.properties.depth_m ? `${feature.properties.depth_m} m` : null].filter(Boolean).join(' · '),
                        image : null,
                        isSpecimen : false
                    }))
                });
            }
        }

        return result;
    });

    function pick(id) {
        filter.value = id;
        router.replace({
            query : id === 'all' ? {} : {
                type : id
            }
        });
    }

    watch(() => route.query.type, (type) => {
        filter.value = type ?? 'all';
    });

    onMounted(() => {
        store.setMap({
            sheet : 'full'
        });
    });
</script>

<template>
    <div class="vw-library">
        <el-sheet
            state="full"
            v-bind:states="['full']">
            <div class="bar">
                <button
                    type="button"
                    class="back-link"
                    v-on:click="router.back()">
                    <el-icon
                        name="arrowLeft"
                        v-bind:size="18" />
                    {{ t('back') }}
                </button>

                <el-menu
                    v-bind:mode="store.map.mode === 'explore' ? 'explore' : 'story'"
                    v-bind:floating="false" />
            </div>

            <h1 class="title">{{ t('library') }}</h1>

            <label
                for="library-search"
                class="kicker search-label">{{ t('library_search') }}</label>
            <div class="search">
                <el-icon
                    name="search"
                    v-bind:size="18" />
                <input
                    id="library-search"
                    v-model="query"
                    type="search"
                    v-bind:placeholder="t('library_search_placeholder')">
            </div>

            <div class="chips">
                <button
                    v-for="chip in chips"
                    v-bind:key="chip.id"
                    type="button"
                    class="chip"
                    v-bind:aria-pressed="filter === chip.id ? 'true' : 'false'"
                    v-bind:is-active="filter === chip.id ? '' : null"
                    v-on:click="pick(chip.id)">
                    {{ chip.label }}
                </button>
            </div>

            <p
                v-if="!groups.length"
                class="empty">
                {{ t('library_empty') }}
            </p>

            <section
                v-for="group in groups"
                v-bind:key="group.type"
                class="group">
                <h2 class="group__title">
                    <el-icon
                        v-bind:name="TYPE_ICONS[group.type] ?? 'info'"
                        v-bind:size="18" />
                    {{ group.label }}
                    <span class="group__count">{{ group.items.length + (group.more ?? 0) }}</span>
                </h2>

                <router-link
                    v-for="item in group.items"
                    v-bind:key="item.key"
                    class="row"
                    v-bind:to="item.to">
                    <span
                        class="thumb"
                        v-bind:has-image="item.image ? '' : null">
                        <img
                            v-if="item.image"
                            v-bind:src="item.image"
                            alt=""
                            loading="lazy">
                        <el-icon
                            v-else
                            v-bind:name="TYPE_ICONS[group.type] ?? 'info'"
                            v-bind:size="22" />
                    </span>
                    <span class="row__text">
                        <span
                            class="row__name"
                            v-bind:is-specimen="item.isSpecimen ? '' : null">{{ item.name }}</span>
                        <span
                            v-if="item.description"
                            class="row__description">{{ item.description }}</span>
                    </span>
                    <el-icon
                        class="row__chevron"
                        name="chevronRight"
                        v-bind:size="18" />
                </router-link>

                <button
                    v-if="group.more"
                    type="button"
                    class="more"
                    v-on:click="pick(group.type)">
                    + {{ group.more }}
                </button>
            </section>
        </el-sheet>
    </div>
</template>

<style lang="scss" scoped>
    .vw-library {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    .bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;
    }

    .title {
        margin: 0.8rem 0 1.2rem;
        padding-top: 1.2rem;
        border-top: 1px solid var(--c-ink);
        font-weight: 700;
        font-size: 3.2rem;
        line-height: 1.06;
    }

    .search-label {
        display: block;
        margin-bottom: 0.6rem;
    }

    .search {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        height: 4.8rem;
        padding: 0 1.2rem;
        border: 1px solid var(--c-ink);
        background: #FFFFFF;
        border-radius: 3px;
        color: var(--c-ink-soft);

        input {
            flex: 1;
            min-width: 0;
            border: 0;
            outline: none;
            background: transparent;
            font-size: 1.7rem;
            color: var(--c-ink);
        }

        &:focus-within {
            outline: 3px solid var(--c-terracotta-light);
            outline-offset: 2px;
        }
    }

    // One row of types that scrolls sideways
    .chips {
        display: flex;
        flex-wrap: nowrap;
        gap: 0.8rem;
        margin: 1.4rem calc(-1 * var(--gutter)) 0.6rem;
        padding: 0 var(--gutter) 0.6rem;
        overflow-x: auto;
        scrollbar-width: none;

        &::-webkit-scrollbar {
            display: none;
        }
    }

    .chip {
        flex-shrink: 0;
        white-space: nowrap;
        min-height: 3.6rem;
        padding: 0 1.4rem;
        border: 1px solid var(--c-marine);
        border-radius: 999px;
        background: transparent;
        color: var(--c-marine);
        font-family: var(--font-header);
        font-size: 1.3rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;

        &[is-active] {
            background: var(--c-terracotta);
            border-color: var(--c-terracotta);
            color: var(--c-paper);
        }
    }

    .empty {
        margin-top: 2.2rem;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .group {
        margin-top: 2rem;
    }

    .group__title {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.4rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--c-ink);
        font-weight: 400;
        font-size: 1.3rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #3A4254;

        .el-icon {
            color: var(--c-marine);
        }
    }

    .group__count {
        margin-left: auto;
        letter-spacing: 0;
        color: var(--c-ink-soft);
    }

    .row {
        display: flex;
        align-items: center;
        gap: 1.4rem;
        padding: 1rem 0;
        border-bottom: 1px solid var(--c-rule);
        text-decoration: none;
        color: var(--c-ink);

        &:hover {
            color: var(--c-ink);
            background: var(--c-plate);
        }
    }

    .thumb {
        width: 5.6rem;
        height: 5.6rem;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border: 1px solid var(--c-frame);
        background: var(--c-plate);
        color: var(--c-marine);

        img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
    }

    .row__text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }

    .row__name {
        font-family: var(--font-header);
        font-weight: 700;
        font-size: 1.8rem;
        line-height: 1.2;

        &[is-specimen] {
            font-style: italic;
        }
    }

    .row__description {
        font-size: 1.5rem;
        color: var(--c-ink-soft);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .row__chevron {
        color: var(--c-link);
    }

    .more {
        min-height: 4.4rem;
        color: var(--c-link);
        font-size: 1.6rem;
    }
</style>
