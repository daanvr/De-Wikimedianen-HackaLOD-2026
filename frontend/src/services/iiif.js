// Live source: IIIF images are loaded by the browser from the IIIF server.
// An Image API URL ({identifier}/{region}/{size}/{rotation}/{quality}.{format})
// becomes the info.json of that image, so the viewer can load deep zoom tiles.
const IMAGE_API_URL = /^(https?:\/\/.+?)\/(full|square|\d+,\d+,\d+,\d+|pct:[\d.,]+)\/[^/]+\/!?[\d.]+\/(default|color|gray|bitonal|native)\.[a-z]+$/i;

export function iiifTileSource(url) {
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
