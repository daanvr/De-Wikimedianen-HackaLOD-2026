# Ontdekmodus
[Documentatie](README.md) › Ontdekmodus

De ontdekmodus (`/map`, in het menu) laat zien waar de Siboga voer, waar ze iets ophaalde en waar dat nu ligt. Je sleept een tijdlijn en het schip vaart mee over de kaart. Bij elk station met vondsten vliegen die het netje in. Tik je op een station, dan vliegt de kaart erheen, kantelt, en duik je de waterkolom in tot op de bodem. Tik je op een specimen, dan zie je wat het is, wie het determineerde en in welk museum het ligt.

Dit document legt uit hoe dat werkt, welke data je ziet, waar die vandaan komt en hoe zeker die is.

## Eerst dit: het is verre van alles
De Siboga verzamelde tienduizenden dieren en planten. Bij GBIF staan ruim 20.000 records die naar de expeditie verwijzen. De ontdekmodus toont er **183**. Dat is bewust: we tonen alleen wat we met de hoogste zekerheid aan een station kunnen koppelen.

| | Aantal |
| --- | --- |
| Siboga-records bij GBIF | ruim 20.000 |
| Zeker van de expeditie ([gouden dataset](gouden-dataset.md)) | 6.714 |
| Daarvan ook zeker van één station | 183 |
| Stations met zulke specimens | 50 (van de 363) |
| Met een foto die we mogen tonen | 36 |
| Stations met een foto op Wikidata | 47 |

Het verschil zit vooral in de records zelf. De meeste noemen geen dagdatum of geen stationnummer, of ze noemen het op een manier die twijfel laat (“possibly Sta. 80”, twee stations, een lettervariant als 225a–h). Die laten we weg. Zo geeft de ontdekmodus een eerlijk beeld van wat we zeker weten, en geen volledig beeld van wat de Siboga vond.

Die keuze kleurt het beeld:
- **Ondiep water.** 46 van de 50 stations liggen ondieper dan 100 meter. Het zijn vaak ankerplaatsen, waar ook aan wal en op het rif verzameld werd. Records van diepzeestations noemen het stationnummer minder vaak op een manier die we zeker kunnen lezen.
- **Wieren en Trondheim.** 133 van de 183 specimens zijn roodwieren, en 140 liggen in Trondheim (NTNU), een collectie die het stationnummer netjes in het record schrijft. Daarna volgen het Natural History Museum in Londen (30) en kleinere collecties.
- **Bodemtuig.** Op alle 50 stations ging er tuig over de bodem (dreg of kor).

