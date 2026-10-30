<script setup>
    import { inject } from 'vue';
    import { formatDate } from '@/services/format.js';

    const t = inject('t');

    const props = defineProps({
        fields : {
            type : Array,
            default : () => []
        }
    });

    function formatValues(field) {
        const values = field.type === 'date' ? field.values.map(formatDate) : field.values;

        return values.filter(Boolean).join(', ');
    }
</script>

<template>
    <dl
        v-if="fields.length"
        class="el-fields">
        <div
            v-for="field in fields"
            v-bind:key="field.key"
            class="row">
            <dt class="label">{{ t('field_' + field.key) }}</dt>
            <dd class="value">{{ formatValues(field) }}</dd>
        </div>
    </dl>
</template>

<style lang="scss" scoped>
    .el-fields {
        margin: 1.8rem 0 2.2rem;
        border-top: 1px solid var(--c-ink);
        border-bottom: 1px solid var(--c-ink);
    }

    .row {
        display: flex;
        justify-content: space-between;
        gap: 1.2rem;
        padding: 0.8rem 0;
        border-bottom: 1px solid var(--c-rule);
        font-size: 1.6rem;

        &:last-child {
            border-bottom: 0;
        }
    }

    .label {
        flex-shrink: 0;
        padding-top: 0.3rem;
        font-family: var(--font-header);
        font-size: 1.2rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--c-ink-soft);
    }

    .value {
        text-align: right;
    }
</style>
