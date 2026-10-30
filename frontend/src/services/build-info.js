// Fills %BUILD_INFO% in a page body with the commits and time of this build.
// __BUILT_AT__ and __CODE_COMMIT__ are set by vite.config.js.
const CODE_REPO = 'https://github.com/daanvr/De-Wikimedianen-HackaLOD-2026';
const CONTENT_REPO = 'https://github.com/hay/siboga-content';
const PLACEHOLDER = '%BUILD_INFO%';
const TIME_ZONE = 'Europe/Amsterdam';

function commitLink(repo, commit) {
    return commit ? `[${commit}](${repo}/commit/${commit})` : '?';
}

export function buildInfo(meta, t) {
    const builtAt = new Date(__BUILT_AT__);
    const date = builtAt.toLocaleDateString('nl-NL', {
        day : 'numeric',
        month : 'long',
        year : 'numeric',
        timeZone : TIME_ZONE
    });
    const time = builtAt.toLocaleTimeString('nl-NL', {
        hour : '2-digit',
        minute : '2-digit',
        timeZone : TIME_ZONE
    });

    return [
        `${t('build_built_at')} ${date}, ${time}`,
        `${t('build_content')} ${commitLink(CONTENT_REPO, meta?.contentCommit)}`,
        `${t('build_code')} ${commitLink(CODE_REPO, __CODE_COMMIT__)}`
    ].join(' · ');
}

export function fillBuildInfo(body, meta, t) {
    if (!body?.includes(PLACEHOLDER)) {
        return body;
    }

    return body.replaceAll(PLACEHOLDER, buildInfo(meta, t));
}
