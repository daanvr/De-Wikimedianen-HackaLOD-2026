import { Marked, Parser } from 'marked';
import { mediaUrl } from '@/services/data.js';

// ::: gallery ... ::: (not indented). Without the closing ::: it is no gallery,
// and the images inside are shown as ordinary images.
const GALLERY = /^:::[ \t]*gallery[ \t]*\n([\s\S]*?)\n:::[ \t]*(?:\n+|$)/;
const GALLERY_START = /^:::[ \t]*gallery/m;
const PLUGIN_HREF = /^\/plugins\/([^/?#]+)(?:\?([^#]*))?/;

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
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
// becomes a <figure>.
function createMarked(lookupKind, zoomLabel) {
    const marked = new Marked({
        gfm : true,
        breaks : false
    });

    marked.use({
        extensions : [galleryExtension],
        renderer : {
            image({ href, title, text }) {
                const src = escapeHtml(mediaUrl(href));
                const alt = escapeHtml(text || '');
                const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
                const label = zoomLabel ? ` aria-label="${escapeHtml(zoomLabel)}"` : '';

                return `<button type="button" class="zoomable" data-zoom${label}><img src="${src}" alt="${alt}"${titleAttr} loading="lazy"></button>`;
            },
            link({ href, title, tokens }) {
                const text = this.parser.parseInline(tokens);
                const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';

                if (href.startsWith('/')) {
                    const kind = lookupKind ? lookupKind(href) : 'internal';

                    return `<a href="${escapeHtml(href)}" data-internal data-kind="${kind}"${titleAttr}>${text}</a>`;
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
                const caption = this.parser.parseInline(figure.caption.tokens);

                return `<figure class="figure">${image}<figcaption>${caption}</figcaption></figure>\n`;
            }
        }
    });

    return marked;
}

// A gallery as a segment: { type : 'gallery', images : [{ src, alt, caption }] },
// where caption is HTML or null.
function gallerySegment(token, marked) {
    const images = token.tokens.map(figureTokens).filter(Boolean).map(({ image, caption }) => ({
        src : mediaUrl(image.href),
        alt : image.text || '',
        caption : caption ? Parser.parseInline(caption.tokens, marked.defaults) : null
    }));

    return images.length ? {
        type : 'gallery',
        images
    } : null;
}

// A paragraph with nothing but a link to a plugin, as the pipeline writes
// [[IIIF#argument]], is shown as the plugin itself.
function pluginSegment(token) {
    if (token.type !== 'paragraph') {
        return null;
    }

    const children = contentTokens(token.tokens);
    const match = children.length === 1 && children[0].type === 'link'
        ? children[0].href.match(PLUGIN_HREF)
        : null;

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
// galleries ({ type : 'gallery', images }). zoomLabel is the accessible name
// of the button around each image.
export function renderSegments(body, lookupKind, zoomLabel = null) {
    if (!body) {
        return [];
    }

    const marked = createMarked(lookupKind, zoomLabel);
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
        const segment = token.type === 'gallery' ? gallerySegment(token, marked) : pluginSegment(token);

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
