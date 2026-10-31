<script setup>
    // Crossing the line: Neptune rises from the sea and hands out a certificate, as sailors did
    // when a ship crossed the equator. The certificate can be saved as an image.
    import { computed } from 'vue';

    const emit = defineEmits(['close']);

    const props = defineProps({
        lon : {
            type : Number,
            required : true
        },
        at : {
            type : Number,
            required : true
        }
    });

    const dateText = computed(() => new Date(props.at).toLocaleDateString('nl-NL', {
        day : 'numeric',
        month : 'long',
        year : 'numeric'
    }));
    const lonText = computed(() => `${props.lon.toFixed(1).replace('.', ',')}° oosterlengte`);
    const lines = computed(() => [
        'Hierbij verklaart Neptunus, heerser over alle zeeën,',
        'dat de bemanning van de Siboga',
        `op ${dateText.value} de Linie is gepasseerd,`,
        `op ${lonText.value}, en dus gedoopt is.`
    ]);

    function save() {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        canvas.width = 1200;
        canvas.height = 800;
        context.fillStyle = '#FBF8F1';
        context.fillRect(0, 0, 1200, 800);
        context.strokeStyle = '#8A3F24';
        context.lineWidth = 10;
        context.strokeRect(30, 30, 1140, 740);
        context.lineWidth = 2;
        context.strokeRect(52, 52, 1096, 696);
        context.textAlign = 'center';
        context.fillStyle = '#A9512F';
        context.font = '600 30px "Old Standard TT", Georgia, serif';
        context.fillText('OORKONDE', 600, 150);
        context.fillStyle = '#163A5C';
        context.font = '700 64px "Old Standard TT", Georgia, serif';
        context.fillText('Linedoop', 600, 235);
        context.fillStyle = '#1B2433';
        context.font = 'italic 34px "Old Standard TT", Georgia, serif';
        lines.value.forEach((line, i) => context.fillText(line, 600, 340 + i * 56));
        context.font = '26px Georgia, serif';
        context.fillStyle = '#4A5263';
        context.fillText('Getekend: Neptunus  🔱', 600, 640);
        context.font = '20px Georgia, serif';
        context.fillText('De Siboga Expeditie · het spel', 600, 700);
        canvas.toBlob((blob) => {
            const link = document.createElement('a');

            link.href = URL.createObjectURL(blob);
            link.download = 'linedoop-siboga.png';
            link.click();
            setTimeout(() => URL.revokeObjectURL(link.href), 1000);
        });
    }
</script>

<template>
    <div class="el-game-equator">
        <svg
            class="neptune"
            viewBox="0 0 200 220"
            aria-hidden="true">
            <path
                class="neptune__trident"
                d="M150 20 L150 200 M135 22 Q135 50 150 55 Q165 50 165 22 M150 10 L150 30" />
            <path
                class="neptune__crown"
                d="M70 52 L76 30 L86 46 L100 24 L114 46 L124 30 L130 52 Z" />
            <circle
                class="neptune__face"
                cx="100"
                cy="78"
                r="28" />
            <circle
                cx="90"
                cy="74"
                r="3" />
            <circle
                cx="110"
                cy="74"
                r="3" />
            <path
                class="neptune__beard"
                d="M72 84 Q74 130 100 150 Q126 130 128 84 Q118 98 100 98 Q82 98 72 84 Z" />
            <path
                class="neptune__body"
                d="M56 220 Q60 150 100 140 Q140 150 144 220 Z" />
            <path
                class="neptune__arm"
                d="M132 160 Q142 120 150 110" />
            <path
                class="neptune__waves"
                d="M0 200 Q25 185 50 200 T100 200 T150 200 T200 200 L200 220 L0 220 Z" />
        </svg>

        <div class="certificate">
            <p class="kicker">Oorkonde</p>
            <h2>Linedoop</h2>
            <p class="text">
                <span
                    v-for="line in lines"
                    v-bind:key="line">{{ line }}</span>
            </p>
            <p class="fact">Volgens onze route stak de echte Siboga de evenaar voor het eerst over tussen station 87 (19 juni 1899) en station 88 (20 juni 1899), in de Straat Makassar. Daarna nog drie keer, rond Halmahera en Waigeo.</p>
            <div class="buttons">
                <button
                    class="button button--outline"
                    type="button"
                    v-on:click="save()">Oorkonde bewaren</button>
                <button
                    class="button button--primary"
                    type="button"
                    v-on:click="emit('close')">Verder varen</button>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
    .el-game-equator {
        position: absolute;
        inset: 0;
        z-index: 18;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0;
        padding: 1.6rem;
        background: rgba(12, 32, 52, 0.6);
        overflow-y: auto;
        animation: fade 0.3s ease;
    }

    .neptune {
        flex: none;
        width: 16rem;
        margin-bottom: -2rem;
        animation: rise-up 1.4s cubic-bezier(0.2, 0.8, 0.3, 1);
    }

    .neptune__trident {
        fill: none;
        stroke: #B8862E;
        stroke-width: 5;
        stroke-linecap: round;
    }

    .neptune__crown {
        fill: #E2B94F;
        stroke: #8A6420;
        stroke-width: 2;
    }

    .neptune__face {
        fill: #E8C4A0;
    }

    .neptune__beard {
        fill: #EDEDED;
        stroke: #B8B8B8;
        stroke-width: 1.5;
    }

    .neptune__body {
        fill: #2F7F8F;
    }

    .neptune__arm {
        fill: none;
        stroke: #E8C4A0;
        stroke-width: 10;
        stroke-linecap: round;
    }

    .neptune__waves {
        fill: #1F5280;
    }

    .certificate {
        position: relative;
        width: 100%;
        max-width: 46rem;
        padding: 2.4rem;
        border: 6px double var(--c-terracotta-dark);
        border-radius: 0.4rem;
        background: var(--c-paper);
        box-shadow: var(--shadow-card);
        text-align: center;
        animation: pop 0.5s 0.6s ease-out backwards;

        h2 {
            margin: 0 0 1.2rem;
            font-family: var(--font-header);
            font-size: 3.6rem;
            color: var(--c-marine);
        }
    }

    .kicker {
        margin: 0;
        color: var(--c-terracotta);
    }

    .text {
        display: flex;
        flex-direction: column;
        margin: 0 0 1.2rem;
        font-family: var(--font-header);
        font-size: 1.8rem;
        font-style: italic;
        line-height: 1.5;
    }

    .fact {
        margin: 0 0 1.6rem;
        color: var(--c-ink-soft);
        font-size: 1.4rem;
    }

    .buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;

        .button {
            flex: 1 1 16rem;
        }

        .button--primary {
            border: 0;
        }
    }

    @keyframes fade {
        from {
            opacity: 0;
        }
    }

    @keyframes rise-up {
        from {
            opacity: 0;
            transform: translateY(8rem);
        }
    }

    @keyframes pop {
        from {
            opacity: 0;
            transform: scale(0.85);
        }
    }
</style>
