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
        // A record href to its image, for the credit and license under images in the body
        lookupImage : {
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
    // How long the highlighted link is kept in view while images above it load
    const SETTLE_MS = 4000;
    // Any of these means the reader takes over, so we stop scrolling for them
    const READER_EVENTS = ['keydown', 'pointerdown', 'touchstart', 'wheel'];

    const root = ref(null);
    const zoomedImage = ref(null);
    const segments = computed(() => renderSegments(props.body, {
        lookupImage : props.lookupImage,
        lookupKind : props.lookupKind,
        zoomLabel : t('image_fullscreen')
    }));

    let scrollTimer = null;
    let settleObserver = null;
    let settleTimer = null;

    function highlightLink() {
        clearTimeout(scrollTimer);
        stopSettling();

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
            scrollToLink(link);
            keepInView(link);
        }, SCROLL_DELAY_MS);
    }

    // Images get their height only once they have loaded, which pushes the link
    // down after we scrolled to it. So while the body still grows, scroll again.
    function keepInView(link) {
        stopSettling();
        settleObserver = new ResizeObserver(() => scrollToLink(link));
        settleObserver.observe(root.value);
        settleTimer = setTimeout(stopSettling, SETTLE_MS);

        for (const name of READER_EVENTS) {
            window.addEventListener(name, stopSettling, {
                passive : true
            });
        }
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

    function scrollToLink(link) {
        link.scrollIntoView({
            behavior : 'smooth',
            block : 'center'
        });
    }

    function stopSettling() {
        settleObserver?.disconnect();
        settleObserver = null;
        clearTimeout(settleTimer);

        for (const name of READER_EVENTS) {
            window.removeEventListener(name, stopSettling);
        }
    }

    watch([segments, () => props.highlight], highlightLink, {
        flush : 'post'
    });

    onMounted(highlightLink);

    onBeforeUnmount(() => {
        clearTimeout(scrollTimer);
        stopSettling();
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
    $icon-anchor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='5' r='2'/%3E%3Cpath d='M12 7v13M8.5 10h7M5 13.5a7 7 0 0 0 14 0M5 13.5l-1.5 1.5M5 13.5l1.8 1M19 13.5l1.5 1.5M19 13.5l-1.8 1'/%3E%3C/svg%3E");
    $icon-book: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 4.5h11a2 2 0 0 1 2 2V20H7a2 2 0 0 1-2-2z'/%3E%3Cpath d='M5 18a2 2 0 0 1 2-2h11'/%3E%3Cpath d='M9 8.5h6M9 11.5h4'/%3E%3C/svg%3E");
    $icon-chevron: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 6l6 6-6 6'/%3E%3C/svg%3E");
    $icon-chapter: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17 20H7a3 3 0 0 1-3-3v-1h10v1a3 3 0 0 0 3 3 3 3 0 0 0 3-3V5a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v11'/%3E%3Cpath d='M10 8h6M10 11h4'/%3E%3C/svg%3E");
    $icon-explore: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='5.5'/%3E%3Ccircle cx='12' cy='12' r='1.6'/%3E%3Cpath d='M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4M5.3 5.3l2.8 2.8M15.9 15.9l2.8 2.8M5.3 18.7l2.8-2.8M15.9 8.1l2.8-2.8'/%3E%3C/svg%3E");
    $icon-info: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='8.5'/%3E%3Cpath d='M12 11v5.5'/%3E%3Ccircle cx='12' cy='7.8' r='0.6' fill='black'/%3E%3C/svg%3E");
    $icon-item: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 8l7-4 7 4v8l-7 4-7-4z'/%3E%3Cpath d='M5 8l7 4 7-4M12 12v8'/%3E%3C/svg%3E");
    $icon-location: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z'/%3E%3Ccircle cx='12' cy='10' r='2.3'/%3E%3C/svg%3E");
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

        // :::details in the markdown: a collapsible block
        .segment :deep(.details) {
            margin: 0 0 1.6rem;
            border-top: 1px solid var(--c-rule);
            border-bottom: 1px solid var(--c-rule);

            summary {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                padding: 1rem 0;
                list-style: none;
                cursor: pointer;
                color: var(--c-link);

                &::-webkit-details-marker {
                    display: none;
                }

                &::before {
                    content: "";
                    flex: none;
                    width: 1.6rem;
                    height: 1.6rem;
                    background: currentColor;
                    mask: $icon-chevron center / contain no-repeat;
                    transition: transform 0.2s ease;
                }

                &:hover {
                    color: var(--c-terracotta);
                }
            }

            &[open] summary::before {
                transform: rotate(90deg);
            }

            .details-body {
                padding-bottom: 0.4rem;
            }
        }

        :deep(a) {
            color: var(--c-link);
            text-decoration-thickness: 1px;
            text-underline-offset: 3px;
        }

        // Links within the site (records, chapters, pages) are dotted, links elsewhere solid
        :deep(a[data-internal]) {
            text-decoration-style: dotted;
        }

        // Needed here too: the rule above is more specific than a:hover in _base.scss
        :deep(a:hover) {
            color: var(--c-terracotta);
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

        :deep(a[data-kind="chapter"])::after {
            mask-image: $icon-chapter;
        }

        :deep(a[data-kind="item"])::after {
            mask-image: $icon-item;
        }

        :deep(a[data-kind="page"])::after,
        :deep(a[data-kind="record"])::after {
            mask-image: $icon-info;
        }

        :deep(a[data-kind="plugin"])::after {
            mask-image: $icon-explore;
        }

        :deep(a[data-kind="location"])::after {
            mask-image: $icon-location;
        }

        :deep(a[data-kind="publication"])::after {
            mask-image: $icon-book;
        }

        :deep(a[data-kind="expedition"])::after {
            mask-image: $icon-anchor;
        }

        // An internal link to something unknown gets no icon
        :deep(a[data-kind="internal"])::after {
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
