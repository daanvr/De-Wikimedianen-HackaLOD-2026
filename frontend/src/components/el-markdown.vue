<script setup>
    import { computed } from 'vue';
    import { useRouter } from 'vue-router';
    import { renderMarkdown } from '@/services/markdown.js';

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
        }
    });

    const html = computed(() => renderMarkdown(props.body, props.lookupKind));

    function onClick(event) {
        const link = event.target.closest('a[data-internal]');

        if (!link || event.metaKey || event.ctrlKey || event.shiftKey) {
            return;
        }

        event.preventDefault();
        router.push(link.getAttribute('href'));
    }
</script>

<template>
    <div
        class="el-markdown"
        v-bind:has-drop-cap="dropCap ? '' : null"
        v-on:click="onClick"
        v-html="html"></div>
</template>

<style lang="scss" scoped>
    $icon-person: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round'%3E%3Ccircle cx='12' cy='8' r='3.5'/%3E%3Cpath d='M5 20c0-4 3.1-6.5 7-6.5s7 2.5 7 6.5'/%3E%3C/svg%3E");
    $icon-external: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5'/%3E%3C/svg%3E");
    $icon-specimen: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round'%3E%3Cpath d='M12 12.5a1.2 1.2 0 1 1 1.2 1.2A2.6 2.6 0 0 1 10.6 11a4 4 0 0 1 4-4 5.3 5.3 0 0 1 5.3 5.3 6.7 6.7 0 0 1-6.7 6.7A8 8 0 0 1 5.2 11 9.3 9.3 0 0 1 9 3.6'/%3E%3C/svg%3E");
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

        :deep(img) {
            display: block;
            max-width: 100%;
            margin: 1.6rem 0;
            border: 1px solid var(--c-frame);
            padding: 0.8rem;
            background: var(--c-plate);
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
        :deep(a[data-kind="internal"])::after,
        :deep(a[data-kind="item"])::after,
        :deep(a[data-kind="location"])::after,
        :deep(a[data-kind="expedition"])::after,
        :deep(a[data-kind="article"])::after,
        :deep(a[data-kind="record"])::after {
            display: none;
        }

        &[has-drop-cap] :deep(> p:first-child::first-letter) {
            float: left;
            font-family: var(--font-header);
            font-weight: 700;
            font-size: 6rem;
            line-height: 5rem;
            padding: 0.4rem 0.8rem 0 0;
            color: var(--c-marine);
        }
    }
</style>
