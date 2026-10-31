# Frontend
De Vue-frontend van De Siboga Expeditie. Hoe hij in elkaar zit, staat in [docs/frontend.md](../docs/frontend.md); hoe je hem draait in [docs/ontwikkelen.md](../docs/ontwikkelen.md).

```bash
just data        # frontend data maken (eenmalig, en na nieuwe content)
just dev         # http://localhost:5173
```

## Kaartlagen
`public/map/` bevat de kaartlagen. Ze staan in git en de pipeline raakt ze niet aan.

| Bestand              | Inhoud                                                  | Herkomst                                                                                                                                                     |
| -------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bathymetry.geojson` | Dieptebanden 200 tot 7000 m                             | [Natural Earth](https://www.naturalearthdata.com/downloads/10m-physical-vectors/), publiek domein                                                            |
| `land.geojson`       | Land en kustlijn; de kustlijn staat er als losse lijn in, zodat de rand van het gebied geen streep op de kaart geeft | Natural Earth 10m land, publiek domein                                                                                                                       |
| `route.geojson`      | De gevaren route in 264 etappes van station naar station, plus een punt per station | Getekend langs de stations, met de "Kaart van den Trek v. H.M. Siboga 1899-1900" uit Weber-van Bosse (1904), [Commons](https://commons.wikimedia.org/wiki/File:Route_of_the_Siboga_Expedition.jpg), publiek domein, als onderlegger. Waar de kaart geen omweg laat zien, is een etappe een rechte lijn |
| `world-bathymetry.geojson` en `world-land.geojson` | Grove diepte en kustlijnen voor de rest van de wereld, buiten de archipel | [Natural Earth](https://www.naturalearthdata.com/) 10m bathymetrie en 50m land, publiek domein |

Daarop ligt de historische kaart als hoofdlaag. Die staat niet in git, maar komt live van Allmaps: `https://allmaps.xyz/images/1fd0accb445d424e/{z}/{x}/{y}@2x.png`, de "Kaart van den Trek v. H.M. Siboga 1899-1900" uit de beeldbank van het [Stadsarchief Amsterdam](https://archief.amsterdam/beeldbank), gegeorefereerd met [Allmaps](https://allmaps.org).

`scripts/prepare_map.py` snijdt de bronbestanden bij tot de archipel en vereenvoudigt ze:

```bash
uv run --with shapely --with pyshp scripts/prepare_map.py <natural-earth-map> <route.geojson> <ne_10m_land.shp> <ne_50m_land.shp> public/map
```

De route is getekend naar een schets op kleine schaal uit 1904: lees hem als "ongeveer hier", niet als GPS-spoor. De stations staan op hun gedrukte positie; stations zonder positie zijn overgeslagen.
