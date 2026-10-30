import { defineAsyncComponent } from 'vue';

// Every plugin from the content repo (type: plugin) is one component here,
// under the id from its frontmatter. A plugin gets two props: `argument`
// (everything after the # in [[IIIF#argument]], or null) and `fullscreen`.
export const PLUGINS = {
    iiif : defineAsyncComponent(() => import('@/plugins/el-plugin-iiif.vue'))
};

export function pluginComponent(id) {
    return PLUGINS[id] ?? null;
}
