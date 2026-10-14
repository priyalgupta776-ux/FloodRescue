

import json
import os
import sys
import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape

if len(sys.argv) != 3:
    print("Usage: python processing/create_results.py <area_name> <event_date>")
    sys.exit(1)

area_name = sys.argv[1]
event_date = sys.argv[2]

os.makedirs("data/outputs", exist_ok=True)

print("Calculating flood area...", flush=True)

with rasterio.open("data/processed/flood_mask.tif") as src:
    mask = src.read(1)
    transform = src.transform
    crs = src.crs

polygons = [
    shape(geom)
    for geom, value in shapes(mask, transform=transform)
    if value == 1
]

if polygons:
    flood = gpd.GeoDataFrame(geometry=polygons, crs=crs)
    flood = flood.to_crs("EPSG:6933")
    area_km2 = flood.geometry.union_all().area / 1_000_000
else:
    area_km2 = 0.0


def count_features(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required analysis output is missing: {path}"
        )
    return len(gpd.read_file(path))


total_roads = count_features("data/processed/roads.geojson")
total_bridges = count_features("data/processed/bridges.geojson")
total_buildings = count_features("data/processed/buildings.geojson")
total_settlements = count_features("data/processed/settlements.geojson")
total_hospitals = count_features("data/processed/hospitals.geojson")

affected_roads = count_features("data/processed/affected_roads.geojson")
affected_bridges = count_features("data/processed/affected_bridges.geojson")
affected_buildings = count_features("data/processed/affected_buildings.geojson")
cut_off = count_features(
    "data/outputs/potentially_cut_off_settlements.geojson"
)

results = {
    "area": area_name,
    "event_date": event_date,
    "flooded_area_km2": round(area_km2, 2),
    "total_roads": total_roads,
    "potentially_affected_roads": affected_roads,
    "total_bridges": total_bridges,
    "potentially_affected_bridges": affected_bridges,
    "total_buildings": total_buildings,
    "potentially_affected_buildings": affected_buildings,
    "total_settlements": total_settlements,
    "total_hospitals": total_hospitals,
    "settlements_potentially_cut_off": cut_off,
    "limitations": [
        "Preliminary satellite-based flood estimate",
        "Infrastructure intersections indicate potential impact, not confirmed damage",
        "Connectivity is simulated and does not confirm actual road passability",
        "Current OpenStreetMap data is used; pre-event data is still required"
    ]
}

with open("data/outputs/results.json", "w") as file:
    json.dump(results, file, indent=4)

print("Results saved successfully:")
print(json.dumps(results, indent=4))
