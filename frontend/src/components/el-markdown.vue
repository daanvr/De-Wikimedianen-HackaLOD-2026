<script setup>
    import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';
    import ElGallery from '@/components/el-gallery.vue';
    import ElLightbox from '@/components/el-lightbox.vue';
    import ElPlugin from '@/components/el-plugin.vue';
    import ElZoomedImage from '@/components/el-zoomed-image.vue';
    import { renderSegments } from '@/services/markdown.js';

    const t = inject('t');
    const router = useRouter();

    const props = defineProps({
        body : {
            type : String,
            default : null
        },
        lookupKind : {
            type : Function,
            default : null
        },
        dropCap : {
            type : Boolean,
            default : false
        },
        // An internal href ("/records/anna-weber"): its first link is highlighted and scrolled to
        highlight : {
            type : String,
            default : null
        }
    });

    // Waits for the sheet to finish opening, so the link ends up where we scrolled to
    const SCROLL_DELAY_MS = 400;

    const root = ref(null);
    const zoomedImage = ref(null);
    const segments = computed(() => renderSegments(props.body, props.lookupKind, t('image_fullscreen')));

    let scrollTimer = null;

    function highlightLink() {
        clearTimeout(scrollTimer);

        if (!root.value) {
            return;
        }

        for (const link of root.value.querySelectorAll('a[is-highlighted]')) {
            link.removeAttribute('is-highlighted');
        }

        const link = props.highlight
            ? [...root.value.querySelectorAll('a[data-internal]')].find((item) => item.getAttribute('href') === props.highlight)
            : null;

        if (!link) {
            return;
        }

        link.setAttribute('is-highlighted', '');
        scrollTimer = setTimeout(() => {
            link.scrollIntoView({
                behavior : 'smooth',
                block : 'center'
            });
        }, SCROLL_DELAY_MS);
    }

    function onClick(event) {
        const zoom = event.target.closest('button[data-zoom]');

        if (zoom) {
            const image = zoom.querySelector('img');

            zoomedImage.value = {
                src : image.getAttribute('src'),
                alt : image.getAttribute('alt') ?? '',
                caption : zoom.closest('figure')?.querySelector('figcaption')?.innerHTML ?? null
            };
            return;
        }

        const link = event.target.closest('a[data-internal]');

        if (!link || event.metaKey || event.ctrlKey || event.shiftKey) {
            return;
        }

        event.preventDefault();
        router.push(link.getAttribute('href'));
    }

    watch([segments, () => props.highlight], highlightLink, {
        flush : 'post'
    });

    onMounted(highlightLink);

    onBeforeUnmount(() => {
        clearTimeout(scrollTimer);
    });
</script>

<template>
    <div
        ref="root"
        class="el-markdown"
        v-bind:has-drop-cap="dropCap ? '' : null"
        v-on:click="onClick">
        <template
            v-for="(segment, index) in segments"
            v-bind:key="index">
            <el-plugin
                v-if="segment.type === 'plugin'"
                v-bind:id="segment.id"
                v-bind:argument="segment.argument" />

            <el-gallery
                v-else-if="segment.type === 'gallery'"
                v-bind:images="segment.images" />

            <div
                v-else
                class="segment"
                v-html="segment.html"></div>
        </template>

        <el-lightbox
            v-if="zoomedImage"
            close-on-click
            v-on:close="zoomedImage = null">
            <el-zoomed-image
                v-bind:src="zoomedImage.src"
                v-bind:alt="zoomedImage.alt"
                v-bind:caption="zoomedImage.caption" />
        </el-lightbox>
    </div>
</template>

