# Spelmodus: vaar zelf met de Siboga
[Documentatie](README.md) › Spelmodus

De spelmodus (`/spel`) is een spel, los van de [datavisualisatie](ontdekmodus.md). Je stuurt de Siboga zelf over de zee, stookt de ketel op, ontdekt de kaart en verzamelt echte specimens die op een verzonnen maar plausibele plek in het water drijven. Je vindt hem in het menu, onder de streep.

De datavisualisatie laat eerlijk zien wat we zeker weten. Het spel mag speels zijn, maar zegt dat ook: bij de start staat deze disclaimer.

> Dit is een spel, een soort artist impression. De specimens zijn echt: de Siboga heeft ze verzameld en ze liggen nu in een museum. Waar ze in het spel drijven, is verzonnen. We hebben ze zo goed mogelijk in de buurt gelegd van waar de Siboga die dag voer, maar het is geen echte vindplek.

De disclaimer blijft bereikbaar via de i-knop. In het album staat bij elk specimen de echte datum en het echte station of de vindplaats uit het record, naast de opmerking dat de plek in het spel verzonnen is.

## Spelen
- **Stuurwiel** (rechtsonder). Pak het vast en draai; een halve slag is vol roer. Laat je los, dan veert het wiel terug naar het midden, met een klein nadeinen. Met een toetsenbord gaat het met ← en → (of A en D).
- **Ketel** (linksonder). Elke schep kolen geeft stoom, en stoom geeft vaart. De druk zakt vanzelf, maar nooit helemaal: het schip vaart altijd. Blijft de druk te lang in het rood, dan springt de veiligheidsklep en verlies je stoom. Met een toetsenbord gaat het met de spatiebalk of ↑.
- **Land.** Vaar je tegen de kust, dan ketst het schip af en houdt het het grootste deel van zijn vaart. De rand van het onderzoeksgebied werkt net zo.
- **Verzamelen.** Vaar over de specimens die in zee drijven. Dichtbij drijven ze naar het schip toe, en ze vliegen in het netje. Elk specimen telt punten naar zijn zeldzaamheid.
- **Stations.** De stations van de Siboga zijn boeien. Vaar je erlangs, dan luidt de scheepsbel, krijgt het station een stempel in het logboek en drijft de echte vangst van dat station naar je toe.
- **Mist.** De kaart is eerst een oud perkament. Waar je vaart, gaat het open, en wat je ontdekt hebt, blijft open.
- **Kompas.** Ben je ver van elk station, of vang je een tijd niets, dan wijst een kompas naar het dichtstbijzijnde station dat je nog niet bezocht hebt.
- **Missies.** Iemand van de bemanning vraagt om een specimen dat je nog niet hebt, binnen een gestippelde cirkel. Een gevangen missiespecimen telt dubbel. "Andere missie" geeft een nieuwe; in het album zoekt "Zoek er een" een missie voor een groep die je nog mist.
- **Linedoop.** De eerste keer dat je de evenaar oversteekt, komt Neptunus boven met een oorkonde, die je als plaatje kunt bewaren.
- **Album.** Tik op het netje. Daar staan je specimens per groep, de stations als stempels en de insignes.

Het spel heeft geen einde. De doelen zijn het album, de insignes en hoeveel van de zee je ontdekt.

## Welke specimens, en waar
Alle 6.714 specimens uit de [gouden dataset](gouden-dataset.md) doen mee, niet alleen de 183 die zeker aan een station hangen. Elk specimen krijgt een vaste plek (`game/spawn.js`), steeds dezelfde. De eerste bron die er is, bepaalt waar:

| Bron | Aantal | Plek in het spel |
| --- | --- | --- |
| Het specimen hangt aan een station | 183 | Binnen 15 km van het station |
| Het record heeft eigen coördinaten | ongeveer 1.600 | Binnen 15 km van die plek |
| Alleen de datum | de rest | Binnen 60 km van waar de Siboga die dag was |

Waar de Siboga op een dag was, volgt uit de stations: een station van die dag, of een punt op de route tussen het station ervoor en erna, naar rato van de tijd. Valt een plek op land, dan zoekt het spel een andere plek of het dichtstbijzijnde water. Zo is de verdeling vanzelf ongelijk: drukke verzameldagen geven dichte velden, lange oversteken blijven leeg.

## Zeldzaamheid en punten
De zeldzaamheid volgt de dataset zelf (`game/rarity.js`):

| Klasse | Regel | Punten | Aandeel |
| --- | --- | --- | --- |
| Gewoon | Een soort met 5 of meer specimens in de dataset | 1 | 55% |
| Ongewoon | Een soort met 2 tot 4 specimens | 3 | 27% |
| Zeldzaam | Een soort met 1 specimen, een groep met minder dan 20 specimens, of een syntype | 10 | 12% |
| Naamdrager | Holotype, lectotype of neotype (`type_rang` 1) | 50 | 6% |

Op de kaart heeft elk specimen het icoon van zijn groep, met een rand in de kleur van zijn klasse. Zeldzame specimens en naamdragers glinsteren.

