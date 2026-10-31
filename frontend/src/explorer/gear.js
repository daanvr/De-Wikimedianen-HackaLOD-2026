// The gear of the Siboga, drawn as in the dive prototype, with an explanation and an archive photo.
import dregPhoto from './media/dreg.jpg';
import korPhoto from './media/kor.jpg';
import laboratoryPhoto from './media/laboratorium.jpg';

export const PHOTO_CREDIT = 'Foto: Hugo Frederik Nierstrasz, 1899–1900. Bijzondere Collecties, Universiteit van Amsterdam. Publiek domein.';

// Where the gear goes: over the bottom, hauled up through the water, towed near the surface or by hand
export const GEAR = {
    kor : {
        name : 'Kor',
        en : 'trawl',
        place : 'bottom',
        text : 'Een net in een ijzeren raam met twee sleden. De kor werd over de bodem gesleept en schepte op wat daar leefde: vissen, garnalen, zeesterren, schelpen. Diepzee-kornetten gingen aan kilometers staaldraad naar beneden.',
        photo : korPhoto,
        caption : 'Bovenkomen der kor (korboom gebroken).'
    },
    dreg : {
        name : 'Dreg',
        en : 'dredge',
        place : 'bottom',
        text : 'Een zwaar ijzeren raam met een zak. De dreg schraapte over de bodem en haalde modder, zand en stenen naar boven, met alles wat erin leefde. Aan de dreg hingen dikke zwabbers die fijne dieren in hun vezels vasthielden.',
        photo : dregPhoto,
        caption : 'Uitbrengen der dreg. Onder de zak hangen de zwabbers.'
    },
    hensen : {
        name : 'Hensen-net',
        en : 'Hensen vertical net',
        place : 'middle',
        text : 'Een fijnmazig trechternet, genoemd naar Victor Hensen. Het werd tot een bepaalde diepte gezakt en dan recht omhoog gehaald. Zo kon je tellen hoeveel plankton er in een waterkolom zat.',
        photo : null
    },
    fowler : {
        name : 'Sluitnet (Fowler)',
        en : 'Fowler closing net',
        place : 'middle',
        text : 'Een net dat op diepte open en weer dicht kan. Zo weet je uit welke waterlaag de vangst komt, en niet alleen dat hij ergens tussen de bodem en het oppervlak zat.',
        photo : null
    },
    sleepnet : {
        name : 'Sleepnet',
        en : 'townet',
        place : 'surface',
        text : 'Een klein fijnmazig net dat langzaam vlak onder het oppervlak achter het schip werd gesleept. Het ving plankton, larven en kwallen.',
        photo : null
    },
    cilinder : {
        name : 'Horizontale cilinder',
        en : 'horizontal cylinder',
        place : 'surface',
        text : 'Een cilindervormig net dat langere tijd horizontaal werd voortgesleept, soms uren of tientallen mijlen lang.',
        photo : null
    },
    rif : {
        name : 'Rif en strand',
        en : 'reef- and shore-exploration',
        place : 'hand',
        text : 'Bij ondiep water en op het strand werd met de hand verzameld, vanuit sloepen en soms duikend. Hier haalde Anna Weber-van Bosse een groot deel van haar wieren.',
        photo : laboratoryPhoto,
        caption : 'Het laboratorium aan boord, waar de vangst werd uitgezocht.'
    }
};

function dredgeMops() {
    return Array.from({ length : 14 }, (_, i) => {
        const x = 66 + i * 8;
        const length = 22 + ((i * 7) % 5) * 4;

        return `<path d="M${x} 80 q-4 ${length / 3} 0 ${length * 2 / 3} q3 ${length / 6} -1 ${length / 3}"/>`;
    }).join('');
}

const HENSEN_SVG = `
    <path d="M50 0 L14 40 M50 0 L86 40 M50 0 V40" stroke="#2A2620" stroke-width="1.1"/>
    <path d="M14 42 L86 42 L78 80 L22 80 Z" fill="#EDE3CB" stroke="#2A2620" stroke-width="1.1"/>
    <path d="M22 80 L78 80 L58 190 L42 190 Z" fill="#E8F0EA" opacity="0.55"/>
    <path d="M22 80 L78 80 L58 190 L42 190 Z" fill="url(#explorer-mesh)"/>
    <path d="M22 80 L78 80 L58 190 L42 190 Z" fill="none" stroke="#2A2620" stroke-width="1.1"/>
    <ellipse cx="50" cy="42" rx="37" ry="7" fill="none" stroke="#3B342C" stroke-width="3"/>
    <rect x="40" y="190" width="20" height="26" rx="3" fill="#B9A27A" stroke="#2A2620" stroke-width="1.1"/>`;

