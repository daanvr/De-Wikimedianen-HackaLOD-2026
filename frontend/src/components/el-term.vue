<script setup>
    import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { renderSegments } from '@/services/markdown.js';

    const t = inject('t');
    const router = useRouter();

    const emit = defineEmits(['close']);

    const props = defineProps({
        // The record of the term, with its definition as body
        term : {
            type : Object,
            required : true
        },
        // The link in the text that opened it; the card is placed next to it
        anchor : {
            type : HTMLElement,
            required : true
        },
        id : {
            type : String,
            required : true
        },
        lookupKind : {
            type : Function,
            default : null
        }
    });

    // Space between the card and the word, and between the card and the edge of the screen, in px
    const GAP = 8;
    const MARGIN = 16;

    const card = ref(null);
    const position = ref({
        top : 0,
        left : 0
    });
    const isPlaced = ref(false);

    const html = computed(() => renderSegments(props.term.body, {
        lookupKind : props.lookupKind
    }).filter((segment) => segment.type === 'html').map((segment) => segment.html).join(''));

    function close(returnFocus = false) {
        emit('close');

        if (returnFocus) {
            props.anchor.focus();
        }
    }

    function onClick(event) {
        const link = event.target.closest('a[data-internal]');

        if (!link || event.metaKey || event.ctrlKey || event.shiftKey) {
            return;
        }

        event.preventDefault();
        close();
        router.push(link.getAttribute('href'));
    }

    function onKeydown(event) {
        if (event.key === 'Escape') {
            close(true);
        }
    }

    // A click on the word itself is left to el-markdown, which closes the card
    function onPointerdown(event) {
        if (!card.value?.contains(event.target) && !props.anchor.contains(event.target)) {
            close();
        }
    }

    // The card stays where it was placed, so it closes once the text moves under it
    function onScroll(event) {
        if (!card.value?.contains(event.target)) {
            close();
        }
    }

    // Below the word, or above it if there is no room below; never past the edge of the screen
    function place() {
        const word = props.anchor.getBoundingClientRect();
        const { width, height } = card.value.getBoundingClientRect();
        const below = word.bottom + GAP;
        const top = below + height > window.innerHeight - MARGIN && word.top - GAP - height > MARGIN
            ? word.top - GAP - height
            : below;
        const left = Math.min(Math.max(word.left, MARGIN), window.innerWidth - width - MARGIN);

        position.value = {
            top,
            left : Math.max(left, MARGIN)
        };
        isPlaced.value = true;
    }

    onMounted(async () => {
        await nextTick();
        place();
        card.value.focus({
            preventScroll : true
        });

        window.addEventListener('keydown', onKeydown);
        window.addEventListener('pointerdown', onPointerdown);
        window.addEventListener('resize', close);
        window.addEventListener('scroll', onScroll, true);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', onKeydown);
        window.removeEventListener('pointerdown', onPointerdown);
        window.removeEventListener('resize', close);
        window.removeEventListener('scroll', onScroll, true);
    });
</script>

<template>
    <!-- In body, so the card is not clipped by the scrolling sheet -->
    <teleport to="body">
        <div
            v-bind:id="id"
            ref="card"
            class="el-term"
            role="dialog"
            tabindex="-1"
            v-bind:aria-labelledby="`${id}-title`"
            v-bind:is-placed="isPlaced ? '' : null"
            v-bind:style="{
                top : `${position.top}px`,
                left : `${position.left}px`
            }"
            v-on:click="onClick">
            <p
                v-bind:id="`${id}-title`"
                class="title">
                {{ term.label || term.title }}
            </p>

            <div
                class="definition"
                v-html="html"></div>

            <a
                v-if="term.uri"
                class="more"
                v-bind:href="term.uri"
                target="_blank"
                rel="noopener">
                {{ t('term_read_more') }}
            </a>
        </div>
    </teleport>
</template>

<style lang="scss" scoped>
    .el-term {
        position: fixed;
        z-index: 200;
        width: min(32rem, calc(100vw - 3.2rem));
        padding: 1.2rem 1.4rem;
        border: 1px solid var(--c-rule);
        border-radius: 6px;
        background: var(--c-paper);
        box-shadow: var(--shadow-float);
        font-family: var(--font-text);
        font-size: 1.6rem;
        line-height: 1.5;
        color: var(--c-ink-body);
        // Hidden until it is placed, so it does not flash in the corner
        visibility: hidden;

        &[is-placed] {
            visibility: visible;
        }

        &:focus {
            outline: none;
        }

        &:focus-visible {
            outline: 2px solid var(--c-link);
            outline-offset: 2px;
        }
    }

    .title {
        margin: 0 0 0.4rem;
        font-weight: 700;
        color: var(--c-ink);
    }

    .definition {
        :deep(p) {
            margin: 0 0 0.8rem;

            &:last-child {
                margin-bottom: 0;
            }
        }

        :deep(a) {
            color: var(--c-link);
            text-underline-offset: 3px;
        }

        :deep(img) {
            max-width: 100%;
        }

        :deep(img.icon-image) {
            margin: 0 0.2rem;
            vertical-align: -0.2rem;
        }
    }

    .more {
        display: inline-block;
        margin-top: 0.8rem;
        font-size: 1.4rem;
        color: var(--c-link);
        text-underline-offset: 3px;

        &:hover {
            color: var(--c-terracotta);
        }
    }
</style>
