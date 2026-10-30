import { Marked } from 'marked';
import { mediaUrl } from '@/services/data.js';

const PLUGIN_HREF = /^\/plugins\/([^/?#]+)(?:\?([^#]*))?/;

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
}

// Internal links ("/records/anna-weber") get data-internal and data-kind, so
// el-markdown can route them and show an icon.
function createMarked(lookupKind) {
    const marked = new Marked({
        gfm : true,
        breaks : false
    });

    marked.use({
        renderer : {
            image({ href, title, text }) {
                const src = escapeHtml(mediaUrl(href));
                const alt = escapeHtml(text || '');
                const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';

                return `<img src="${src}" alt="${alt}"${titleAttr} loading="lazy">`;
            },
            link({ href, title, tokens }) {
                const text = this.parser.parseInline(tokens);
                const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';

                if (href.startsWith('/')) {
                    const kind = lookupKind ? lookupKind(href) : 'internal';

                    return `<a href="${escapeHtml(href)}" data-internal data-kind="${kind}"${titleAttr}>${text}</a>`;
                }

                return `<a href="${escapeHtml(href)}" data-kind="external" target="_blank" rel="noopener"${titleAttr}>${text}</a>`;
            }
        }
    });

    return marked;
}

// A paragraph with nothing but a link to a plugin, as the pipeline writes
// [[IIIF#argument]], is shown as the plugin itself.
function pluginEmbed(token) {
    if (token.type !== 'paragraph') {
        return null;
    }

    const children = token.tokens.filter((child) => child.type !== 'text' || child.text.trim());
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
// ({ type : 'html', html }) and plugins ({ type : 'plugin', id, argument }).
export function renderSegments(body, lookupKind) {
    if (!body) {
        return [];
    }

    const marked = createMarked(lookupKind);
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
        const plugin = pluginEmbed(token);

        if (plugin) {
            flush();
            segments.push(plugin);
        } else {
            tokens.push(token);
        }
    }

    flush();

    return segments;
}
