// How rare a specimen is in the game, after the gold set itself: a species with many specimens
// is common, one of a kind is rare, and the specimens a species was described on bear the name.
// Roughly 55% common, 27% uncommon, 12% rare and 6% name bearers.
export const RARITIES = {
    common : {
        label : 'Gewoon',
        points : 1,
        color : '#FBF8F1'
    },
    uncommon : {
        label : 'Ongewoon',
        points : 3,
        color : '#3F7A5C'
    },
    rare : {
        label : 'Zeldzaam',
        points : 10,
        color : '#1F5A84'
    },
    nameBearer : {
        label : 'Naamdrager',
        points : 50,
        color : '#B8862E'
    }
};

export const RARITY_ORDER = ['common', 'uncommon', 'rare', 'nameBearer'];

// Groups with fewer specimens than this make every specimen in them rare
const SMALL_GROUP = 20;
// Species with this many specimens or more are common
const COMMON_SPECIES = 5;

export function assignRarities(specimens) {
    const species = new Map();
    const groups = new Map();

    for (const specimen of specimens) {
        species.set(specimen.name, (species.get(specimen.name) ?? 0) + 1);
        groups.set(specimen.group, (groups.get(specimen.group) ?? 0) + 1);
    }

    for (const specimen of specimens) {
        const count = specimen.name ? species.get(specimen.name) : 1;

        if (specimen.typeRank === 1) {
            specimen.rarity = 'nameBearer';
        } else if (specimen.typeRank === 2 || count === 1 || groups.get(specimen.group) < SMALL_GROUP) {
            specimen.rarity = 'rare';
        } else if (count < COMMON_SPECIES) {
            specimen.rarity = 'uncommon';
        } else {
            specimen.rarity = 'common';
        }
    }
}

export function pointsOf(specimen) {
    return RARITIES[specimen.rarity]?.points ?? 1;
}
