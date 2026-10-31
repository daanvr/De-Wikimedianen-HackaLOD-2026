// Who of the crew says what, and when: at most one line at a time, and ordinary lines not more
// often than once in a while, so the guides help without talking all the time.
import { mediaUrl } from '@/services/data.js';
import { CREW, LINES, fill } from './texts.js';

const COOLDOWN_MS = 20000;

export function createCrew(records) {
    const turns = new Map();
    let lastSaid = -Infinity;
    let counter = 0;

    function person(id) {
        const crew = CREW[id] ?? CREW.weber;
        const record = crew.record ? records?.[crew.record] : null;

        return {
            ...crew,
            portrait : record?.image ? mediaUrl(record.image.thumb ?? record.image.src) : null
        };
    }

    // A line for an event, or null when it is too soon after the last one
    function say(event, values = {}, extra = {}) {
        const entry = LINES[event];
        const now = performance.now();

        if (!entry || (!entry.priority && now - lastSaid < COOLDOWN_MS)) {
            return null;
        }

        const turn = turns.get(event) ?? 0;
        const [who, text] = entry.lines[turn % entry.lines.length];
        const speaker = who === '{giver}' ? values.giver ?? 'weber' : who;

        turns.set(event, turn + 1);
        lastSaid = now;
        counter++;

        return {
            id : counter,
            ...person(speaker),
            text : fill(text, values),
            ...extra
        };
    }

    return {
        person,
        say
    };
}
