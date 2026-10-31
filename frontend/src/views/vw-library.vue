<script setup>
    import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElIcon from '@/components/el-icon.vue';
    import ElSheet from '@/components/el-sheet.vue';
    import { mediaUrl } from '@/services/data.js';

    const TYPE_ORDER = ['person', 'specimen', 'media', 'item', 'publication', 'location', 'expedition', 'other'];
    const HIDDEN_TYPES = ['term'];
    const TYPE_ICONS = {
        person : 'person',
        specimen : 'specimen',
        media : 'image',
        location : 'location',
        item : 'item',
        publication : 'book',
        expedition : 'anchor',
        other : 'info'
    };

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    // Vue Router sets history.state.forward when the user came back with the back button
    const isReturning = Boolean(window.history.state?.forward);

    const sheet = ref(null);
    const query = ref(isReturning ? store.library.query : '');
    const filter = ref(route.query.type ?? 'all');

    // A search always looks through everything, whatever the filter
    const isSearching = computed(() => query.value.trim() !== '');
    const activeFilter = computed(() => isSearching.value ? 'all' : filter.value);

    const types = computed(() => {
        // Terms are definitions in the text, not part of the collection
        const present = store.contentTypes.filter((type) => !HIDDEN_TYPES.includes(type));

        return TYPE_ORDER.filter((type) => present.includes(type))
            .concat(present.filter((type) => !TYPE_ORDER.includes(type)));
    });

    // Everything in the library, whatever the filter or search
    const total = computed(() => store.recordList.filter((record) => !HIDDEN_TYPES.includes(record.contentType)).length);

    const chips = computed(() => [
        {
            id : 'all',
            label : t('filter_all')
        },
        ...types.value.map((type) => ({
            id : type,
            label : t('content_type_' + type)
        }))
    ]);

    function matches(text) {
        const needle = query.value.trim().toLowerCase();

        return !needle || text.toLowerCase().includes(needle);
    }

    const groups = computed(() => {
        const result = [];

        for (const type of types.value) {
            if (activeFilter.value !== 'all' && activeFilter.value !== type) {
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
                    // The small thumbnail if the pipeline could make one
                    image : record.image ? mediaUrl(record.image.thumb ?? record.image.src) : null,
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

        return result;
    });

    function pick(id) {
        filter.value = id;
        query.value = '';
        router.replace({
            query : id === 'all' ? {} : {
                type : id
            }
        });
    }

    watch(() => route.query.type, (type) => {
        filter.value = type ?? 'all';
    });

    onMounted(async () => {
        store.setMap({
            sheet : 'full'
        });

        if (isReturning) {
            await nextTick();
            sheet.value?.scrollTo(store.library.scrollTop);
        }
    });

    onBeforeUnmount(() => {
        store.library = {
            query : query.value,
            scrollTop : sheet.value?.scrollPosition() ?? 0
        };
    });
</script>

<template>
    <div class="vw-library">
        <el-sheet
            ref="sheet"
            state="screen">
            <div class="bar"></div>

            <h1 class="title">{{ t('library') }}</h1>

            <p class="kicker total">{{ total }} {{ t('library_total') }}</p>

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
                    v-bind:aria-pressed="activeFilter === chip.id ? 'true' : 'false'"
                    v-bind:is-active="activeFilter === chip.id ? '' : null"
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
                    <span class="group__count">{{ group.items.length }}</span>
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

    // Leaves room for the menu button in the top right corner (see app.vue)
    // Leaves room for the menu button in the top right corner (see app.vue)
    .bar {
        display: flex;
        align-items: center;
        min-height: 4.8rem;
    }

    .title {
        margin: 0.8rem 0 1.2rem;
        padding-top: 1.2rem;
        border-top: 1px solid var(--c-ink);
        font-weight: 700;
        font-size: 3.2rem;
        line-height: 1.06;
    }

    .total {
        margin: -0.4rem 0 1.6rem;
        color: var(--c-ink-soft);
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
</style>
