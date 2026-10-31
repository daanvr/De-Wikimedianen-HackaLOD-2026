"""Prepare the static map layers for the frontend.

Reads Natural Earth bathymetry shapefiles, Natural Earth land and the route
drawn from station to station (one LineString per leg), clips them to the
archipelago, simplifies them and writes small GeoJSON files to public/map/.
The route file also gets one Point per station, so the map can draw the stops.

Usage:
    uv run --with shapely --with pyshp scripts/prepare_map.py <natural-earth-dir> <route-geojson> <land-geojson> <output-dir>
"""
import json
import sys
from pathlib import Path

import shapefile
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

BBOX = box(104.0, -16.0, 142.0, 10.0)
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

def clip_and_simplify(geometries: list, tolerance: float):
    merged = unary_union([geometry.buffer(0) for geometry in geometries])
    clipped = merged.intersection(BBOX)
    return clipped.simplify(tolerance, preserve_topology = True)

def round_coordinates(value, digits: int = 4):
    if isinstance(value, (list, tuple)):
        return [round_coordinates(item, digits) for item in value]
    return round(value, digits)

def write_geojson(path: Path, features: list):
    for feature in features:
        feature["geometry"]["coordinates"] = round_coordinates(feature["geometry"]["coordinates"])
    collection = {
        "type" : "FeatureCollection",
        "features" : features
    }
    path.write_text(json.dumps(collection, ensure_ascii = False, separators = (",", ":")))
    print(f"wrote {path} ({path.stat().st_size // 1024} KB, {len(features)} features)")

def prepare_bathymetry(natural_earth_dir: Path, output_dir: Path):
    features = []
    for layer, depth in BATHYMETRY_LAYERS:
        reader = shapefile.Reader(str(natural_earth_dir / layer / f"ne_10m_bathymetry_{layer}.shp"))
        geometries = [shape(record.__geo_interface__) for record in reader.shapes()]
        geometry = clip_and_simplify(geometries, 0.01)
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
    source = json.loads(land_path.read_text())
    geometries = [shape(feature["geometry"]) for feature in source["features"]]
    geometry = clip_and_simplify(geometries, 0.005)
    write_geojson(output_dir / "land.geojson", [{
        "type" : "Feature",
        "properties" : {},
        "geometry" : mapping(geometry)
    }])

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

def main():
    natural_earth_dir, route_path, land_path, output_dir = [Path(arg) for arg in sys.argv[1:5]]
    output_dir.mkdir(parents = True, exist_ok = True)
    prepare_bathymetry(natural_earth_dir, output_dir)
    prepare_land(land_path, output_dir)
    prepare_route(route_path, output_dir)

if __name__ == "__main__":
    main()
