# De Wikimedianen (HackaLOD 2026)
Dit is de Github repository van team De Wikimedianen voor hun bijdragen aan de HackaLOD 2026. Een hackathon met erfgoeddata van het Netwerk Digitaal Erfgoed op vrijdag 30 oktober 2026 in de Nieuwe Kerk in Middelburg.

Het resultaat is de website **[De Siboga Expeditie](https://siboga.nl)**: het verhaal van de Nederlandse zee-expeditie van 1899–1900 naar de Indonesische archipel, verteld met Linked Data uit erfgoed- en natuurhistorische collecties.

# Wat we gedaan hebben
## Het idee
De Siboga-expeditie bracht tienduizenden dieren en planten naar Nederland. Die liggen nu verspreid over musea in Leiden, Londen, Parijs, Harvard en Trondheim, en de verslagen verschenen tussen 1901 en 1986 in 148 delen. Wij brengen dat verspreide materiaal weer samen: elk verhaal verwijst naar records, en elk record verwijst naar Linked Data elders. De kaart is de ruggengraat. Het model is herbruikbaar voor elk verhaal dat je via punten op een kaart en Linked Data kunt vertellen.

## De website
- **Verhaal in hoofdstukken.** Over het schip, de bemanning, het verzamelen, de route, de collectie, de vrouwen in en rond de expeditie, wat er na de reis gebeurde en hoe het nu gaat met de Siboga-soorten. Met een verklarend woordenboek.
- **Records.** Personen, plaatsen, specimens, publicaties, foto's en collecties, elk met een eigen pagina en een verwijzing naar de bron.
- **Datavisualisatie.** Een kaart met tijdlijn: het schip vaart mee, bij elk station vliegen de vondsten het net in, en je kunt de waterkolom in duiken tot op de bodem. Zie [docs/ontdekmodus.md](docs/ontdekmodus.md).
- **Statisch en robuust.** Een Python-pipeline haalt alle bronnen vooraf op en een Vue-frontend toont ze. Alles staat lokaal, zodat de site ook werkt als een externe dienst uitvalt. Zie [docs/](docs/README.md).

## De inhoud
De teksten staan in de content-repo [hay/siboga-content](https://github.com/hay/siboga-content), geschreven in Obsidian.
- **Hoofdstukken** met bronvermelding, gecontroleerd tegen de oorspronkelijke bronnen, vooral *Een jaar aan boord H.M. Siboga* van Anna Weber-van Bosse (1904).
- **Ruim honderd records**, onder meer voor de wetenschappers en de bemanning, inclusief de Indonesische bemanningsleden die alleen Anna bij naam noemt.
- **Vrouwen in de wetenschap.** Dertien vrouwen schreven mee aan zeventien delen van de Siboga-reeks, van Ethel Barton (1901) tot Marian Pettibone (1970). Ze hebben allemaal een record met een Wikidata-koppeling.
- **Collecties en platforms** als locatie-records met een Wikidata-URI: Naturalis, het voormalige Zoölogisch Museum Amsterdam, het Museum of Comparative Zoology, het MNHN, het Natural History Museum in Londen, het NTNU Vitenskapsmuseet, de Bijzondere Collecties van de UvA, het Stadsarchief Amsterdam en de KB, plus GBIF, de Biodiversity Heritage Library en WoRMS.
- **Verklarend woordenboek** gekoppeld aan het [Termennetwerk](https://termennetwerk.netwerkdigitaalerfgoed.nl/) van het NDE: 45 van de ongeveer 80 termen hebben een link naar de Cultuurhistorische Thesaurus, de Art & Architecture Thesaurus, de Indisch Erfgoed Thesaurus of Wikidata.

## Data die we open hebben gemaakt
- **Wikidata.** De 363 stations van de expeditie staan als items op Wikidata, de meeste met coördinaten. Ook bemanningsleden en het scheepsdier, de kasuaris Piet, kregen een item. Daarnaast werken we aan een item per deel van de Siboga-reeks.
- **Zenodo.** De stationslijst staat als dataset op Zenodo: [doi:10.5281/zenodo.23433434](https://doi.org/10.5281/zenodo.23433434).
- **Gouden dataset.** 6.714 specimens waarvan zeker is dat ze van de Siboga komen, waarvan 183 ook zeker van één station. Zie [docs/gouden-dataset.md](docs/gouden-dataset.md).

## Bronnen en Linked Data
| Bron | Waarvoor | NDE |
| --- | --- | --- |
| [Wikidata](https://www.wikidata.org/wiki/Q4201627) | Stations, personen, plaatsen, publicaties, collecties | Termennetwerk |
| [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Siboga_Expedition) | Foto's van de expeditie (Bijzondere Collecties UvA), portretten, platen | |
| [Nederlandse Thesaurus van Auteursnamen](https://datasetregister.netwerkdigitaalerfgoed.nl/datasets/http://data.bibliotheken.nl/id/dataset/persons) (KB) | Auteurs van de Siboga-reeks | Datasetregister |
| [Cultuur-Historische Objecten](https://datasetregister.netwerkdigitaalerfgoed.nl/datasets/https://linkeddata.cultureelerfgoed.nl/rce/datacatalog/id/dataset/db6193aa-84af-3edf-90fd-074a0a11248d) (RCE) | Huis te Eerbeek, het huis van de Webers | Datasetregister |
| [Termennetwerk](https://termennetwerk.netwerkdigitaalerfgoed.nl/) | Termen in het verklarend woordenboek | Termennetwerk |
| [GBIF](https://www.gbif.org/) | Specimens van Naturalis en andere musea | |
| [Biodiversity Heritage Library](https://www.biodiversitylibrary.org/) | Gescande delen van de Siboga-reeks | |
| [WoRMS](https://www.marinespecies.org/) | Geldige soortnamen | |
| [Stadsarchief Amsterdam](https://archief.amsterdam/) | Archief van het Zoölogisch Museum, historische kaart | |

# Uitleg en documentatie
De technische documentatie van de website staat in [docs/](docs/README.md). De codeconventies staan in [CLAUDE.md](CLAUDE.md). Het inhoudelijke overzicht van de expeditie staat in [expeditie/](expeditie/README.md).

# "Gratis" datavisualisaties, naast onze HackaLOD output
Doordat de expeditie, de stations en de mensen op Wikidata staan, kun je ze ook bekijken met tools die de Wikidata-community al gebouwd heeft.
- [Reasonator](https://reasonator.toolforge.org/?q=Q4201627): de Siboga-expeditie als overzichtspagina
- [Scholia](https://scholia.toolforge.org/Q4201627): publicaties en verbanden rond de expeditie
- [Kaart van de stations](https://query.wikidata.org/#%23title%3A%20Siboga%20Expedition%20%281899%E2%80%931900%29%3A%20route%20langs%20de%20stations%0A%23defaultView%3AMap%7B%22hide%22%3A%5B%22%3Fgeo%22%2C%22%3Frgb%22%5D%2C%22layer%22%3A%22%3Flayer%22%7D%0ASELECT%20%3Fitem%20%3FitemLabel%20%3Fdate%20%3Fgeo%20%3Flayer%20%3Frgb%20WITH%20%7B%0A%20%20%23%20All%20stations%20with%20coordinates%2C%20with%20a%20sort%20key%3A%20date%20%2B%20station%20number%20%2B%20suffix%0A%20%20SELECT%20%3Fitem%20%3Fcoord%20%3Fdate%20%3Fkey%20WHERE%20%7B%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ141748032%20%3B%20%20%20%20%20%20%20%23%20instance%20of%3A%20sampling%20station%0A%20%20%20%20%20%20%20%20%20%20wdt%3AP625%20%3Fcoord%20%3B%20%20%20%20%20%20%20%20%20%20%20%20%20%23%20coordinate%20location%0A%20%20%20%20%20%20%20%20%20%20p%3AP793%20%3Fevent%20.%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%23%20significant%20event%0A%20%20%20%20%3Fevent%20ps%3AP793%20wd%3AQ4201627%20.%20%20%20%20%20%20%20%20%23%20%3D%20Siboga%20Expedition%0A%20%20%20%20OPTIONAL%20%7B%20%3Fevent%20pq%3AP585%20%3Fpit%20.%20%7D%20%20%23%20point%20in%20time%0A%20%20%20%20OPTIONAL%20%7B%20%3Fevent%20pq%3AP580%20%3Fstart%20.%20%7D%23%20start%20time%0A%20%20%20%20BIND%28SUBSTR%28STR%28COALESCE%28%3Fpit%2C%20%3Fstart%29%29%2C%201%2C%2010%29%20AS%20%3Fdate%29%0A%20%20%20%20%3Fitem%20rdfs%3Alabel%20%3Flabel%20.%20FILTER%28LANG%28%3Flabel%29%20%3D%20%22en%22%29%0A%20%20%20%20BIND%28STRAFTER%28%3Flabel%2C%20%22station%20no.%20%22%29%20AS%20%3Fno%29%0A%20%20%20%20BIND%28REPLACE%28%3Fno%2C%20%22%5B%5E0-9%5D%22%2C%20%22%22%29%20AS%20%3Fnum%29%0A%20%20%20%20BIND%28CONCAT%28%3Fdate%2C%20%22%7C%22%2C%20SUBSTR%28CONCAT%28%22000%22%2C%20%3Fnum%29%2C%20STRLEN%28%3Fnum%29%20%2B%201%29%2C%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20REPLACE%28%3Fno%2C%20%22%5B0-9%5D%22%2C%20%22%22%29%29%20AS%20%3Fkey%29%0A%20%20%7D%0A%7D%20AS%20%25stations%0AWITH%20%7B%0A%20%20%23%20For%20each%20station%3A%20the%20key%20of%20the%20next%20station%20in%20time%0A%20%20SELECT%20%3Fa%20%28MIN%28%3Fkb%29%20AS%20%3FnextKey%29%20WHERE%20%7B%0A%20%20%20%20INCLUDE%20%25stations%0A%20%20%20%20BIND%28%3Fitem%20AS%20%3Fa%29%20BIND%28%3Fkey%20AS%20%3Fka%29%0A%20%20%20%20%7B%20SELECT%20%28%3Fitem%20AS%20%3Fb%29%20%28%3Fkey%20AS%20%3Fkb%29%20WHERE%20%7B%20INCLUDE%20%25stations%20%7D%20%7D%0A%20%20%20%20FILTER%28%3Fkb%20%3E%20%3Fka%29%0A%20%20%7D%20GROUP%20BY%20%3Fa%0A%7D%20AS%20%25next%0AWHERE%20%7B%0A%20%20%7B%0A%20%20%20%20%23%20Layer%201%3A%20the%20stations%20as%20points%0A%20%20%20%20INCLUDE%20%25stations%0A%20%20%20%20BIND%28%3Fcoord%20AS%20%3Fgeo%29%0A%20%20%20%20BIND%28%22Stations%22%20AS%20%3Flayer%29%0A%20%20%20%20BIND%28%221F4E79%22%20AS%20%3Frgb%29%0A%20%20%7D%20UNION%20%7B%0A%20%20%20%20%23%20Layer%202%3A%20one%20line%20segment%20from%20each%20station%20to%20the%20next%0A%20%20%20%20INCLUDE%20%25next%0A%20%20%20%20%7B%20SELECT%20%28%3Fitem%20AS%20%3Fa%29%20%28%3Fcoord%20AS%20%3Fca%29%20%3Fdate%20WHERE%20%7B%20INCLUDE%20%25stations%20%7D%20%7D%0A%20%20%20%20%7B%20SELECT%20%28%3Fcoord%20AS%20%3Fcb%29%20%28%3Fkey%20AS%20%3FnextKey%29%20WHERE%20%7B%20INCLUDE%20%25stations%20%7D%20%7D%0A%20%20%20%20BIND%28STRDT%28CONCAT%28%22LINESTRING%28%22%2C%0A%20%20%20%20%20%20%20%20%20%20%20STR%28geof%3Alongitude%28%3Fca%29%29%2C%20%22%20%22%2C%20STR%28geof%3Alatitude%28%3Fca%29%29%2C%20%22%2C%22%2C%0A%20%20%20%20%20%20%20%20%20%20%20STR%28geof%3Alongitude%28%3Fcb%29%29%2C%20%22%20%22%2C%20STR%28geof%3Alatitude%28%3Fcb%29%29%2C%20%22%29%22%29%2C%0A%20%20%20%20%20%20%20%20%20geo%3AwktLiteral%29%20AS%20%3Fgeo%29%0A%20%20%20%20BIND%28%3Fa%20AS%20%3Fitem%29%0A%20%20%20%20BIND%28%22Route%22%20AS%20%3Flayer%29%0A%20%20%20%20BIND%28%22C0392B%22%20AS%20%3Frgb%29%0A%20%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%0A%7D%0A) in de Wikidata Query Service
- [Deelnemers aan de expeditie](https://w.wiki/fVNb) in de Wikidata Query Service
- [De expeditie in de Expeditia-tool](https://www.expeditia.info/expedition/Q4201627), waarin via Linked Data gerelateerde specimen getoond worden