## Hoe een specimen aan een station komt
Een specimen hoort bij een station als het museumrecord zelf het stationnummer noemt, samen met “Siboga”, en de datum klopt. Datum of positie alleen is nooit genoeg. De volledige regels staan in [gouden-dataset.md](gouden-dataset.md#hoe-zeker). Bij elk specimen staat het veld en de tekst waaruit de koppeling komt, met het stukje dat de regel raakte gemarkeerd. Zo kan iedereen het nakijken.

## Wat je ziet
- **Kaart.** Alleen de blauwe zeekaart van de site, net als de gewone kaart over de hele wereld: uitzoomen kan tot de hele aarde, buiten het onderzoeksgebied alleen tot ongeveer provincieniveau, met dezelfde zee- en landnamen. Draaien en kantelen kan met twee vingers (of de rechtermuisknop). Staat de kaart gedraaid of schuin, dan verschijnt onder het menu een kompas dat meedraait met het noorden en een beetje mee kantelt; een tik zet de kaart weer recht van boven met het noorden boven. Stations zijn stippen; hoe meer specimens, hoe groter. De vijf stations met de meeste vondsten zijn uitgelicht. Een stippellijn toont de route, en wat al gevaren is, is helderder.
- **Tijdlijn.** Op afstand langs de route: 0,6 pixel per kilometer, dus lange oversteken zijn lange lege stukken. Elke kolom naar beneden is een loding uit 1899, op de plek van het station. De doorlopende lijn is de diepte van de zee van nu. Boven het wateroppervlak staan bolletjes waar specimens vandaan komen, met een sterretje als er een naamdrager bij is. Vaar je erlangs, dan vliegen ze het netje in; vaar je terug, dan vliegen ze eruit. Het pijltje rechts vaart soepel naar het volgende station.
- **Netje.** Telt wat er tot nu toe gevangen is, met een voortgangsbalk. Tik erop voor de vangst per station.
- **Duik.** Overgenomen uit het duikprototype. De kaart vliegt naar het schip en kantelt, de waterlijn komt omhoog en het schip ligt half onder water. Scrollen gaat de diepte in, met dieptemeter, liniaal en zones (zonlicht, schemer, middernacht, diepzeevlakte). Het tuig van het station hangt aan zijn kabel (kor, dreg, Hensen-net, sluitnet, sleepnet, cilinder, of “met de hand” bij rif en strand); tik erop voor uitleg en een archieffoto. Het loodlijntje toont de gelode diepte. Op de bodem staat de bodemnotitie uit 1899, daaronder de vangst van het station, een foto bij het station als die er is, de tekst uit de stationslijst en de bronnen. Omhoog scrollen of “Boven water” brengt je terug; tijdens het opstijgen negeert de kaart je hand, zodat hij altijd recht uitkomt.
- **Specimen.** Foto, naam, familie en groep. Is het een naamdrager, dan staat dat er groot bij, met een zegel. Daarna de reis: gevangen (station en datum), elke determinatie die het record kent, en het museum waar het nu ligt. Links naar GBIF en, voor Naturalis, naar Bioportal.

### Naamdragers
Een specimen waarop een soort beschreven is, alleen (holotype, lectotype, neotype) of samen met andere exemplaren (syntype), krijgt een zegel met een ster: in de tijdlijn, in de waterkolom, in de vangst en op de specimenpagina. In deze selectie zijn dat er 4.

### Geregistreerd: datum, station en verzamelaar
De eerste stap op de specimenpagina heet *Geregistreerd*. Er staat wat het record zegt, zonder het mooier te maken:
- de datum uit `eventDate`;
- het station. Dat is geen veld in het record maar onze afleiding: het nummer staat in de tekst en de datum past. Het bewijs staat onderaan de pagina;
- de verzamelaar uit `recordedBy`, letterlijk zoals het record hem schrijft. Dat kan een persoon zijn, maar ook de expeditie of het schip. Is het veld leeg, dan staat er "onbekend". In deze selectie is het 39 keer leeg en 138 keer "Anna Antoinette Weber-van Bosse scr.";
- de vindplaats uit `locality`.

Wie over een gegeven beweegt of erop tikt, ziet in een tooltip uit welk veld het komt (de Darwin Core-term) en wat het betekent.

### Determinaties
Een specimen kan na de eerste determinatie opnieuw gedetermineerd zijn, soms meer dan eens. De specimenpagina toont daarom zoveel stappen als het record kent: eerst uit de identificatiegeschiedenis van het museum (de GBIF-extensie Identification), anders uit `previousIdentifications`, en altijd de huidige naam als laatste. Herdeterminaties die alleen op het etiket staan, komen uit de gouden dataset. In deze selectie heeft geen enkel record een geschiedenis; de lijst groeit vanzelf mee zodra musea die publiceren.

## De diepte: wat we wel en niet weten
De diepte per station is de **bodemdiepte**, gelood in 1899. Het is niet de diepte waarop een dier gevangen is. Die weten we bijna nooit, en de ontdekmodus wekt die indruk ook niet:
- **Bodem.** Een specimen ligt op de bodem als het tot een groep hoort die op de bodem leeft (wieren, koralen, sponzen, stekelhuidigen, weekdieren, wormen, mosdiertjes) en het station tuig over de bodem gebruikte. Dat geldt voor 170 van de 183.
- **Netbereik.** Een specimen van een netstation met een bekend netbereik zweeft binnen dat bereik. In deze selectie komt dat nog niet voor.
- **Willekeurig.** De rest staat op een willekeurige, vaste plek in de waterkolom, en dat staat er ook bij.

De waterkleur wordt donkerder met de diepte, ongeveer zoals het licht in helder tropisch water afneemt, maar blijft blauw. De schaal is een wortelschaal, zodat een rif van 9 m en een trog van 5 km allebei passen.

## Wat er bij de stations is toegevoegd
De stations komen uit de stationslijst van Fauconnier (2026), naar de gedrukte lijst van Weber (1902). Daar is dit aan toegevoegd:
- **Route.** Een met de hand getekende route langs alle stations, 16.349 km. Elk station heeft een plek op de route (`km`); daarop zijn kaart en tijdlijn gebouwd.
- **Positie.** 264 stations hebben een positie in de stationslijst. 34 ankerplaatsen zonder gedrukte positie hebben een geschatte positie uit de gouden dataset. Bij 65 andere stations gebruiken we de plek op de route. Zie `positie_geschat`.
- **Diepte van nu.** De diepte volgens GEBCO 2024, om de kilometer langs de route. Bij een station tonen we de moderne diepte alleen als de positie uit de stationslijst komt.
- **Tuig.** Uit de werkzaamheden afgeleid: `bodem`, `netten` of `onbekend` voor de plaatsing van specimens, en per tuig (kor, dreg, enzovoort) voor de tekening.
- **Netbereik.** Bij 18 stations staat in de tekst van tot welke diepte een net werd gehaald, zoals “From 1500 M. depth to surface” (`net_bereik_m`).
- **Niet op de bodem.** Zes stations melden dat het tuig de bodem niet haalde (`niet_op_bodem`).

## Bestanden
```
frontend/public/datasets/              ← in git, als geheel vervangen
├── siboga-goud.json                   ← specimens, musea, namen (zie gouden-dataset.md)
└── route-stations.json                ← route, diepte van nu en alle stations
frontend/public/data/                  ← van de pipeline, niet in git
├── explorer.json                      ← per specimen: foto en determinaties; per station: foto
├── media/specimen-<gbif>.jpg          ← de foto's van specimens
└── media/station-<nummer>.jpg         ← de foto's bij stations
```

`route-stations.json` maakt en raakt de pipeline niet. Formaat, zoals in de gouden dataset: `{"velden": [...], "rijen": [[...], ...]}`.

| Onderdeel | Velden |
| --- | --- |
| `lijn` | km, lon, lat, diepte_vandaag_m (om de 4 km; negatief is land of droogvallend rif) |
| `stations` | nummer, wikidata, datum, tot, km, lat, lon, positie_geschat (0 gedrukt, 1 geschatte ankerplaats, 2 plek op de route), diepte_m, diepte_soort, diepte_gedrukt, diepte_vandaag_m, bodem, tuig, net_bereik_m, niet_op_bodem, werkzaamheden, opmerkingen, noten, pagina |

`explorer.json` maakt de [pipeline](pipeline.md#ontdekmodus), net als de plaatjes van records: `fetch` zet de GBIF-records en foto's van de 183 specimens in de cache, `build` kopieert de foto's naar `media/` en schrijft per GBIF-sleutel `image` (`src`, `credit`, `license`, `licenseUrl`, `sourceUrl`), `identifications` (`name`, `by`, `date`, `remarks`, `current`) en `recordedBy` (de verzamelaars, letterlijk uit het record). Een foto komt er alleen in met een Creative Commons-licentie en een naam.

Daarnaast staat in `explorer.json` per stationnummer de foto van het station (`stations` → `image`, met ook `caption`). Die komt van het Wikidata-item van het station (P18) en staat op Wikimedia Commons; `fetch` vraagt de items per vijftig op en haalt de foto's met maker en licentie op, net als bij records. Het zijn 47 stations, bijna allemaal met een foto van Hugo Frederik Nierstrasz uit de expeditie zelf. Het bijschrift is het laatste deel van de bestandsnaam (“Sanguisiapo”). Zo'n foto toont de plek of de omgeving van het station, niet het moment van de vangst.

Zonder `explorer.json` werkt de ontdekmodus ook, alleen zonder foto's.

## Code
De ontdekmodus staat los van de rest van de frontend:

```
frontend/src/explorer/
├── el-explorer.vue           ← het geheel: kaart, datum, tijdlijn, duik, netje, specimen
├── data.js                   ← laadt en koppelt de drie bestanden; posities op de route
├── groups.js                 ← tekentjes per groep, en welke groepen op de bodem leven
├── gear.js                   ← het tuig: tekening, uitleg en archieffoto
├── el-explorer-map.vue       ← eigen MapLibre-kaart met de blauwe zeekaart; vliegen en kantelen
├── el-explorer-timeline.vue  ← tijdlijn op afstand, netje en de vliegende vondsten
├── el-explorer-dive.vue      ← de duik
├── el-explorer-specimen.vue  ← één specimen
├── el-explorer-net.vue       ← wat er tot nu toe in het netje zit
├── el-explorer-badge.vue     ← het zegel voor naamdragers
├── el-explorer-icon.vue
└── media/                    ← papier- en aquareltextuur, archieffoto's van het tuig
```

`views/vw-map.vue` toont `el-explorer.vue` schermvullend. Hetzelfde onderdeel is ook de plugin `deepdive` uit de content-repo, zodat het in een hoofdstuk kan staan; met een argument duikt het meteen bij een station: `[[Diep onder het schip#99]]`. De kaart is een eigen kaart, maar de zeekaart zelf (lagen, kleuren, wereldlagen, zoomgrens en namen) komt uit `services/sea-chart.js`, dezelfde module als die van `el-map.vue`. De gedetailleerde lagen komen uit de store (`store.mapLayers`).

## Bronnen en licenties
- **Specimens**: GBIF, licentie en bronvermelding per record en per dataset, zie [gouden-dataset.md](gouden-dataset.md#licenties-en-bronvermelding).
- **Foto's van specimens**: van het museum via GBIF, met de licentie en naam die erbij staan.
- **Stationslijst**: Fauconnier, S. (2026). *Station list of the Siboga Expedition (1899-1900) cross-referenced with Wikidata* [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.23433434. CC0. Naar Weber (1902), *Siboga-Expeditie* Monographie I (publiek domein).
- **Diepte van nu**: GEBCO Compilation Group (2024). GEBCO 2024 Grid. doi:10.5285/1c44ce99-0a0d-5f4f-e063-7086abc0ea0f. Publiek domein, met bronvermelding.
- **Archieffoto's van het tuig**: Hugo Frederik Nierstrasz, 1899–1900. Bijzondere Collecties, Universiteit van Amsterdam. Publiek domein.
- **Foto's bij stations**: via Wikidata (P18) van Wikimedia Commons, met de maker en licentie die erbij staan; bijna allemaal Nierstrasz, Bijzondere Collecties UvA, publiek domein.
- **Wikidata**: CC0.
