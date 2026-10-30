import { Marked } from 'marked';
import { mediaUrl } from '@/services/data.js';

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
}

// Renders a body from siboga.json. Internal links ("/records/anna-weber") get
// data-internal and data-kind, so el-markdown can route them and show an icon.
export function renderMarkdown(body, lookupKind) {
    if (!body) {
        return '';
    }

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

    return marked.parse(body);
}
