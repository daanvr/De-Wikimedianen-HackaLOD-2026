import { Marked, Parser } from 'marked';
import { mediaUrl } from '@/services/data.js';
import { MANIFEST_URL } from '@/services/iiif.js';

// :::details Summary ... ::: (not indented) is a collapsible block. Its closing
// ::: is the first one that doesn't close a ::: block nested inside it.
const DETAILS_OPEN = /^:::[ \t]*details\b[ \t]*(.*)$/;
const DETAILS_START = /^:::[ \t]*details\b/m;
const FENCE_CLOSE = /^:::[ \t]*$/;
const FENCE_OPEN = /^:::[ \t]*\S/;

// ::: gallery ... ::: (not indented). Without the closing ::: it is no gallery,
// and the images inside are shown as ordinary images.
const GALLERY = /^:::[ \t]*gallery[ \t]*\n([\s\S]*?)\n:::[ \t]*(?:\n+|$)/;
const GALLERY_START = /^:::[ \t]*gallery/m;
// An image this wide or less (in px) is an icon in the text, without the zoom button
const ICON_MAX_WIDTH = 32;
// "alt|14" or "alt|300x200": the Obsidian size the pipeline keeps in the alt text
const IMAGE_SIZE = /^(.*?)\|(\d+)(?:x(\d+))?$/;
const PLUGIN_HREF = /^\/plugins\/([^/?#]+)(?:\?([^#]*))?/;
const RECORD_HREF = /^\/records\//;

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
}

// The alt text of an image and its size from Obsidian, if any
function imageSize(text) {
    const match = (text || '').match(IMAGE_SIZE);

    if (!match) {
        return {
            alt : text || '',
            width : null,
            height : null
        };
    }

    return {
        alt : match[1].trim(),
        width : Number(match[2]),
        height : match[3] ? Number(match[3]) : null
    };
}

// The first link to a record in a list of inline tokens, also inside italics
function recordLink(tokens) {
    for (const token of tokens ?? []) {
        if (token.type === 'link' && RECORD_HREF.test(token.href)) {
            return token;
        }

        const link = recordLink(token.tokens);

        if (link) {
            return link;
        }
    }

    return null;
}

// Credit and license of an image, taken from the record its caption links to,
// so they are always shown with the image. Empty if there is no such record.
function creditHtml(captionTokens, lookupImage) {
    const link = recordLink(captionTokens);
    const image = link && lookupImage ? lookupImage(link.href) : null;

    if (!image?.license) {
        return '';
    }

    const license = image.licenseUrl
        ? `<a href="${escapeHtml(image.licenseUrl)}" target="_blank" rel="noopener">${escapeHtml(image.license)}</a>`
        : escapeHtml(image.license);
    const credit = image.credit ? `${escapeHtml(image.credit)} · ` : '';

    return `<span class="image-credit">${credit}${license}</span>`;
}

// The inline tokens of a paragraph without line breaks and whitespace
function contentTokens(tokens) {
    return tokens.filter((child) => child.type !== 'br' && (child.type !== 'text' || child.text.trim()));
}

// An image, optionally with an italic line directly below it as its caption:
//     ![Siboga at anchor](image1.jpg)
//     *Hr.Ms. Siboga, 1898. [Source](https://...)*
function figureTokens(token) {
    if (token.type !== 'paragraph') {
        return null;
    }

    const [image, caption, ...rest] = contentTokens(token.tokens);

    if (image?.type !== 'image' || rest.length || (caption && caption.type !== 'em')) {
        return null;
    }

    return {
        image,
        caption : caption ?? null
    };
}

// The lines of the ::: block at the start of src, including its opening and
// closing line, or null if it isn't closed
function fencedLines(src) {
    const lines = src.split('\n');
    let depth = 0;

    for (const [index, line] of lines.entries()) {
        if (FENCE_CLOSE.test(line)) {
            depth -= 1;
        } else if (FENCE_OPEN.test(line)) {
            depth += 1;
        }

        if (depth === 0) {
            return lines.slice(0, index + 1);
        }
    }

    return null;
}

const detailsExtension = {
    name : 'details',
    level : 'block',
    start(src) {
        return src.match(DETAILS_START)?.index;
    },
    tokenizer(src) {
        const opening = DETAILS_OPEN.exec(src.split('\n', 1)[0]);
        const lines = opening ? fencedLines(src) : null;

        if (!lines) {
            return undefined;
        }

        const block = lines.join('\n');
        const token = {
            type : 'details',
            raw : block + src.slice(block.length).match(/^\n*/)[0],
            summary : this.lexer.inlineTokens(opening[1].trim()),
            tokens : []
        };

        this.lexer.blockTokens(lines.slice(1, -1).join('\n'), token.tokens);

        return token;
    },
    // Without a summary the browser shows its own label
    renderer(token) {
        const summary = token.summary.length ? `<summary>${this.parser.parseInline(token.summary)}</summary>` : '';

        return `<details class="details">${summary}<div class="details-body">${this.parser.parse(token.tokens)}</div></details>\n`;
    }
};

const galleryExtension = {
    name : 'gallery',
    level : 'block',
    start(src) {
        return src.match(GALLERY_START)?.index;
    },
    tokenizer(src) {
        const match = GALLERY.exec(src);

        if (!match) {
            return undefined;
        }

        const token = {
            type : 'gallery',
            raw : match[0],
            tokens : []
        };

        this.lexer.blockTokens(match[1], token.tokens);

        return token;
    },
    // Only used if a gallery is rendered as HTML after all: then it shows its images
    renderer(token) {
        return this.parser.parse(token.tokens);
    }
};

// Internal links ("/records/anna-weber") get data-internal and data-kind, so
// el-markdown can route them and show an icon. Images are wrapped in a button
// (data-zoom) that el-markdown opens fullscreen, and an image with a caption
// becomes a <figure>, with the credit and license from lookupImage.
function createMarked({ lookupImage, lookupKind, zoomLabel }) {
    const marked = new Marked({
        gfm : true,
        breaks : false
    });

    marked.use({
        extensions : [detailsExtension, galleryExtension],
        renderer : {
            image({ href, title, text }) {
                const src = escapeHtml(mediaUrl(href));
                const { alt, width, height } = imageSize(text);
                const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
                const sizeAttr = (width ? ` width="${width}"` : '') + (height ? ` height="${height}"` : '');

                if (width && width <= ICON_MAX_WIDTH) {
                    return `<img class="icon-image" src="${src}" alt="${escapeHtml(alt)}"${sizeAttr}${titleAttr}>`;
                }

                const label = zoomLabel ? ` aria-label="${escapeHtml(zoomLabel)}"` : '';

                return `<button type="button" class="zoomable" data-zoom${label}><img src="${src}" alt="${escapeHtml(alt)}"${sizeAttr}${titleAttr} loading="lazy"></button>`;
            },
            link({ href, title, tokens }) {
                const text = this.parser.parseInline(tokens);
                const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';

                if (href.startsWith('/')) {
                    const kind = lookupKind ? lookupKind(href) : 'internal';
                    // A term opens its definition in a card instead of going to a page
                    const popup = kind === 'term' ? ' aria-haspopup="dialog"' : '';

                    return `<a href="${escapeHtml(href)}" data-internal data-kind="${kind}"${popup}${titleAttr}>${text}</a>`;
                }

                return `<a href="${escapeHtml(href)}" data-kind="external" target="_blank" rel="noopener"${titleAttr}>${text}</a>`;
            },
            paragraph(token) {
                const figure = figureTokens(token);

                // false: the default renderer makes a normal <p>
                if (!figure?.caption) {
                    return false;
                }

                const image = this.parser.parseInline([figure.image]);
                const caption = this.parser.parseInline(figure.caption.tokens) + creditHtml(figure.caption.tokens, lookupImage);

                return `<figure class="figure">${image}<figcaption>${caption}</figcaption></figure>\n`;
            }
        }
    });

    return marked;
}

// A gallery as a segment: { type : 'gallery', images : [{ src, alt, caption }] },
// where caption is HTML (with credit and license) or null.
function gallerySegment(token, marked, lookupImage) {
    const images = token.tokens.map(figureTokens).filter(Boolean).map(({ image, caption }) => ({
        src : mediaUrl(image.href),
        alt : imageSize(image.text).alt,
        caption : caption ? Parser.parseInline(caption.tokens, marked.defaults) + creditHtml(caption.tokens, lookupImage) : null
    }));

    return images.length ? {
        type : 'gallery',
        images
    } : null;
}

// A paragraph with nothing but a link to a plugin, as the pipeline writes
// [[IIIF#argument]], is shown as the plugin itself. So is a paragraph with
// nothing but the URL of a IIIF manifest, so editors can just paste one.
function pluginSegment(token) {
    if (token.type !== 'paragraph') {
        return null;
    }

    const children = contentTokens(token.tokens);
    const link = children.length === 1 && children[0].type === 'link' ? children[0] : null;

    if (link && MANIFEST_URL.test(link.href)) {
        return {
            type : 'plugin',
            id : 'iiif',
            argument : link.href
        };
    }

    const match = link?.href.match(PLUGIN_HREF);

    if (!match) {
        return null;
    }

    return {
        type : 'plugin',
        id : match[1],
        argument : new URLSearchParams(match[2] ?? '').get('argument')
    };
}

// Renders a body from siboga.json as a list of segments: blocks of HTML
// ({ type : 'html', html }), plugins ({ type : 'plugin', id, argument }) and
// galleries ({ type : 'gallery', images }). Options: lookupKind gives the kind
// of an internal href, lookupImage the image of a record href, and zoomLabel
// is the accessible name of the button around each image.
export function renderSegments(body, options = {}) {
    if (!body) {
        return [];
    }

    const marked = createMarked(options);
    const segments = [];
    let tokens = [];

    function flush() {
        if (tokens.length) {
            segments.push({
                type : 'html',
                html : marked.parser(tokens)
            });
            tokens = [];
        }
    }

    for (const token of marked.lexer(body)) {
        const segment = token.type === 'gallery' ? gallerySegment(token, marked, options.lookupImage) : pluginSegment(token);

        if (segment) {
            flush();
            segments.push(segment);
        } else {
            tokens.push(token);
        }
    }

    flush();

    return segments;
}