// viewBox size and the point where the cable attaches, in viewBox units
export const GEAR_DRAWINGS = {
    kor : {
        width : 240,
        height : 110,
        attach : [0, 40],
        svg : `
            <path d="M40 12 C90 10 150 30 214 48 L232 50 L232 66 L214 66 C150 82 90 98 40 96 Z" fill="#D8C59A" opacity="0.6"/>
            <path d="M40 12 C90 10 150 30 214 48 L232 50 L232 66 L214 66 C150 82 90 98 40 96 Z" fill="url(#explorer-mesh)"/>
            <path d="M40 12 C90 10 150 30 214 48 L232 50 L232 66 L214 66 C150 82 90 98 40 96 Z" fill="none" stroke="#2A2620" stroke-width="1.3"/>
            <path d="M214 44 V70" stroke="#2A2620" stroke-width="3"/>
            <path d="M0 40 L36 12 M0 40 L36 92" stroke="#2A2620" stroke-width="1.4"/>
            <path d="M36 8 V96 M30 8 L72 11" stroke="#3B342C" stroke-width="5" stroke-linecap="round"/>
            <path d="M22 96 C28 106 52 106 78 100" stroke="#3B342C" stroke-width="5" fill="none" stroke-linecap="round"/>`
    },
    dreg : {
        width : 200,
        height : 124,
        attach : [0, 36],
        svg : `
            <path d="M44 10 C100 8 150 20 176 34 C188 44 188 56 176 64 C150 76 100 74 44 68 Z" fill="#B49A6C" opacity="0.65"/>
            <path d="M44 10 C100 8 150 20 176 34 C188 44 188 56 176 64 C150 76 100 74 44 68 Z" fill="url(#explorer-mesh)"/>
            <path d="M44 10 C100 8 150 20 176 34 C188 44 188 56 176 64 C150 76 100 74 44 68 Z" fill="none" stroke="#2A2620" stroke-width="1.3"/>
            <path d="M0 36 L30 14 M0 36 L30 62" stroke="#3B342C" stroke-width="2.4"/>
            <path d="M30 10 L46 5 L46 72 L30 66 Z" fill="#4D453D" stroke="#2A2620" stroke-width="1.2"/>
            <path d="M46 70 L62 80 H172" stroke="#3B342C" stroke-width="2"/>
            <g stroke="#6B5A40" stroke-width="2.2" fill="none" stroke-linecap="round" opacity="0.9">${dredgeMops()}</g>`
    },
    hensen : {
        width : 100,
        height : 230,
        attach : [50, 0],
        svg : HENSEN_SVG
    },
    fowler : {
        width : 100,
        height : 230,
        attach : [50, 0],
        svg : HENSEN_SVG
    },
    sleepnet : {
        width : 160,
        height : 60,
        attach : [0, 30],
        svg : `
            <path d="M0 30 L14 10 M0 30 L14 50" stroke="#2A2620" stroke-width="1"/>
            <path d="M14 10 L140 26 L140 34 L14 50 Z" fill="#E8F0EA" opacity="0.55"/>
            <path d="M14 10 L140 26 L140 34 L14 50 Z" fill="url(#explorer-mesh)"/>
            <path d="M14 10 L140 26 L140 34 L14 50 Z" fill="none" stroke="#2A2620" stroke-width="1"/>
            <ellipse cx="14" cy="30" rx="5" ry="20" fill="none" stroke="#3B342C" stroke-width="2.6"/>
            <rect x="140" y="23" width="16" height="14" rx="2" fill="#B9A27A" stroke="#2A2620" stroke-width="1"/>`
    },
    cilinder : {
        width : 170,
        height : 60,
        attach : [0, 30],
        svg : `
            <path d="M0 30 L12 12 M0 30 L12 48" stroke="#2A2620" stroke-width="1"/>
            <path d="M12 12 H100 L150 26 V34 L100 48 H12 Z" fill="#E8F0EA" opacity="0.55"/>
            <path d="M12 12 H100 L150 26 V34 L100 48 H12 Z" fill="url(#explorer-mesh)"/>
            <path d="M12 12 H100 L150 26 V34 L100 48 H12 Z" fill="none" stroke="#2A2620" stroke-width="1"/>
            <ellipse cx="12" cy="30" rx="5" ry="18" fill="none" stroke="#3B342C" stroke-width="2.6"/>
            <ellipse cx="100" cy="30" rx="4" ry="18" fill="none" stroke="#3B342C" stroke-width="1.6"/>
            <rect x="150" y="23" width="16" height="14" rx="2" fill="#B9A27A" stroke="#2A2620" stroke-width="1"/>`
    }
};

// The gear named in the operations of the station list
export function gearsOf(operations) {
    const text = (operations ?? '').toLowerCase();
    const gears = [];

    if (/trawl/.test(text)) {
        gears.push('kor');
    }

    if (/dredge/.test(text)) {
        gears.push('dreg');
    }

    if (/hensen/.test(text)) {
        gears.push('hensen');
    }

    if (/fowler/.test(text)) {
        gears.push('fowler');
    }

    if (/tow-?\s?net/.test(text)) {
        gears.push('sleepnet');
    }

    if (/cylinder/.test(text)) {
        gears.push('cilinder');
    }

    if (/reef|shore|land-expl|diving/.test(text)) {
        gears.push('rif');
    }

    return gears;
}
