
import os
import sys
import osmnx as ox

if len(sys.argv) != 5:
    print("Usage: python processing/osm_hospitals.py west south east north")
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

print("Downloading hospitals and clinics...", flush=True)

hospitals = ox.features_from_bbox(
    bbox=bbox,
    tags={"amenity": ["hospital", "clinic"]}
)

hospitals = hospitals[hospitals.geometry.notna()]
hospitals.to_file("data/processed/hospitals.geojson", driver="GeoJSON")

print(f"Hospitals and clinics found: {len(hospitals)}", flush=True)


