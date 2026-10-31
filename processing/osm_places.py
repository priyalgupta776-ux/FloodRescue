

import os
import sys
import time
import osmnx as ox

ox.settings.overpass_url = "https://maps.mail.ru/osm/tools/overpass/api"
ox.settings.timeout = 180
ox.settings.requests_timeout = 180

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

# Avoid unnecessarily large requests.
if east - west > 0.5 or north - south > 0.5:
    print("Error: Area is too large. Use a smaller bounding box.")
    sys.exit(1)

os.makedirs("data/processed", exist_ok=True)

bbox = (west, south, east, north)

# Configure request timeouts.
ox.settings.timeout = 180
ox.settings.requests_timeout = 180

tags = {
    "place": [
        "city", "town", "village", "hamlet",
        "isolated_dwelling"
    ]
}

print("Downloading settlements from OpenStreetMap...", flush=True)

# Retry temporary Overpass failures with exponential backoff.
places = None

for attempt in range(4):
    try:
        print(
            f"Attempt {attempt + 1}/4...",
            flush=True
        )

        places = ox.features_from_bbox(
            bbox=bbox,
            tags=tags
        )

        if places.empty:
            print("No settlements found in this area.", flush=True)
            sys.exit(1)

        places = places[places.geometry.notna()]

        if places.empty:
            print("No valid settlement geometries found.", flush=True)
            sys.exit(1)

        break

    except Exception as e:
        print(f"Download failed: {e}", flush=True)

        if attempt == 3:
            print(
                "Overpass is still unavailable. "
                "Wait and retry the analysis later.",
                flush=True
            )
            sys.exit(1)

        wait_seconds = 15 * (2 ** attempt)
        print(
            f"Retrying in {wait_seconds} seconds...",
            flush=True
        )
        time.sleep(wait_seconds)

# Save only after a successful download.
output_file = "data/processed/settlements.geojson"
temp_file = output_file + ".tmp"

try:
    places.to_file(temp_file, driver="GeoJSON")
    os.replace(temp_file, output_file)
except Exception as e:
    if os.path.exists(temp_file):
        os.remove(temp_file)
    print(f"Could not save settlements: {e}", flush=True)
    sys.exit(1)

print(f"Settlements found: {len(places)}", flush=True)
print(f"Saved to: {output_file}", flush=True)
