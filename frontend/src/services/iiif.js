// Live source: IIIF images are loaded by the browser from the IIIF server.
// An Image API URL ({identifier}/{region}/{size}/{rotation}/{quality}.{format})
// becomes the info.json of that image, so the viewer can load deep zoom tiles.
// A Presentation API manifest is fetched, and its first image is shown.
const IMAGE_API_URL = /^(https?:\/\/.+?)\/(full|square|\d+,\d+,\d+,\d+|pct:[\d.,]+)\/[^/]+\/!?[\d.]+\/(default|color|gray|bitonal|native)\.[a-z]+$/i;
const MANIFEST_URL = /\/manifest(\.json)?$/i;

function asArray(value) {
    if (!value) {
        return [];
    }

    return Array.isArray(value) ? value : [value];
}

// The image of the first canvas, from a Presentation API 3 or 2 manifest
function firstImage(manifest) {
    const canvas = manifest.items?.[0];

    if (canvas) {
        const body = canvas.items?.[0]?.items?.[0]?.body;

        return {
            service : asArray(body?.service)[0]?.id ?? asArray(body?.service)[0]?.['@id'] ?? null,
            url : body?.id ?? null
        };
    }

    const resource = manifest.sequences?.[0]?.canvases?.[0]?.images?.[0]?.resource;

    return {
        service : asArray(resource?.service)[0]?.['@id'] ?? null,
        url : resource?.['@id'] ?? null
    };
}

async function manifestTileSource(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Could not load IIIF manifest ${url} (HTTP ${response.status})`);
    }

    const image = firstImage(await response.json());

    if (image.service) {
        return `${image.service.replace(/\/$/, '')}/info.json`;
    }

    if (image.url) {
        return iiifTileSource(image.url);
    }

    throw new Error(`No image in IIIF manifest ${url}`);
}

// What the viewer opens for a URL: an info.json URL, or a plain image
export async function iiifTileSource(url) {
    if (/\/info\.json$/i.test(url)) {
        return url;
    }

    if (MANIFEST_URL.test(url)) {
        return manifestTileSource(url);
    }

    const match = url.match(IMAGE_API_URL);

    if (match) {
        return `${match[1]}/info.json`;
    }

    // Not a IIIF Image API URL: show it as one plain image
    return {
        type : 'image',
        url
    };
}
