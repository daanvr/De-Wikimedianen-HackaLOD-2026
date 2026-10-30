<script setup>
    import { computed, inject, onMounted, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import ElIcon from '@/components/el-icon.vue';
    import { formatDate } from '@/services/format.js';

    const store = inject('store');
    const t = inject('t');
    const route = useRoute();
    const router = useRouter();

    const stationId = computed(() => route.query.station ? String(route.query.station) : null);
    const station = computed(() => stationId.value ? store.stationById(stationId.value) : null);
    const properties = computed(() => station.value?.properties ?? {});
    const wikidataUrl = computed(() => properties.value.wikidata_uri?.replace('http://www.wikidata.org/entity/', 'https://www.wikidata.org/wiki/') ?? null);

    function close() {
        router.replace({
            path : '/map'
        });
    }

    function update() {
        const settings = {
            mode : 'explore',
            stationId : stationId.value,
            sheet : 'none',
            boat : null
        };

        if (station.value) {
            const [lon, lat] = station.value.geometry.coordinates;

            settings.focus = {
                lon,
                lat,
                zoom : Math.max(6, store.map.focus?.zoom ?? 6)
            };
            settings.sheet = 'peek';
        } else if (store.map.mode !== 'explore') {
            settings.focus = null;
        }

        store.setMap(settings);
    }

    watch(stationId, update);

    onMounted(update);
</script>

<template>
    <div class="vw-map">
        <div class="top">
            <router-link
                class="dataset"
                to="/library?type=station">
                <el-icon
                    class="dataset__icon"
                    name="station"
                    v-bind:size="20" />
                <span class="dataset__label">{{ t('stations_all') }}</span>
                <span class="dataset__count">{{ store.stations.length }}</span>
            </router-link>

            <router-link
                v-for="plugin in store.explorePlugins"
                v-bind:key="plugin.id"
                class="dataset"
                is-plugin
                v-bind:to="`/plugins/${plugin.id}`">
                <el-icon
                    class="dataset__icon"
                    name="explore"
                    v-bind:size="20" />
                <span class="dataset__text">
                    <span class="dataset__label">{{ plugin.title }}</span>
                    <span
                        v-if="plugin.description"
                        class="dataset__description">{{ plugin.description }}</span>
                </span>
            </router-link>
        </div>

        <article
            v-if="station"
            class="card">
            <div class="card__inner">
                <div class="kicker card__kicker">
                    <span>{{ t('station') }} {{ properties.station }}</span>
                    <span class="card__date">{{ formatDate(properties.start_date) }}</span>
                </div>

                <h1 class="card__title">
                    {{ properties.depth_m ? `${t('station_depth')} ${properties.depth_m} m` : `${t('station')} ${properties.station}` }}
                </h1>

                <dl class="card__facts">
                    <div v-if="properties.bottom">
                        <dt>{{ t('station_bottom') }}</dt>
                        <dd>{{ properties.bottom }}</dd>
                    </div>
                    <div v-if="properties.operations">
                        <dt>{{ t('station_operations') }}</dt>
                        <dd>{{ properties.operations }}</dd>
                    </div>
                    <div v-if="properties.remarks">
                        <dt>{{ t('station_remarks') }}</dt>
                        <dd>{{ properties.remarks }}</dd>
                    </div>
                </dl>

                <div class="card__actions">
                    <a
                        v-if="wikidataUrl"
                        class="button button--primary card__button"
                        v-bind:href="wikidataUrl"
                        target="_blank"
                        rel="noopener">
                        {{ t('station_source') }}
                        <el-icon
                            name="external"
                            v-bind:size="16" />
                    </a>
                    <button
                        type="button"
                        class="button button--outline"
                        v-on:click="close()">
                        {{ t('close') }}
                    </button>
                </div>
            </div>
        </article>
    </div>
</template>

<style lang="scss" scoped>
    @use "../../node_modules/valenski/mixins";

    .vw-map {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }

    .top {
        position: absolute;
        top: 1.6rem;
        left: 1.6rem;
        // Leaves room for the menu button (see app.vue)
        right: 7.4rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        z-index: 30;

        @include mixins.respond-from(900px) {
            left: auto;
            width: 34.2rem;
        }
    }

    .dataset {
        pointer-events: auto;
        flex: 1;
        min-width: 0;
        height: 4.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0 1.2rem;
        background: var(--c-paper);
        color: var(--c-ink);
        text-decoration: none;
        border: 1px solid var(--c-marine);
        border-radius: 4px;
        box-shadow: inset 0 0 0 3px var(--c-paper), inset 0 0 0 4px #D8CFBB, var(--shadow-float);

        &:hover {
            color: var(--c-ink);
        }

        &[is-plugin] {
            height: auto;
            min-height: 4.8rem;
            padding: 0.8rem 1.2rem;
        }
    }

    .dataset__icon {
        color: var(--c-terracotta);
    }

    .dataset__label {
        flex: 1;
        font-family: var(--font-header);
        font-size: 1.7rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .dataset__text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;

        .dataset__label {
            flex: none;
        }
    }

    .dataset__description {
        font-size: 1.4rem;
        line-height: 1.3;
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .dataset__count {
        font-size: 1.4rem;
        color: var(--c-ink-soft);
    }

    .card {
        pointer-events: auto;
        position: absolute;
        left: 1.6rem;
        right: 1.6rem;
        bottom: 2rem;
        max-height: 60%;
        overflow-y: auto;
        background: var(--c-paper);
        border: 2px solid var(--c-ink);
        padding: 0.4rem;
        box-shadow: 0 14px 32px rgba(8, 26, 44, 0.4);
        z-index: 20;
        animation: rise 0.3s ease;

        @include mixins.respond-from(900px) {
            left: 1.6rem;
            right: auto;
            width: 40rem;
        }
    }

    .card__inner {
        border: 1px solid var(--c-ink);
        padding: 1.4rem 1.6rem 1.6rem;
    }

    .card__kicker {
        display: flex;
        justify-content: space-between;
        color: var(--c-terracotta);
    }

    .card__date {
        color: var(--c-ink-soft);
    }

    .card__title {
        margin: 0.6rem 0 0.8rem;
        font-weight: 700;
        font-size: 2.4rem;
        line-height: 1.1;
    }

    .card__facts {
        margin-bottom: 1.4rem;
        font-size: 1.5rem;
        color: var(--c-ink-soft);

        div {
            margin-bottom: 0.4rem;
        }

        dt {
            display: inline;
            font-family: var(--font-header);
            font-size: 1.1rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;

            &::after {
                content: " ";
            }
        }

        dd {
            display: inline;
            color: var(--c-ink);
        }
    }

    .card__actions {
        display: flex;
        gap: 1rem;
    }

    .card__button {
        flex: 1;
        padding: 0 1.2rem;
        white-space: nowrap;
    }

    @keyframes rise {
        from {
            opacity: 0;
            transform: translateY(1.6rem);
        }
    }
</style>
