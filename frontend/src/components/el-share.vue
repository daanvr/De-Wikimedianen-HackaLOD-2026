<script setup>
    import { inject, onBeforeUnmount, ref, watch } from 'vue';
    import QRCode from 'qrcode';
    import ElIcon from '@/components/el-icon.vue';
    import ElLightbox from '@/components/el-lightbox.vue';

    const COPIED_MS = 2000;

    const t = inject('t');

    const emit = defineEmits(['close']);

    const props = defineProps({
        url : {
            type : String,
            required : true
        }
    });

    const input = ref(null);
    const isCopied = ref(false);
    const qrCode = ref(null);

    let copiedTimer = null;

    async function copy() {
        try {
            await navigator.clipboard.writeText(props.url);
        } catch (error) {
            // Without clipboard access (http, old browsers) the link is selected for copying by hand
            input.value?.select();
            return;
        }

        isCopied.value = true;
        clearTimeout(copiedTimer);
        copiedTimer = setTimeout(() => {
            isCopied.value = false;
        }, COPIED_MS);
    }

    async function renderQrCode() {
        // Made in the browser, so it also works without internet
        qrCode.value = await QRCode.toDataURL(props.url, {
            margin : 1,
            width : 480,
            color : {
                dark : '#1B2433',
                light : '#FBF8F1'
            }
        });
    }

    watch(() => props.url, renderQrCode, {
        immediate : true
    });

    onBeforeUnmount(() => {
        clearTimeout(copiedTimer);
    });
</script>

<template>
    <el-lightbox v-on:close="emit('close')">
        <section
            class="el-share"
            role="dialog"
            aria-labelledby="share-title">
            <h2
                id="share-title"
                class="title">{{ t('share_title') }}</h2>

            <img
                v-if="qrCode"
                class="qr"
                v-bind:src="qrCode"
                v-bind:alt="t('share_qr')">

            <label
                for="share-url"
                class="kicker label">{{ t('share_link') }}</label>
            <div class="link">
                <input
                    id="share-url"
                    ref="input"
                    class="link__input"
                    type="text"
                    readonly
                    v-bind:value="url"
                    v-on:focus="$event.target.select()">
                <button
                    type="button"
                    class="button button--primary link__button"
                    v-on:click="copy()">
                    <el-icon
                        v-bind:name="isCopied ? 'check' : 'copy'"
                        v-bind:size="18" />
                    {{ isCopied ? t('share_copied') : t('share_copy') }}
                </button>
            </div>
        </section>
    </el-lightbox>
</template>

<style lang="scss" scoped>
    .el-share {
        width: 100%;
        max-width: 42rem;
        padding: 2.4rem;
        background: var(--c-paper);
        border-radius: 10px;
        box-shadow: var(--shadow-card);
    }

    .title {
        margin: 0 0 1.6rem;
        font-weight: 700;
        font-size: 2.4rem;
    }

    .qr {
        display: block;
        width: 100%;
        max-width: 24rem;
        margin: 0 auto 2rem;
        border: 1px solid var(--c-frame);
    }

    .label {
        display: block;
        margin-bottom: 0.6rem;
    }

    .link {
        display: flex;
        gap: 0.8rem;
    }

    .link__input {
        flex: 1;
        min-width: 0;
        height: 5.2rem;
        padding: 0 1.2rem;
        border: 1px solid var(--c-frame);
        border-radius: 3px;
        background: var(--c-plate);
        color: var(--c-ink);
        font-family: var(--font-text);
        font-size: 1.5rem;
    }

    .link__button {
        flex-shrink: 0;
        padding: 0 1.6rem;
    }
</style>
