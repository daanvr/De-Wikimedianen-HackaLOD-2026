// Stops the browser from zooming the page while a full screen view such as the data visualisation or
// the game is open, so nobody zooms the controls off screen. The map and the game still zoom themselves;
// only the page zoom of the browser (pinch, Ctrl/Cmd + wheel or trackpad, Ctrl/Cmd + plus, minus or 0)
// is held back, and only for as long as such a view is mounted.
import { onBeforeUnmount, onMounted } from 'vue';

const ZOOM_KEYS = new Set(['+', '=', '-', '_', '0']);
const LOCKED_VIEWPORT = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';

let users = 0;
let savedViewport = null;
let savedTouchAction = '';

function onGesture(event) {
    // Safari: pinch on iOS and on a Mac trackpad
    event.preventDefault();
}

function onKey(event) {
    if ((event.ctrlKey || event.metaKey) && ZOOM_KEYS.has(event.key)) {
        event.preventDefault();
    }
}

function onTouchMove(event) {
    // Two fingers on the page itself; the map handles its own pinch before this
    if (event.touches.length > 1) {
        event.preventDefault();
    }
}

function onWheel(event) {
    // A trackpad pinch arrives as a wheel event with ctrlKey
    if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
    }
}

function lock() {
    const meta = document.querySelector('meta[name="viewport"]');

    if (meta) {
        savedViewport = meta.getAttribute('content');
        meta.setAttribute('content', LOCKED_VIEWPORT);
    }

    // No pinch or double-tap zoom, but scrolling (the dive) and swiping (the timeline) still work
    savedTouchAction = document.documentElement.style.touchAction;
    document.documentElement.style.touchAction = 'pan-x pan-y';
    document.addEventListener('gesturestart', onGesture, { passive : false });
    document.addEventListener('gesturechange', onGesture, { passive : false });
    document.addEventListener('touchmove', onTouchMove, { passive : false });
    document.addEventListener('wheel', onWheel, { passive : false });
    window.addEventListener('keydown', onKey);
}

function unlock() {
    const meta = document.querySelector('meta[name="viewport"]');

    if (meta && savedViewport !== null) {
        meta.setAttribute('content', savedViewport);
    }

    document.documentElement.style.touchAction = savedTouchAction;
    document.removeEventListener('gesturestart', onGesture);
    document.removeEventListener('gesturechange', onGesture);
    document.removeEventListener('touchmove', onTouchMove);
    document.removeEventListener('wheel', onWheel);
    window.removeEventListener('keydown', onKey);
}

// Call in the setup of a full screen view: browser zoom is off while the view is mounted
export function usePreventZoom() {
    onMounted(() => {
        users += 1;

        if (users === 1) {
            lock();
        }
    });

    onBeforeUnmount(() => {
        users -= 1;

        if (users === 0) {
            unlock();
        }
    });
}