<style lang="scss" scoped>
    $icon-person: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round'%3E%3Ccircle cx='12' cy='8' r='3.5'/%3E%3Cpath d='M5 20c0-4 3.1-6.5 7-6.5s7 2.5 7 6.5'/%3E%3C/svg%3E");
    $icon-external: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5'/%3E%3C/svg%3E");
    $icon-specimen: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round'%3E%3Cpath d='M12 12.5a1.2 1.2 0 1 1 1.2 1.2A2.6 2.6 0 0 1 10.6 11a4 4 0 0 1 4-4 5.3 5.3 0 0 1 5.3 5.3 6.7 6.7 0 0 1-6.7 6.7A8 8 0 0 1 5.2 11 9.3 9.3 0 0 1 9 3.6'/%3E%3C/svg%3E");
    $icon-fullscreen: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23163A5C' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5'/%3E%3C/svg%3E");
    $icon-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3.5' y='5' width='17' height='14' rx='1'/%3E%3Ccircle cx='9' cy='10' r='1.6'/%3E%3Cpath d='M4 17l5-5 4 4 2.5-2.5L20 18'/%3E%3C/svg%3E");

    .el-markdown {
        font-size: var(--fs-text);
        line-height: 1.6;
        color: var(--c-ink-body);

        :deep(p) {
            margin: 0 0 1.6rem;
        }

        :deep(h2),
        :deep(h3) {
            margin: 2.4rem 0 0.8rem;
            font-weight: 400;
            font-size: 1.3rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: #3A4254;
        }

        :deep(blockquote) {
            margin: 2rem 0;
            padding: 0.4rem 0 0.4rem 1.6rem;
            border-left: 3px double var(--c-ink);
            font-style: italic;
            font-size: 2rem;
            color: var(--c-marine);
        }

        :deep(ul),
        :deep(ol) {
            margin: 0 0 1.6rem 2.2rem;
        }

        // Only the images in the HTML; a gallery or plugin styles its own
        .segment :deep(img) {
            display: block;
            max-width: 100%;
            margin: 1.6rem 0;
            border: 1px solid var(--c-frame);
            padding: 0.8rem;
            background: var(--c-plate);
        }

        .segment :deep(.zoomable) {
            position: relative;
            display: block;
            max-width: 100%;
            margin: 1.6rem 0;
            padding: 0;
            border: 0;
            background: none;
            cursor: zoom-in;

            img {
                margin: 0;
            }

            // The same fullscreen icon as el-figure, drawn with CSS because the button is plain HTML
            &::after {
                content: "";
                position: absolute;
                right: 1.6rem;
                bottom: 1.6rem;
                width: 4.4rem;
                height: 4.4rem;
                border: 1px solid var(--c-marine);
                border-radius: 4px;
                background: $icon-fullscreen center / 2rem no-repeat, rgba(251, 248, 241, 0.92);
            }
        }

        .segment :deep(.figure) {
            margin: 1.6rem 0;

            .zoomable {
                margin: 0;
            }

            figcaption {
                margin-top: 0.8rem;
                font-size: 1.4rem;
                line-height: 1.4;
                font-style: italic;
                color: var(--c-ink-soft);
            }
        }

        :deep(a) {
            color: var(--c-link);
            text-decoration-thickness: 1px;
            text-underline-offset: 3px;
        }

        :deep(a[data-kind])::after {
            content: "";
            display: inline-block;
            width: 1.4rem;
            height: 1.4rem;
            margin-left: 0.3rem;
            vertical-align: -0.15rem;
            background: currentColor;
            mask: $icon-external center / contain no-repeat;
        }

        :deep(a[data-kind="person"])::after {
            mask-image: $icon-person;
        }

        :deep(a[data-kind="specimen"]) {
            font-style: italic;

            &::after {
                mask-image: $icon-specimen;
            }
        }

        :deep(a[data-kind="media"])::after {
            mask-image: $icon-image;
        }

        :deep(a[data-kind="chapter"])::after,
        :deep(a[data-kind="plugin"])::after,
        :deep(a[data-kind="internal"])::after,
        :deep(a[data-kind="item"])::after,
        :deep(a[data-kind="location"])::after,
        :deep(a[data-kind="expedition"])::after,
        :deep(a[data-kind="article"])::after,
        :deep(a[data-kind="record"])::after {
            display: none;
        }

        :deep(a[is-highlighted]) {
            padding: 0 0.3rem;
            border-radius: 3px;
            background: var(--c-terracotta-soft);
            box-shadow: 0 0 0 2px var(--c-terracotta-soft);
            animation: highlight 2.4s ease;
        }

        &[has-drop-cap] > .segment:first-child :deep(> p:first-child::first-letter) {
            float: left;
            font-family: var(--font-header);
            font-weight: 700;
            font-size: 6rem;
            line-height: 5rem;
            padding: 0.4rem 0.8rem 0 0;
            color: var(--c-marine);
        }
    }

    @keyframes highlight {
        0%,
        40% {
            background: var(--c-terracotta-light);
            box-shadow: 0 0 0 4px var(--c-terracotta-light);
        }
    }
</style>