## Bemanning
Gidsen uit de bemanning zeggen af en toe iets, met hun portret uit de persoonsrecords: Max Weber, Anna Weber-van Bosse, commandant Tydeman, Hugo Nierstrasz, Jan Versluys, J.W. Huijsmans, dokter Schmidt, een stoker, en de scheepskat en de kasuaris, die echt aan boord waren. Feiten over hen komen uit het hoofdstuk Bemanning en de persoonsrecords. Wat speels is, zeggen de personages zelf, zodat het niet als feit over de expeditie leest. Een gewone regel komt hooguit eens per 20 seconden. De teksten staan in `game/texts.js`.

## Code
Het spel staat los van de rest van de frontend:

```
frontend/src/game/
├── el-game.vue           ← het geheel: de spellus, de staat, de overlays
├── el-game-map.vue       ← eigen MapLibre-kaart: zeekaart, boeien, specimens, mist, schip, rook, kielzog
├── el-game-helm.vue      ← het stuurwiel
├── el-game-boiler.vue    ← manometer, ketelluik en kolenschep
├── el-game-hud.vue       ← netje en score, missiekaartje, kompas, meldingen; de vangst vliegt in het netje
├── el-game-album.vue     ← verzameling, logboek en insignes
├── el-game-intro.vue     ← uitleg en disclaimer
├── el-game-equator.vue   ← linedoop en oorkonde
├── data.js               ← laadt alle specimens met de loaders van de ontdekmodus
├── physics.js            ← het schip: ketel, snelheid, roer en afketsen (een pure step-functie)
├── land.js               ← landmasker (1,5 km per pixel) en een waterrooster van 0,1°
├── fog.js                ← de mist als canvas boven de kaart
├── spawn.js              ← de plek van elk specimen
├── rarity.js             ← zeldzaamheid en punten
├── missions.js           ← missies, met een zoektocht over water of het doel haalbaar is
├── achievements.js       ← wanneer een insigne verdiend is
├── crew.js               ← wie wat zegt, en hoe vaak
├── texts.js              ← de teksten van de bemanning, de insignes en de missies
├── sound.js              ← alle geluiden, gemaakt met Web Audio (geen geluidsbestanden)
└── save.js               ← voortgang in localStorage
```

Van de ontdekmodus gebruikt het spel de loaders (`rows`, `buildSpecimen`, `pointAt` in `explorer/data.js`), het schip (`explorer/boat.js`), de groepicoontjes, het zegel en de specimenpagina (`el-explorer-specimen.vue`). De zeekaart komt uit `services/sea-chart.js`, het detailland uit `store.mapLayers`.

Hoe het werkt:
- **Land.** `land.js` tekent het detailland van de zeekaart één keer op een onzichtbaar canvas en bewaart per pixel of het land is. Botsen en plaatsen kosten daarna één opzoeking. De richting van de kust volgt uit de landpixels rond het punt; daarlangs wordt de koers gespiegeld. Smalle zeestraten van minder dan een paar kilometer kunnen dicht zitten; daarom start het schip op het eerste punt van de route uit Soerabaja met open water rondom.
- **Mist.** Een canvas van ongeveer 3 km per pixel in Web Mercator, als `canvas`-bron in MapLibre, boven de specimens en onder het schip. Het schip veegt het open; het canvas gaat alleen opnieuw naar de kaart als er iets veranderd is.
- **Specimens.** Alleen de specimens binnen 250 km gaan naar de kaart, 12 keer per seconde, met een kleine drift. Iconen worden getekend als de kaart erom vraagt (`styleimagemissing`).
- **Missies.** Een kandidaat ligt 150 tot 400 km verderop, in het water. Een A*-zoektocht over het waterrooster controleert of de route over zee hooguit 1,8 keer zo lang is als de rechte lijn.
- **Opslaan.** Om de 5 seconden en als het tabblad verdwijnt, onder de sleutel `siboga-spel-v1`: schip, vangst, stations, mist (één bit per cel), insignes, missie en tellers. Zonder localStorage werkt het spel ook, alleen zonder geheugen.

### Bijstellen
De getallen die het gevoel bepalen, staan als constanten bovenaan de bestanden:

| Wat | Waar | Nu |
| --- | --- | --- |
| Vaart bij lage en volle druk | `physics.js` `MIN_SPEED`, `MAX_SPEED` | 8 en 45 km per spelseconde |
| Drukverlies, schep, oververhitten | `physics.js` | 5% per s, +12%, 1,2 s boven 92% |
| Draaisnelheid | `physics.js` `TURN_RATE`, `TURN_SPEED` | 50° per s, vanaf 16 km/s |
| Terugveren van het wiel | `el-game-helm.vue` `STIFFNESS`, `DAMPING` | 32 en 8 |
| Vangen en aantrekken | `el-game.vue` `CATCH_KM`, `MAGNET_KM` | 5 en 13 km |
| Stations, kompas | `el-game.vue` `STATION_KM`, `OFF_COURSE_KM` | 14 en 120 km |
| Zicht in de mist | `fog.js` `REVEAL_KM` | 110 km |
| Zoom en kanteling | `el-game-map.vue` `GAME_ZOOM`, `PITCH` | 7,4 en 30° |

In development staat `window.sibogaGame` klaar, met `ship` en `teleport(lon, lat)`, om snel ergens te testen.

## Nog te doen
- Testen en bijstellen op een echte telefoon: het gevoel van het wiel, de vaart en de dichtheid van de specimens.
- Foto's van specimens: nu hebben er 36 een foto, de rest toont het groepicoon.
- De teksten van de bemanning naar de content-repo, als ze vaststaan.
