<script setup>
    import { computed, ref } from 'vue';
    import { formatDate } from '@/services/format.js';
    import ElIcon from '@/components/el-icon.vue';
    import ElExplorerBadge from './el-explorer-badge.vue';
    import ElExplorerIcon from './el-explorer-icon.vue';
    import ElExplorerTerm from './el-explorer-term.vue';
    import { groupName } from './groups.js';

    const TYPE_TEXT = {
        1 : 'Op dit exemplaar is de soort beschreven. Het legt de naam vast: wie wil weten wat deze soort is, moet dit dier bekijken.',
        2 : 'Samen met een paar andere exemplaren is de soort op dit dier beschreven. Het is een van de dragers van de naam.',
        3 : 'Het museum noemt dit typemateriaal, maar niet van welke soort.',
        4 : 'Aanvullend typemateriaal bij de eerste beschrijving.',
        5 : 'Komt van dezelfde vindplaats als het type, maar is zelf geen officieel type.'
    };

    const emit = defineEmits(['close']);

    const props = defineProps({
        specimen : {
            type : Object,
            required : true
        }
    });

    const isImageLoaded = ref(false);

    const typeTitle = computed(() => {
        if (props.specimen.typeRank === 1) {
            return 'Naamdrager';
        }

        return props.specimen.typeRank === 2 ? 'Een van de naamdragers' : 'Typemateriaal';
    });

    // First identification, any later ones, and the name it has now; as many as the record knows
    const identifications = computed(() => props.specimen.identifications.map((identification, i, list) => ({
        ...identification,
        key : `${i}-${identification.name}`,
        label : identificationLabel(identification, i, list.length)
    })));

    const evidenceParts = computed(() => {
        const evidence = props.specimen.evidence;

        if (!evidence?.text) {
            return null;
        }

        const at = evidence.text.indexOf(evidence.match);

        if (at < 0) {
            return [evidence.text, '', ''];
        }

        return [
            evidence.text.slice(0, at),
            evidence.match,
            evidence.text.slice(at + evidence.match.length)
        ];
    });

    function identificationLabel(identification, index, count) {
        const parts = [index === 0 ? 'Gedetermineerd' : 'Opnieuw gedetermineerd'];

        if (identification.date) {
            parts.push(formatDate(identification.date));
        }

        if (identification.current && count > 1) {
            parts.push('huidige naam');
        }

        return parts.join(' · ');
    }
</script>

