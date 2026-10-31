// Loads the frontend data written by the pipeline (siboga.json + media/).
export const DATA_URL = '/data/siboga.json';
export const MEDIA_BASE = '/data/';
export const SCHEMA_VERSION = 4;

export async function loadFrontendData() {
    const response = await fetch(DATA_URL);

    if (!response.ok) {
        throw new Error(`Could not load ${DATA_URL} (HTTP ${response.status})`);
    }

    const data = await response.json();

    if (data.meta?.schemaVersion !== SCHEMA_VERSION) {
        console.warn(`Expected schemaVersion ${SCHEMA_VERSION}, got ${data.meta?.schemaVersion}`);
    }

    return data;
}

// Paths in siboga.json are relative to the folder that holds siboga.json
export function mediaUrl(src) {
    if (!src) {
        return null;
    }

    if (/^(https?:)?\/\//.test(src) || src.startsWith('/')) {
        return src;
    }

    return MEDIA_BASE + src;
}
