
import os
import sys
import osmnx as ox

if len(sys.argv) != 5:
    print("Usage: python processing/osm_places.py west south east north")
    sys.exit(1)

try:
    west, south, east, north = map(float, sys.argv[1:5])
except ValueError:
    print("Error: Coordinates must be numbers.")
    sys.exit(1)

if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
    print("Error: Invalid bounding box.")
    sys.exit(1)

os.makedirs("data/processed", exist_ok=True)
bbox = (west, south, east, north)

print("Downloading settlements...", flush=True)

places = ox.features_from_bbox(
    bbox=bbox,
    tags={"place": ["city", "town", "village", "hamlet", "isolated_dwelling"]}
)

places = places[places.geometry.notna()]
places.to_file("data/processed/settlements.geojson", driver="GeoJSON")

print(f"Settlements found: {len(places)}", flush=True)

