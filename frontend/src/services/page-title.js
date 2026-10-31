import { chapterHeading } from '@/services/format.js';

// The title of a view without the site name: the same text as its heading.
// Null for the home screen and for items that don't exist (yet).
function viewTitle(route, store, t) {
    const id = route.params.id;

    if (route.name === 'chapter') {
        const chapter = store.chapterById(id);

        return chapter ? chapterHeading(chapter) : null;
    }

    if (route.name === 'record') {
        const record = store.records[id];

        return record ? record.label || record.title : null;
    }

    if (route.name === 'page') {
        return store.pages[id]?.title ?? null;
    }

    if (route.name === 'plugin') {
        return store.plugins[id]?.title ?? null;
    }

    const keys = {
        chapters : 'chapters',
        library : 'library',
        map : 'explore_mode'
    };

    return keys[route.name] ? t(keys[route.name]) : null;
}

// The text for document.title, for example "Anna Weber-van Bosse · De Siboga-Expeditie"
export function pageTitle(route, store, t) {
    const site = t('site_title');
    const title = viewTitle(route, store, t);

    return title ? `${title} · ${site}` : site;
}
