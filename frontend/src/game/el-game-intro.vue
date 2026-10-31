<script setup>
    // The start of the game: how to play, and that the places of the specimens are made up
    import { ref } from 'vue';

    const emit = defineEmits(['start', 'close']);

    const props = defineProps({
        hasSave : {
            type : Boolean,
            default : false
        },
        // Opened from the info button during the game: only the explanation and a way back
        isInfo : {
            type : Boolean,
            default : false
        }
    });

    const isConfirming = ref(false);

    function startNew() {
        if (props.hasSave && !isConfirming.value) {
            isConfirming.value = true;

            return;
        }

        emit('start', true);
    }
</script>

<template>
    <div class="el-game-intro">
        <div class="card">
            <p class="kicker">Spel</p>
            <h1 class="title">Vaar zelf met de Siboga</h1>

            <ul class="controls">
                <li>
                    <strong>Stuurwiel</strong> rechtsonder: pak het vast en draai. Laat je los, dan draait het vanzelf terug. Op een toetsenbord kan het ook met ← en →.
                </li>
                <li>
                    <strong>Kolen</strong> linksonder: elke schep geeft stoom, en stoom geeft vaart. Stook niet te hard, anders springt de veiligheidsklep. Op een toetsenbord met de spatiebalk.
                </li>
                <li>
                    <strong>Verzamelen:</strong> vaar over de specimens die in zee drijven, en langs de stations. Zeldzame specimens en naamdragers tellen veel meer punten. Alles wat je vangt, komt in je album.
                </li>
            </ul>

            <div class="disclaimer">
                <h2>Een spel, geen kaart van de werkelijkheid</h2>
                <p>Dit is een spel, een soort artist impression. De specimens zijn echt: de Siboga heeft ze verzameld en ze liggen nu in een museum. Waar ze in het spel drijven, is verzonnen. We hebben ze zo goed mogelijk in de buurt gelegd van waar de Siboga die dag voer, maar het is geen echte vindplek.</p>
                <p>
                    Wil je zien wat we zeker weten? Kijk dan in de
                    <router-link to="/map">Datavisualisatie</router-link>.
                </p>
            </div>

            <div
                v-if="isInfo"
                class="buttons">
                <button
                    class="button button--primary"
                    type="button"
                    v-on:click="emit('close')">Verder varen</button>
            </div>

            <div
                v-else
                class="buttons">
                <button
                    v-if="hasSave"
                    class="button button--primary"
                    type="button"
                    v-on:click="emit('start', false)">Verder varen</button>
                <button
                    class="button"
                    v-bind:class="hasSave ? 'button--outline' : 'button--primary'"
                    type="button"
                    v-on:click="startNew()">{{ isConfirming ? 'Zeker? Je album wordt leeggemaakt' : 'Nieuwe reis' }}</button>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-intro {
        position: absolute;
        inset: 0;
        z-index: 20;
        display: flex;
        align-items: center;
        justify-content: center;
        // Room for the menu button of the app
        padding: 7.6rem 1.6rem 1.6rem;
        background: var(--c-scrim);
        animation: fade-in 0.2s ease;
        overflow-y: auto;
    }

    .card {
        width: 100%;
        max-width: 52rem;
        max-height: 100%;
        overflow-y: auto;
        padding: 2.4rem 2.4rem 2rem;
        border-radius: 1.2rem;
        background: var(--c-paper);
        box-shadow: var(--shadow-card);
        font-size: 1.6rem;
        line-height: 1.45;
    }

    .kicker {
        margin: 0;
        font-size: var(--fs-kicker);
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--c-terracotta);
    }

    .title {
        margin: 0.4rem 0 1.4rem;
        font-family: var(--font-header);
        font-size: 3rem;
        line-height: 1.1;
        color: var(--c-marine);
    }

    .controls {
        margin: 0 0 1.6rem;
        padding-left: 1.8rem;

        li {
            margin-bottom: 0.6rem;
        }
    }

    .disclaimer {
        padding: 1.2rem 1.4rem;
        border-left: 3px solid var(--c-terracotta-light);
        background: var(--c-plate);
        font-size: 1.5rem;

        h2 {
            margin: 0 0 0.6rem;
            font-family: var(--font-header);
            font-size: 1.8rem;
        }

        p {
            margin: 0 0 0.6rem;

            &:last-child {
                margin-bottom: 0;
            }
        }
    }

    // Stays in view at the bottom of the card while the text scrolls
    .buttons {
        position: sticky;
        bottom: -2rem;
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 1.8rem -2.4rem -2rem;
        padding: 1.2rem 2.4rem 2rem;
        background: var(--c-paper);
        box-shadow: 0 -8px 12px -10px rgba(8, 26, 44, 0.35);

        .button {
            flex: 1 1 18rem;
        }

        .button--primary {
            border: 0;
        }
    }

    @keyframes fade-in {
        from {
            opacity: 0;
        }
    }
</style>
