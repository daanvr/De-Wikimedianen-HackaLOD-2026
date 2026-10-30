const MONTHS = [
    'januari',
    'februari',
    'maart',
    'april',
    'mei',
    'juni',
    'juli',
    'augustus',
    'september',
    'oktober',
    'november',
    'december'
];

const ROMAN_NUMERALS = [
    [1000, 'M'],
    [900, 'CM'],
    [500, 'D'],
    [400, 'CD'],
    [100, 'C'],
    [90, 'XC'],
    [50, 'L'],
    [40, 'XL'],
    [10, 'X'],
    [9, 'IX'],
    [5, 'V'],
    [4, 'IV'],
    [1, 'I']
];

// Chapter titles are file names such as "Hoofdstuk 1 - de Siboga vertrekt uit Amsterdam"
export function chapterHeading(chapter) {
    const stripped = chapter.title.replace(/^hoofdstuk\s*\d+\s*[-–:]?\s*/i, '').trim();
    const heading = stripped || chapter.title;

    return heading.charAt(0).toUpperCase() + heading.slice(1);
}

// Formats YYYY, YYYY-MM or YYYY-MM-DD as a Dutch date
export function formatDate(value) {
    if (!value) {
        return '';
    }

    const match = /^(-?\d{1,4})(?:-(\d{2}))?(?:-(\d{2}))?/.exec(value);

    if (!match) {
        return value;
    }

    const [, year, month, day] = match;
    const parts = [];

    if (day) {
        parts.push(String(Number(day)));
    }

    if (month) {
        parts.push(MONTHS[Number(month) - 1]);
    }

    parts.push(year);

    return parts.join(' ');
}

export function toRoman(number) {
    let rest = Number(number);
    let result = '';

    if (!rest || rest < 1) {
        return '';
    }

    for (const [value, numeral] of ROMAN_NUMERALS) {
        while (rest >= value) {
            result += numeral;
            rest -= value;
        }
    }

    return result;
}
