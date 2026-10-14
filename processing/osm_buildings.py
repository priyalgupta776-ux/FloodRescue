import os
import osmnx as ox

os.makedirs("data/processed", exist_ok=True)

north = 27.75
south = 27.60
east = 85.45
west = 85.20

print("Downloading buildings...")

buildings = ox.features_from_bbox(
    bbox=(west, south, east, north),
    tags={"building": True}
)

buildings = buildings[
    buildings.geometry.notna()
]

print("Buildings found:", len(buildings))

buildings.to_file(
    "data/processed/buildings.geojson",
    driver="GeoJSON"
)

print("Saved: data/processed/buildings.geojson")
