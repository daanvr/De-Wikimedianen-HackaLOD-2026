# Stationslijst

Bestanden: [`../data/Siboga_stations_v2_5.xlsx`](../data/Siboga_stations_v2_5.xlsx) en [`../data/siboga_stations_v2_5.csv`](../data/siboga_stations_v2_5.csv). In de spreadsheet staat een tabblad "Read me" met alle conventies.

## Wat is een station?

Een plek waar de expeditie stopte om te meten, te vissen, te dreggen of de bodem te bemonsteren. Museumspecimens verwijzen naar deze stationsnummers als vindplaats. Daardoor is de stationslijst de sleutel tussen de reis en de collecties.

## Bron

*Liste des Stations de la Campagne scientifique du Siboga, révisée par le Commandant M.-G. F. Tydeman*, in Max Weber, *Introduction et description de l'expédition* (1902), lijstpagina's 3–16, achterin het boek (PDF-pagina's ca. 162–176).

## Omvang

- **323 genummerde stations**, plus lettervarianten (bv. 45a, 202a–d): samen **363 rijen**.
- Periode: **maart 1899 – februari 1900**. Vanaf station 275 is het jaar 1900.

> Dit beantwoordt een open vraag in `expeditie/expeditie.md` over het aantal stations. Het getal 156 daar kwam uit een eerdere, onvolledige transcriptie.

## Wie deed wat

| Kolommen | Gemaakt door | Betrouwbaarheid |
|---|---|---|
| Datum, breedte, lengte, diepte | Getranscribeerd, daarna door Sandra Fauconnier met de hand gecontroleerd tegen de scans (10 oktober 2026) | Gezaghebbend |
| Bodem, vangtuig, opmerkingen | Getranscribeerd uit slechte OCR, met hulp van Claude | **Minst gecontroleerd.** Vooral plaatsnamen kunnen fouten bevatten |
| Decimale coördinaten, begin- en einddatum, dieptetype | Berekend uit de gecontroleerde kolommen | Gecontroleerd: 0 afwijkingen ten opzichte van Sandra's eigen decimalen |
| Afgeleide en geëxtrapoleerde posities | Berekend, zie hieronder | Schattingen |

## Drie soorten posities

1. **Uit de bron** (255 rijen): breedte en lengte zoals Tydeman ze opgeeft.
2. **Afgeleid uit peiling** (9 rijen, station 225 en 225a–h): de bron geeft hier geen coördinaten, maar een afstand en kompasrichting vanaf de zuidpunt van Zuid-Lucipara (Banda Zee). De positie is daaruit berekend met een aangenomen referentiepunt van ca. 5,51° Z, 127,54° O. Onzekerheid: ongeveer 2 tot 3 km.
3. **Geëxtrapoleerd** (97 rijen): stations zonder positie, zoals ankerplaatsen, strand-, rif- en netstations. Ze liggen op een rechte lijn tussen het vorige en het volgende station met een bekende positie, gelijk verdeeld. **Dit is een schatting.** In baaien en zeestraten kan zo'n punt ver van de werkelijke route liggen. Stations 322 en 323 hebben geen positie, omdat er geen later station is om naartoe te interpoleren.

Voor de kaart: maak deze drie soorten zichtbaar verschillend, en presenteer type 3 niet als exacte plek.

## Diepte

- In 12 rijen is de diepte met een verhoogde punt gedrukt (stations 39, 45a, 111, 183, 185, 199, 202a–d, 203, 309a). Dat is **geen bodemloding**. Het getal geeft aan hoe diep de draad, het net of de cilinder kwam, zonder de bodem te raken. Deze rijen hebben `Depth type` = *apparatus/wire depth*.
- Bij bereiken zoals "18-27" of "up to 36" staat in `Depth (m, numeric)` één getal: de bovengrens of het midden. ❓ Nog kiezen welke conventie we voor Wikidata gebruiken.

## Controles

- Geen minuten van 60 of meer, geen coördinaten buiten het gebied en geen onverklaarbare sprongen. Grote afstanden tussen stations vallen samen met meerdaagse tochten.
- Hersteld: bij stations 126, 128 en 130 ontbrak de punt voor de tiende minuut.
- **Beperking:** de controles vangen onmogelijke waarden. Een verkeerd maar plausibel cijfer binnen een cluster vangen ze niet.

## Open punten

- ❓ Plaatsnamen in de kolom Opmerkingen controleren tegen de scan.
- ❓ De afgeleide posities van de 225-reeks controleren op een zeekaart.
- ❓ Beleid voor Wikidata: krijgen geschatte posities een P625 met lage rang en kwalificator, of helemaal geen P625?
- ❓ Een niet-genummerde verkenning van de kust (Lithothamnion, bij Karang Lintang en Pulu Palabangan) staat in de opmerkingen van station 91, omdat de bron er geen nummer aan geeft.
