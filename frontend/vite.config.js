import { execSync } from 'child_process';
import { fileURLToPath, URL } from 'url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import removeConsole from 'vite-plugin-remove-console';

// Short commit of the code repo, shown on pages with %BUILD_INFO%
function codeCommit() {
    try {
        return execSync('git rev-parse --short HEAD').toString().trim();
    } catch (error) {
        return null;
    }
}

export default defineConfig({
    define : {
        __BUILT_AT__ : JSON.stringify(new Date().toISOString()),
        __CODE_COMMIT__ : JSON.stringify(codeCommit())
    },
    css : {
        preprocessorOptions : {
            scss : {
                api : 'modern-compiler',
                silenceDeprecations : ['import']
            }
        }
    },
    plugins : [
        vue(),
        removeConsole()
    ],
    resolve : {
        alias : {
            '@' : fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server : {
        host : true
    }
});
