// Live source: IIIF images are loaded by the browser from the IIIF server.
// An Image API URL ({identifier}/{region}/{size}/{rotation}/{quality}.{format})
// becomes the info.json of that image, so the viewer can load deep zoom tiles.
// A Presentation API manifest is fetched, and gives one image per canvas.
const IMAGE_API_URL = /^(https?:\/\/.+?)\/(full|square|\d+,\d+,\d+,\d+|pct:[\d.,]+)\/[^/]+\/!?[\d.]+\/(default|color|gray|bitonal|native)\.[a-z]+$/i;

export const MANIFEST_URL = /^https?:\/\/\S+\/manifest(\.json)?$/i;

function asArray(value) {
    if (!value) {
        return [];
    }

    return Array.isArray(value) ? value : [value];
}

// One image per canvas, from a Presentation API 3 or 2 manifest
function manifestImages(manifest) {
    if (manifest.items) {
        return manifest.items.map((canvas) => {
            const body = canvas.items?.[0]?.items?.[0]?.body;
            const service = asArray(body?.service)[0];

            return {
                service : service?.id ?? service?.['@id'] ?? null,
                url : body?.id ?? null
            };
        });
    }

    return (manifest.sequences?.[0]?.canvases ?? []).map((canvas) => {
        const resource = canvas.images?.[0]?.resource;

        return {
            service : asArray(resource?.service)[0]?.['@id'] ?? null,
            url : resource?.['@id'] ?? null
        };
    });
}

// What the viewer opens for one image URL: an info.json URL, or a plain image
function imageTileSource(url) {
    if (/\/info\.json$/i.test(url)) {
        return url;
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

async function manifestTileSources(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Could not load IIIF manifest ${url} (HTTP ${response.status})`);
    }

    const sources = manifestImages(await response.json())
        .map((image) => {
            if (image.service) {
                return `${image.service.replace(/\/$/, '')}/info.json`;
            }

            return image.url ? imageTileSource(image.url) : null;
        })
        .filter(Boolean);

    if (!sources.length) {
        throw new Error(`No image in IIIF manifest ${url}`);
    }

    return sources;
}

// The pages the viewer opens for a URL: one for an image, one per canvas for a manifest
export async function iiifTileSources(url) {
    if (MANIFEST_URL.test(url)) {
        return manifestTileSources(url);
    }

    return [imageTileSource(url)];
}
