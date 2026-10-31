// The texts of the game: who is on board, what they say, the badges and the mission cards.
// Facts about the crew come from the chapter Bemanning and the person records; what is playful
// is said by the characters themselves, so it does not read as a fact about the expedition.
export const CREW = {
    weber : {
        name : 'Max Weber',
        role : 'leider van de expeditie',
        record : 'max-weber'
    },
    anna : {
        name : 'Anna Weber-van Bosse',
        role : 'algologe',
        record : 'anna-weber-van-bosse'
    },
    tydeman : {
        name : 'Commandant Tydeman',
        role : 'commandant van de Siboga',
        record : 'gustaaf-frederik-tydeman'
    },
    stoker : {
        name : 'De stoker',
        role : 'onderdeks, bij de ketels',
        emoji : '🔥'
    },
    nierstrasz : {
        name : 'Hugo Nierstrasz',
        role : 'zoöloog',
        record : 'hugo-frederik-nierstrasz'
    },
    versluys : {
        name : 'Jan Versluys',
        role : 'assistent van Weber',
        record : 'jan-versluys'
    },
    huijsmans : {
        name : 'J.W. Huijsmans',
        role : 'tekenaar',
        record : 'jozef-willem-huijsmans'
    },
    schmidt : {
        name : 'Dokter Schmidt',
        role : 'scheepsarts',
        record : 'august-herman-schmidt'
    },
    cat : {
        name : 'De scheepskat',
        role : 'voer echt mee',
        emoji : '🐈'
    },
    cassowary : {
        name : 'De kasuaris',
        role : 'liep echt rond aan boord',
        emoji : '🐦'
    }
};

// Per event a few lines; {name} and the like are filled in. Priority lines skip the waiting time.
export const LINES = {
    welcome : {
        priority : true,
        lines : [
            ['weber', 'Welkom aan boord van de Siboga! Neem het roer, stook de ketel op en vang zoveel mogelijk specimens. Ze drijven overal in zee.']
        ]
    },
    firstCatch : {
        priority : true,
        lines : [
            ['versluys', 'Uw eerste vangst! Ik zet hem meteen in het album.']
        ]
    },
    nameBearer : {
        priority : true,
        lines : [
            ['weber', 'Een naamdrager! Op dit exemplaar is een soort beschreven: wie wil weten wat {name} is, moet dit dier bekijken.']
        ]
    },
    rare : {
        lines : [
            ['weber', 'Een zeldzame vangst: {name}! Daar ben ik blij mee.'],
            ['huijsmans', 'Wat een mooie! Die teken ik straks meteen na.']
        ]
    },
    algae : {
        lines : [
            ['anna', 'Een wier! Wieren zijn mijn vak. Deze gaat mee naar huis.'],
            ['anna', 'Kijk eens wat een kleur. Wieren worden vaak vergeten, maar ik niet.']
        ]
    },
    bump : {
        lines : [
            ['tydeman', 'Land! En wel héél dichtbij. Iets meer afstand houden, graag.'],
            ['tydeman', 'Roer om! Mijn schip is geen strandstoel.'],
            ['schmidt', 'Iedereen nog heel? Mooi, dan ga ik weer verder met het onderzoek.']
        ]
    },
    offCourse : {
        lines : [
            ['tydeman', 'We zijn uit koers. Het kompas wijst naar het dichtstbijzijnde station: {distance} km.']
        ]
    },
    valve : {
        priority : true,
        lines : [
            ['stoker', 'Rustig met die kolen! De veiligheidsklep is eraf gesprongen.'],
            ['stoker', 'Pssst! Daar gaat je stoom. Niet zo hard stoken, dan blijft de klep dicht.']
        ]
    },
    coalHint : {
        priority : true,
        lines : [
            ['stoker', 'Het vuur gaat bijna uit en we varen nog maar langzaam. Schep er kolen op, dan krijgen we weer stoom!'],
            ['stoker', 'De ketel koelt af. Een paar scheppen kolen en we varen weer op volle kracht.']
        ]
    },
    stoking : {
        lines : [
            ['stoker', 'Wij stokers scheppen dag in dag uit kolen in de ketels. Onderweg moest er zestien keer nieuwe kolen geladen worden.']
        ]
    },
    stationPhoto : {
        priority : true,
        lines : [
            ['nierstrasz', 'Station {station}! Van deze plek is een foto uit de expeditie bewaard: {caption}.']
        ]
    },
    station : {
        lines : [
            ['tydeman', 'Station {station}: hier lag de Siboga op {date}.'],
            ['versluys', 'Station {station}. Ik noteer het in het logboek.']
        ]
    },
    missionDone : {
        priority : true,
        lines : [
            ['{giver}', 'Prachtig, precies wat ik zocht! Dat levert dubbele punten op.']
        ]
    },
    milestone : {
        priority : true,
        lines : [
            ['weber', 'Al {count} specimens! De musea zullen er blij mee zijn.']
        ]
    },
    idle : {
        lines : [
            ['cat', 'Miauw. (Er voer echt een scheepskat mee op de Siboga.)'],
            ['cassowary', 'De kasuaris kijkt je strak aan. (Er liep echt een kasuaris rond aan boord.)']
        ]
    }
};

