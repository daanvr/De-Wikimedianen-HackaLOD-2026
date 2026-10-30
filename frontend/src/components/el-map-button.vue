<script setup>
    import ElIcon from '@/components/el-icon.vue';

    const props = defineProps({
        icon : {
            type : String,
            required : true
        },
        label : {
            type : String,
            required : true
        },
        to : {
            type : [String, Object],
            default : null
        },
        variant : {
            type : String,
            default : 'paper'
        },
        floating : {
            type : Boolean,
            default : true
        }
    });

    const emit = defineEmits(['click']);
</script>

<template>
    <router-link
        v-if="to"
        class="el-map-button"
        v-bind:to="to"
        v-bind:aria-label="label"
        v-bind:title="label"
        v-bind:variant="variant"
        v-bind:is-floating="floating ? '' : null">
        <el-icon v-bind:name="icon" />
    </router-link>

    <button
        v-else
        type="button"
        class="el-map-button"
        v-bind:aria-label="label"
        v-bind:title="label"
        v-bind:variant="variant"
        v-bind:is-floating="floating ? '' : null"
        v-on:click="emit('click', $event)">
        <el-icon v-bind:name="icon" />
    </button>
</template>

<style lang="scss" scoped>
    .el-map-button {
        width: 4.8rem;
        height: 4.8rem;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        cursor: pointer;
        pointer-events: auto;
        transition: transform 0.15s ease;

        &:active {
            transform: scale(0.96);
        }

        &[variant="paper"] {
            background: var(--c-paper);
            color: var(--c-marine);
            border: 1px solid var(--c-marine);
            box-shadow: inset 0 0 0 3px var(--c-paper), inset 0 0 0 4px #D8CFBB;

            &[is-floating] {
                box-shadow: inset 0 0 0 3px var(--c-paper), inset 0 0 0 4px #D8CFBB, var(--shadow-float);
            }
        }

        &[variant="terracotta"] {
            background: var(--c-terracotta);
            color: var(--c-paper);
            box-shadow: inset 0 0 0 3px var(--c-terracotta), inset 0 0 0 4px rgba(251, 248, 241, 0.5);

            &[is-floating] {
                box-shadow: inset 0 0 0 3px var(--c-terracotta), inset 0 0 0 4px rgba(251, 248, 241, 0.5), var(--shadow-float);
            }

            &:hover {
                background: var(--c-terracotta-dark);
                box-shadow: inset 0 0 0 3px var(--c-terracotta-dark), inset 0 0 0 4px rgba(251, 248, 241, 0.5), var(--shadow-float);
            }
        }
    }
</style>
