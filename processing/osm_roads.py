import os
import osmnx as ox

os.makedirs("data/processed", exist_ok=True)

# Smaller test area around Kathmandu
north = 27.75
south = 27.60
east = 85.45
west = 85.20

print("Downloading road network...")

roads_graph = ox.graph_from_bbox(
    bbox=(west, south, east, north),
    network_type="drive"
)

roads = ox.graph_to_gdfs(
    roads_graph,
    nodes=False,
    edges=True
)

print("Road segments:", len(roads))

roads.to_file(
    "data/processed/roads.geojson",
    driver="GeoJSON"
)
ox.save_graphml(
    roads_graph,
    "data/processed/road_network.graphml"
)

print("Saved: data/processed/road_network.graphml")
print("Saved: data/processed/roads.geojson")

# Find bridges
if "bridge" in roads.columns:
    bridges = roads[
        roads["bridge"].notna()
        & (roads["bridge"].astype(str) != "nan")
    ]
else:
    bridges = roads.iloc[0:0]

print("Bridges:", len(bridges))

bridges.to_file(
    "data/processed/bridges.geojson",
    driver="GeoJSON"
)

print("Saved: data/processed/bridges.geojson")
