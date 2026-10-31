// The progress of the game in the browser. The game works without it: in a private window or
// with blocked storage you simply start a new voyage each time.
const KEY = 'siboga-spel-v1';
const SOUND_KEY = 'siboga-spel-geluid';

export function clearProgress() {
    try {
        localStorage.removeItem(KEY);
    } catch (error) {
        console.warn('Could not clear the saved game');
    }
}

export function loadProgress() {
    try {
        const saved = JSON.parse(localStorage.getItem(KEY));

        return saved?.version === 1 ? saved : null;
    } catch (error) {
        return null;
    }
}

export function loadMuted() {
    try {
        return localStorage.getItem(SOUND_KEY) === 'uit';
    } catch (error) {
        return false;
    }
}

export function saveProgress(state) {
    try {
        localStorage.setItem(KEY, JSON.stringify({
            version : 1,
            ...state
        }));
    } catch (error) {
        console.warn('Could not save the game');
    }
}

export function saveMuted(isMuted) {
    try {
        localStorage.setItem(SOUND_KEY, isMuted ? 'uit' : 'aan');
    } catch (error) {
        console.warn('Could not save the sound setting');
    }
}