<template>
    <section
        class="el-explorer-specimen"
        v-bind:aria-label="specimen.name">
        <div
            class="visual"
            v-bind:has-image="isImageLoaded ? '' : null">
            <img
                v-if="specimen.image"
                class="visual__image"
                alt=""
                v-bind:src="specimen.image.src"
                v-on:load="isImageLoaded = true">

            <el-explorer-icon
                v-if="!isImageLoaded"
                class="visual__icon"
                v-bind:group="specimen.group"
                v-bind:size="96" />

            <button
                type="button"
                class="close"
                aria-label="Terug"
                v-on:click="emit('close')">
                <el-icon
                    name="arrowLeft"
                    v-bind:size="20" />
            </button>

            <p
                v-if="specimen.image"
                class="visual__credit">{{ specimen.image.credit }} · {{ specimen.image.license }}</p>
        </div>

        <div class="body">
            <header class="head">
                <h2 class="name">{{ specimen.name }}</h2>
                <p class="meta">{{ [specimen.family, groupName(specimen.group)].filter(Boolean).join(' · ') }}</p>
            </header>

            <div
                v-if="specimen.typeRank"
                class="type"
                v-bind:is-name-bearer="specimen.isNameBearer ? '' : null">
                <el-explorer-badge
                    v-if="specimen.isNameBearer"
                    class="type__badge"
                    v-bind:size="52" />
                <div class="type__text">
                    <strong class="type__title">{{ typeTitle }}<template v-if="specimen.typeStatus"> · {{ specimen.typeStatus }}</template></strong>
                    <p class="type__body">{{ TYPE_TEXT[specimen.typeRank] }}</p>
                    <p
                        v-if="specimen.typeNote"
                        class="type__note">{{ specimen.typeNote }}</p>
                </div>
            </div>

            <ol class="journey">
                <li class="step">
                    <svg
                        class="step__icon"
                        viewBox="0 0 32 32"
                        aria-hidden="true">
                        <path d="M4 20 L28 20 L25 25 L8 25 Z M11 20 V8 M21 20 V10 M15 20 v-6 h4 v6" />
                        <path d="M2 28 c3-2 5 2 8 0 s5 2 8 0 s5 2 8 0" />
                    </svg>
                    <div class="step__text">
                        <el-explorer-term
                            class="step__label"
                            term="eventDate"
                            text="De datum van het verzamelen volgens het museumrecord.">Geregistreerd · {{ specimen.date ? formatDate(specimen.date) : 'datum onbekend' }}</el-explorer-term>
                        <el-explorer-term
                            v-if="specimen.station"
                            class="step__main"
                            text="Geen veld in het record: wij hebben het afgeleid. Het stationsnummer staat in de tekst van het record en de datum past bij het station. Het bewijs staat onderaan.">Station {{ specimen.station.nummer }}</el-explorer-term>
                        <el-explorer-term
                            class="step__sub"
                            term="recordedBy"
                            text="Wie het verzamelde, letterlijk zoals het record het schrijft. Dat kan een persoon zijn, maar ook de expeditie of het schip.">Verzameld door: {{ specimen.collectors.length ? specimen.collectors.join(', ') : 'onbekend, staat niet in het record' }}</el-explorer-term>
                        <el-explorer-term
                            v-if="specimen.locality"
                            class="step__raw"
                            term="locality"
                            text="De vindplaats, letterlijk uit het record.">{{ specimen.locality }}</el-explorer-term>
                    </div>
                </li>

                <li
                    v-for="identification in identifications"
                    v-bind:key="identification.key"
                    class="step">
                    <svg
                        class="step__icon"
                        viewBox="0 0 32 32"
                        aria-hidden="true">
                        <path d="M6 26 l3-9 L22 4 l6 6 L15 23 Z M9 17 l6 6 M19 7 l6 6 M4 28 h10" />
                    </svg>
                    <div class="step__text">
                        <el-explorer-term
                            class="step__label"
                            term="dateIdentified"
                            text="Wanneer de soort bepaald is, volgens het record.">{{ identification.label }}</el-explorer-term>
                        <el-explorer-term
                            class="step__main"
                            term="identifiedBy"
                            text="Wie de soort bepaalde, letterlijk zoals het record het schrijft.">{{ identification.by.length ? identification.by.join(', ') : 'onbekend, staat niet in het record' }}</el-explorer-term>
                        <el-explorer-term
                            v-if="identification.name"
                            class="step__raw step__raw--name"
                            term="scientificName"
                            text="De naam die bij deze determinatie hoort.">{{ identification.name }}</el-explorer-term>
                        <span
                            v-if="identification.remarks"
                            class="step__raw">{{ identification.remarks }}</span>
                    </div>
                </li>

                <li
                    v-if="!identifications.length"
                    class="step">
                    <svg
                        class="step__icon"
                        viewBox="0 0 32 32"
                        aria-hidden="true">
                        <path d="M6 26 l3-9 L22 4 l6 6 L15 23 Z M9 17 l6 6 M19 7 l6 6 M4 28 h10" />
                    </svg>
                    <div class="step__text">
                        <el-explorer-term
                            class="step__label"
                            term="identifiedBy"
                            text="Wie de soort bepaalde, volgens het record.">Gedetermineerd</el-explorer-term>
                        <span class="step__main">onbekend, staat niet in het record</span>
                    </div>
                </li>

                <li class="step">
                    <svg
                        class="step__icon"
                        viewBox="0 0 32 32"
                        aria-hidden="true">
                        <path d="M4 12 L16 5 L28 12 Z M6 12 v12 M11 12 v12 M16 12 v12 M21 12 v12 M26 12 v12 M3 27 h26" />
                    </svg>
                    <div class="step__text">
                        <span class="step__label">Nu in</span>
                        <el-explorer-term
                            class="step__main"
                            term="publishingOrganization"
                            text="De organisatie die het record op GBIF publiceert.">{{ specimen.museum?.organisatie ?? specimen.museum?.naam }}</el-explorer-term>
                        <el-explorer-term
                            class="step__raw"
                            term="catalogNumber"
                            text="Plaats van de organisatie volgens GBIF, en het nummer van het exemplaar in de collectie.">{{ [specimen.museum?.stad, specimen.catalog].filter(Boolean).join(' · ') }}</el-explorer-term>
                    </div>
                </li>
            </ol>

            <div class="links">
                <a
                    v-if="specimen.naturalisUrl"
                    class="button button--primary button--block"
                    target="_blank"
                    rel="noopener"
                    v-bind:href="specimen.naturalisUrl">Bekijk bij Naturalis</a>
                <a
                    class="button button--outline button--block"
                    target="_blank"
                    rel="noopener"
                    v-bind:href="specimen.gbifUrl">Bekijk bij GBIF</a>
            </div>

            <section
                v-if="evidenceParts && specimen.station"
                class="evidence">
                <h3 class="evidence__title">Hoe we weten dat het van station {{ specimen.station.nummer }} komt</h3>
                <p class="evidence__text">In het museumrecord, veld <code>{{ specimen.evidence.field }}</code>: “{{ evidenceParts[0] }}<mark>{{ evidenceParts[1] }}</mark>{{ evidenceParts[2] }}”</p>
            </section>

            <p
                v-if="specimen.dataset"
                class="credit">{{ specimen.dataset.bronvermelding ?? specimen.dataset.titel }} · {{ specimen.license }}</p>
        </div>
    </section>
