
import os
import sys
import osmnx as ox

ox.settings.overpass_url = "https://overpass.kumi.systems/api"
ox.settings.timeout = 180
ox.settings.requests_timeout = 180


# Usage:
# python processing/osm_analysis.py west south east north

if len(sys.argv) != 5:
    print(
        "Usage: python processing/osm_analysis.py "
        "<west> <south> <east> <north>"
    )
    sys.exit(1)

try:
    west, south, east, north = map(float, sys.argv[1:5])
except ValueError:
    print("Error: Bounding box coordinates must be numbers.")
    sys.exit(1)

# Validate the selected bounding box
if not (
    -180 <= west < east <= 180
    and -90 <= south < north <= 90
):
    print("Error: Invalid bounding box coordinates.")
    sys.exit(1)

# Keep requests reasonably small for the demo
if east - west > 0.5 or north - south > 0.5:
    print("Error: Selected area is too large. Select a smaller area.")
    sys.exit(1)

os.makedirs("data/processed", exist_ok=True)

print("FloodRescue - OpenStreetMap Analysis", flush=True)
print(f"West: {west}, South: {south}", flush=True)
print(f"East: {east}, North: {north}", flush=True)

bbox = (west, south, east, north)

# 1. Download buildings
print("Downloading buildings...", flush=True)

buildings = ox.features_from_bbox(
    bbox=bbox,
    tags={"building": True}
)

buildings = buildings[buildings.geometry.notna()]
buildings.to_file(
    "data/processed/buildings.geojson",
    driver="GeoJSON"
)

print(f"Buildings downloaded: {len(buildings)}", flush=True)

# 2. Download the drivable road network
print("Downloading road network...", flush=True)

roads_graph = ox.graph_from_bbox(
    bbox=bbox,
    network_type="drive",
    simplify=True
)

# Save the graph for connectivity analysis
ox.save_graphml(
    roads_graph,
    filepath="data/processed/road_network.graphml"
)

roads = ox.graph_to_gdfs(
    roads_graph,
    nodes=False,
    edges=True
)

roads = roads[roads.geometry.notna()]
roads.to_file(
    "data/processed/roads.geojson",
    driver="GeoJSON"
)

print(f"Road segments downloaded: {len(roads)}", flush=True)

# 3. Extract bridges from the road data
print("Extracting bridges...", flush=True)

if "bridge" in roads.columns:
    bridges = roads[
        roads["bridge"].notna()
        & (roads["bridge"].astype(str).str.lower() != "no")
    ].copy()
else:
    bridges = roads.iloc[0:0].copy()

bridges.to_file(
    "data/processed/bridges.geojson",
    driver="GeoJSON"
)

print(f"Bridges found: {len(bridges)}", flush=True)

print("OpenStreetMap analysis completed.", flush=True)
