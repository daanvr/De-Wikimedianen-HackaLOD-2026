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
| `land.geojson`       | Kustlijnen                                              | Natural Earth 10m land, publiek domein                                                                                                                       |
| `route.geojson`      | De gevaren route, in 146 stukken                        | Getraceerd van de "Kaart van den Trek v. H.M. Siboga 1899-1900" uit Weber-van Bosse (1904), [Commons](https://commons.wikimedia.org/wiki/File:Route_of_the_Siboga_Expedition.jpg), publiek domein |

`scripts/prepare_map.py` snijdt de bronbestanden bij tot de archipel en vereenvoudigt ze:

```bash
uv run --with shapely --with pyshp scripts/prepare_map.py <natural-earth-map> <route-data-map> <land.geojson> public/map
```

De route is een schets op kleine schaal uit 1904: lees hem als "ongeveer hier", niet als GPS-spoor.