</template>

<style lang="scss" scoped>
    .el-explorer-specimen {
        --c-brass: #B8862E;

        position: absolute;
        inset: 0;
        z-index: 8;
        display: flex;
        flex-direction: column;
        background: var(--c-paper);
        overflow-y: auto;
        overscroll-behavior: contain;
        animation: open 0.45s cubic-bezier(0.2, 0.7, 0.2, 1) backwards;

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

    .visual {
        position: relative;
        flex: none;
        height: 32rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--c-plate);
        color: var(--c-handle);
        overflow: hidden;
    }

    .visual__image {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: contain;
        opacity: 0;
        transform: scale(1.25);
        transition: opacity 0.5s, transform 1.4s cubic-bezier(0.2, 0.7, 0.2, 1);

        [has-image] > & {
            opacity: 1;
            transform: scale(1);
        }
    }

    .visual__credit {
        position: absolute;
        right: 0.8rem;
        bottom: 0.6rem;
        margin: 0;
        max-width: 80%;
        padding: 0.2rem 0.6rem;
        border-radius: 3px;
        background: rgba(251, 248, 241, 0.85);
        font-size: 1.1rem;
        color: var(--c-ink-soft);
    }

    .close {
        position: absolute;
        top: 1.2rem;
        left: 1.2rem;
        width: 4.4rem;
        height: 4.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 0;
        border-radius: 50%;
        background: var(--c-paper);
        color: var(--c-marine);
        box-shadow: var(--shadow-float);
        cursor: pointer;
    }

    .body {
        display: flex;
        flex-direction: column;
        gap: 2.4rem;
        padding: 2rem 1.8rem 3.2rem;
    }

    .head {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    .name {
        margin: 0;
        font-style: italic;
        font-weight: 400;
        font-size: 3rem;
        line-height: 1.1;
    }

    .meta {
        margin: 0;
        color: var(--c-ink-soft);
    }

    .type {
        display: flex;
        align-items: flex-start;
        gap: 1.4rem;
        padding: 1.4rem 1.6rem;
        border-radius: 8px;
        background: var(--c-plate);

        &[is-name-bearer] {
            background: #F4E7C9;
            box-shadow: inset 0 0 0 1px var(--c-brass);
        }
    }

    .type__text {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    .type__title {
        font-family: var(--font-header);
        font-weight: 400;
        font-size: 2rem;
    }

    .type__body,
    .type__note {
        margin: 0;
        font-size: 1.6rem;
    }

    .type__note {
        font-style: italic;
        color: var(--c-ink-soft);
    }

    .journey {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
    }

    .step {
        position: relative;
        display: flex;
        gap: 1.4rem;
        padding-bottom: 2rem;

        // The line that joins the steps
        &:not(:last-child)::before {
            content: "";
            position: absolute;
            left: 2.2rem;
            top: 4.8rem;
            bottom: 0.4rem;
            border-left: 2px dotted var(--c-frame);
        }
    }

    .step__icon {
        flex: none;
        width: 4.4rem;
        height: 4.4rem;
        padding: 0.6rem;
        box-sizing: border-box;
        border-radius: 50%;
        background: var(--c-plate);

        path {
            fill: none;
            stroke: var(--c-marine);
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
    }

    .step__text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        padding-top: 0.4rem;
    }

    .step__label {
        font-family: var(--font-header);
        font-size: var(--fs-kicker);
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--c-ink-soft);
    }

    .step__main {
        font-size: 1.8rem;
    }

    .step__sub {
        font-size: 1.5rem;
    }

    .step__raw {
        font-size: 1.4rem;
        color: var(--c-ink-soft);
    }

    .step__raw--name {
        font-style: italic;
    }

    .links {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .evidence {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
    }

    .evidence__title {
        margin: 0;
        font-family: var(--font-header);
        font-size: var(--fs-kicker);
        font-weight: 400;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--c-ink-soft);
    }

    .evidence__text {
        margin: 0;
        font-size: 1.5rem;

        mark {
            padding: 0 0.2rem;
            background: var(--c-terracotta-soft);
            color: var(--c-ink);
        }

        code {
            font-size: 1.3rem;
        }
    }

    .credit {
        margin: 0;
        font-size: 1.3rem;
        color: var(--c-ink-soft);
    }

    @keyframes open {
        from {
            opacity: 0;
            transform: scale(0.94);
        }
    }
</style>
