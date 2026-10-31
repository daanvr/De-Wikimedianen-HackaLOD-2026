// Icons and habitat per group of the gold dataset (lijsten.groep). The icons
// are stand-ins until there are cut-out photos of the specimens themselves.
export const ICON_PATHS = {
    coral : 'M12 21v-7M12 14l-4-4V6M12 14l4-4V5M8 10L5 8M16 9l3-2M12 17l-3-2',
    crab : 'M7 14a5 3.5 0 1 0 10 0a5 3.5 0 1 0-10 0M7 13L4 9M17 13l3-4M4 9L3 6M4 9l2-3M20 9l1-3M20 9l-2-3M8 17l-2 3M16 17l2 3',
    fish : 'M3 12c3-4 8-5 12-3l4-3v12l-4-3c-4 2-9 1-12-3zM8 11.5h.01',
    foram : 'M12 12a1 1 0 1 0 2 0a3 3 0 1 0-6 0a5 5 0 1 0 10 0a7 7 0 1 0-14 0',
    moss : 'M6 6h4v4H6zM14 6h4v4h-4zM6 14h4v4H6zM14 14h4v4h-4zM10 8h4M8 10v4M16 10v4M10 16h4',
    seaweed : 'M12 21c0-5-3-6-3-10s3-5 3-8M12 21c0-4 3-5 3-9s-2-5-1-8M12 21c-1-3-5-4-6-8M12 21c1-3 5-3 6-7',
    shell : 'M4 18c4-1 8-5 9-12 3 3 6 7 7 12zM13 6l-2 12M13 6l3 12',
    sponge : 'M8 4h8l-1 15a3 3 0 0 1-6 0zM10.5 8h.01M13.5 11h.01M11 14h.01',
    star : 'M12 3l2.4 6.2 6.6.3-5.2 4.1 1.8 6.4L12 16.3 6.4 20l1.8-6.4L3 9.5l6.6-.3z',
    unknown : 'M12 12.5a1.2 1.2 0 1 1 1.2 1.2A2.6 2.6 0 0 1 10.6 11a4 4 0 0 1 4-4 5.3 5.3 0 0 1 5.3 5.3 6.7 6.7 0 0 1-6.7 6.7A8 8 0 0 1 5.2 11 9.3 9.3 0 0 1 9 3.6',
    worm : 'M4 16c2-4 4 0 6-4s4 0 6-4 3 1 4 0'
};

const GROUP_ICONS = {
    'Blauwalgen' : 'seaweed',
    'Bruinwieren' : 'seaweed',
    'Chordadieren (vissen, zakpijpen)' : 'fish',
    'Ciliophora' : 'foram',
    'Foraminiferen' : 'foram',
    'Geleedpotigen (kreeften, krabben)' : 'crab',
    'Groenwieren' : 'seaweed',
    'Kelkwormen' : 'worm',
    'Kraagdieren' : 'worm',
    'Mosdiertjes' : 'moss',
    'Neteldieren (koralen, poliepen)' : 'coral',
    'Ringwormen' : 'worm',
    'Roodwieren' : 'seaweed',
    'Snoerwormen' : 'worm',
    'Sponzen' : 'sponge',
    'Spuitwormen' : 'worm',
    'Stekelhuidigen (zee-egels, zeesterren)' : 'star',
    'Weekdieren' : 'shell'
};

// Groups that live on or in the sea floor. Specimens of these groups, caught
// with gear that went over the bottom, are drawn on the bottom. All others get
// a place in the water column that is not known and is chosen at random.
export const BOTTOM_GROUPS = new Set([
    'Bruinwieren',
    'Foraminiferen',
    'Groenwieren',
    'Kelkwormen',
    'Kraagdieren',
    'Mosdiertjes',
    'Neteldieren (koralen, poliepen)',
    'Ringwormen',
    'Roodwieren',
    'Snoerwormen',
    'Sponzen',
    'Spuitwormen',
    'Stekelhuidigen (zee-egels, zeesterren)',
    'Weekdieren'
]);

export function groupIcon(group) {
    return ICON_PATHS[GROUP_ICONS[group] ?? 'unknown'];
}

// Short name of a group, without the examples in brackets
export function groupName(group) {
    return group.replace(/\s*\(.*\)$/, '');
}