export const ACHIEVEMENTS = [
    {
        id : 'first',
        title : 'Eerste vangst',
        text : 'Je eerste specimen.'
    },
    {
        id : 'catch10',
        title : 'Tien in het net',
        text : '10 specimens verzameld.'
    },
    {
        id : 'catch50',
        title : 'Volle emmer',
        text : '50 specimens verzameld.'
    },
    {
        id : 'catch100',
        title : 'Honderdtal',
        text : '100 specimens verzameld.'
    },
    {
        id : 'nameBearer',
        title : 'Naamgever',
        text : 'Je eerste naamdrager.'
    },
    {
        id : 'allRarities',
        title : 'Van alles wat',
        text : 'Een specimen van elke klasse: gewoon, ongewoon, zeldzaam en naamdrager.'
    },
    {
        id : 'groups5',
        title : 'Veelzijdig',
        text : 'Specimens uit 5 groepen.'
    },
    {
        id : 'groups10',
        title : 'Natuurkenner',
        text : 'Specimens uit 10 groepen.'
    },
    {
        id : 'algae10',
        title : 'Wierenkoningin',
        text : '10 wieren verzameld. Anna Weber-van Bosse is trots op je.'
    },
    {
        id : 'equator',
        title : 'Gedoopt',
        text : 'De evenaar overgestoken. Neptunus heeft je gedoopt.'
    },
    {
        id : 'stations10',
        title : 'Stationschef',
        text : '10 stations bezocht.'
    },
    {
        id : 'stations50',
        title : 'Routevaarder',
        text : '50 stations bezocht.'
    },
    {
        id : 'discovered25',
        title : 'Ontdekker',
        text : 'Een kwart van de zee ontdekt.'
    },
    {
        id : 'discovered50',
        title : 'Cartograaf',
        text : 'De helft van de zee ontdekt.'
    },
    {
        id : 'stoker',
        title : 'Stoker',
        text : '100 scheppen kolen in de ketel.'
    },
    {
        id : 'valve',
        title : 'Klepje eraf',
        text : 'De veiligheidsklep laten springen.'
    },
    {
        id : 'beachcomber',
        title : 'Strandjutter',
        text : 'Tien keer tegen de kust gevaren.'
    },
    {
        id : 'mission1',
        title : 'Opdracht volbracht',
        text : 'Je eerste missie.'
    },
    {
        id : 'mission5',
        title : 'Betrouwbaar',
        text : '5 missies volbracht.'
    },
    {
        id : 'mission10',
        title : 'Rechterhand',
        text : '10 missies volbracht.'
    }
];

export const RARITY_PHRASES = {
    common : 'een specimen',
    uncommon : 'een ongewoon specimen',
    rare : 'een zeldzaam specimen',
    nameBearer : 'een naamdrager'
};

export const MISSION_TEMPLATES = [
    'In {sea} drijft {rarity} uit de groep {group}. Haal je het voor me op?',
    'Ik heb gehoord dat er {rarity} uit de groep {group} drijft, in {sea}. Vaar je erheen?',
    'Wie vindt {rarity} uit de groep {group}? Zoek in {sea}, binnen de stippellijn.'
];

// Fills {key} in a text with the values
export function fill(text, values) {
    return text.replace(/\{(\w+)\}/g, (match, key) => values[key] ?? match);
}
