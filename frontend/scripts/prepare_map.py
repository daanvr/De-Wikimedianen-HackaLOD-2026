"""Prepare the static map layers for the frontend.

Reads Natural Earth bathymetry shapefiles, Natural Earth land and the route
drawn from station to station (one LineString per leg), clips them to the
archipelago, simplifies them and writes small GeoJSON files to public/map-layers/.
The route file also gets one Point per station, so the map can draw the stops.
Coarse world versions of the land (Natural Earth 50m) and depth layers fill in
the rest of the world, outside the archipelago. The land files hold the land as polygons and
the coastline as separate lines, so the edge of the archipelago, where the two
are cut apart, never shows up as a line on the map.

Usage:
    uv run --with shapely --with pyshp scripts/prepare_map.py <natural-earth-dir> <route-geojson> <ne_10m_land.shp> <ne_50m_land.shp> <output-dir>
"""
import json
import sys
from pathlib import Path

import shapefile
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.ops import unary_union

BBOX = box(104.0, -16.0, 142.0, 10.0)
# The world layers are only seen zoomed out, so they can be much coarser
WORLD_TOLERANCE = 0.1
# Coastlines are seen up to about province level, so the land needs more detail than the depths
WORLD_LAND_TOLERANCE = 0.02
WORLD_DIGITS = 2
BATHYMETRY_LAYERS = [
    ("K_200", 200),
    ("J_1000", 1000),
    ("I_2000", 2000),
    ("H_3000", 3000),
    ("G_4000", 4000),
    ("F_5000", 5000),
    ("E_6000", 6000),
    ("D_7000", 7000)
]

def bathymetry_shapes(natural_earth_dir: Path, layer: str) -> list:
    # Natural Earth ships the layers both as one zip per layer (a folder each) and as one flat zip
    name = f"ne_10m_bathymetry_{layer}.shp"
    path = natural_earth_dir / layer / name
    if not path.exists():
        path = natural_earth_dir / name
    return [shape(record.__geo_interface__) for record in shapefile.Reader(str(path)).shapes()]

def clip_and_simplify(geometries: list, tolerance: float):
    merged = unary_union([geometry.buffer(0) for geometry in geometries])
    clipped = merged.intersection(BBOX)
    return clipped.simplify(tolerance, preserve_topology = True)

def drop_small_parts(geometry, min_area: float):
    polygons = [part for part in getattr(geometry, "geoms", [geometry]) if part.area >= min_area]
    return MultiPolygon([
        Polygon(polygon.exterior, [ring for ring in polygon.interiors if Polygon(ring).area >= min_area])
        for polygon in polygons
    ])

def land_features(land, area) -> list:
    """The land within `area` as one polygon feature plus one coastline feature."""
    return [{
        "type" : "Feature",
        "properties" : {},
        "geometry" : mapping(area(land))
    }, {
        "type" : "Feature",
        "properties" : {},
        "geometry" : mapping(area(land.boundary))
    }]

def read_shapes(path: Path) -> list:
    if path.suffix == ".shp":
        return [shape(record.__geo_interface__) for record in shapefile.Reader(str(path)).shapes()]
    return [shape(feature["geometry"]) for feature in json.loads(path.read_text())["features"]]

def round_coordinates(value, digits: int = 4):
    if isinstance(value, (list, tuple)):
        return [round_coordinates(item, digits) for item in value]
    return round(value, digits)

def world_geometry(geometries: list, tolerance: float):
    # Simplified as a whole, so islands across the edge of the archipelago are not cut off
    merged = unary_union([geometry.buffer(0) for geometry in geometries])
    simplified = merged.simplify(tolerance, preserve_topology = True)
    return drop_small_parts(simplified, tolerance * tolerance * 20)

def write_geojson(path: Path, features: list, digits: int = 4):
    for feature in features:
        feature["geometry"]["coordinates"] = round_coordinates(feature["geometry"]["coordinates"], digits)
    collection = {
        "type" : "FeatureCollection",
        "features" : features
    }
    path.write_text(json.dumps(collection, ensure_ascii = False, separators = (",", ":")))
    print(f"wrote {path} ({path.stat().st_size // 1024} KB, {len(features)} features)")

def prepare_bathymetry(natural_earth_dir: Path, output_dir: Path):
    features = []
    for layer, depth in BATHYMETRY_LAYERS:
        geometry = clip_and_simplify(bathymetry_shapes(natural_earth_dir, layer), 0.01)
        if geometry.is_empty:
            continue
        features.append({
            "type" : "Feature",
            "properties" : {
                "depth" : depth
            },
            "geometry" : mapping(geometry)
        })
    write_geojson(output_dir / "bathymetry.geojson", features)

def prepare_land(land_path: Path, output_dir: Path):
    # Simplified a little beyond the edge, so the coastline runs on across it
    nearby = BBOX.buffer(1, join_style = "mitre")
    geometries = [geometry.buffer(0).intersection(nearby) for geometry in read_shapes(land_path)]
    land = unary_union(geometries).simplify(0.005, preserve_topology = True)
    write_geojson(output_dir / "land.geojson", land_features(land, BBOX.intersection))

def prepare_route(route_path: Path, output_dir: Path):
    source = json.loads(route_path.read_text())
    legs = []
    stations = {}
    for feature in source["features"]:
        properties = feature["properties"]
        coordinates = feature["geometry"]["coordinates"]
        legs.append({
            "type" : "Feature",
            "properties" : {
                "leg" : properties["etappe"],
                "from" : properties["van"],
                "to" : properties["naar"],
                "dateFrom" : properties["van_datum"],
                "dateTo" : properties["naar_datum"]
            },
            "geometry" : {
                "type" : "LineString",
                "coordinates" : coordinates
            }
        })
        ends = [
            (properties["van"], properties["van_datum"], coordinates[0]),
            (properties["naar"], properties["naar_datum"], coordinates[-1])
        ]
        for name, date, coordinate in ends:
            # Departure and return are both Soerabaja: one port dot
            is_port = name.startswith("Soerabaja")
            station = "Soerabaja" if is_port else name
            stations.setdefault(station, {
                "type" : "Feature",
                "properties" : {
                    "station" : station,
                    "date" : date,
                    "port" : is_port
                },
                "geometry" : {
                    "type" : "Point",
                    "coordinates" : coordinate
                }
            })
    write_geojson(output_dir / "route.geojson", legs + list(stations.values()))

def prepare_world(natural_earth_dir: Path, world_land_path: Path, output_dir: Path):
    features = []
    for layer, depth in BATHYMETRY_LAYERS:
        features.append({
            "type" : "Feature",
            "properties" : {
                "depth" : depth
            },
            "geometry" : mapping(world_geometry(bathymetry_shapes(natural_earth_dir, layer), WORLD_TOLERANCE).difference(BBOX))
        })
    write_geojson(output_dir / "world-bathymetry.geojson", features, WORLD_DIGITS)
    land = world_geometry(read_shapes(world_land_path), WORLD_LAND_TOLERANCE)
    write_geojson(output_dir / "world-land.geojson", land_features(land, lambda geometry: geometry.difference(BBOX)), WORLD_DIGITS)

def main():
    natural_earth_dir, route_path, land_path, world_land_path, output_dir = [Path(arg) for arg in sys.argv[1:6]]
    output_dir.mkdir(parents = True, exist_ok = True)
    prepare_bathymetry(natural_earth_dir, output_dir)
    prepare_land(land_path, output_dir)
    prepare_route(route_path, output_dir)
    prepare_world(natural_earth_dir, world_land_path, output_dir)

if __name__ == "__main__":
    main()
