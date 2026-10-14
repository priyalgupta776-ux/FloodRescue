
import networkx as nx
import geopandas as gpd
import osmnx as ox
import os

print("Loading road network...")
graph = ox.load_graphml("data/processed/road_network.graphml")

print("Loading affected roads...")
roads = gpd.read_file("data/processed/affected_roads.geojson")

print("Loading settlements...")
settlements = gpd.read_file("data/processed/settlements.geojson")
settlements = settlements.to_crs("EPSG:4326")

print("Loading hospitals...")
hospitals = gpd.read_file("data/processed/hospitals.geojson")
hospitals = hospitals.to_crs("EPSG:4326")

settlement_points = settlements.geometry.representative_point()
hospital_points = hospitals.geometry.representative_point()

settlement_nodes = list(ox.nearest_nodes(
    graph, X=settlement_points.x, Y=settlement_points.y
))

hospital_nodes = list(ox.nearest_nodes(
    graph, X=hospital_points.x, Y=hospital_points.y
))

# Find settlements that can reach a hospital BEFORE disruption
print("Checking normal road network...")
normal_reachable = set(
    nx.multi_source_dijkstra_path_length(
        graph.reverse(copy=False),
        set(hospital_nodes),
        weight="length"
    ).keys()
)

# Create a separate network for the flood simulation
flood_graph = graph.copy()

print("Removing flood-affected road edges...")
removed = 0

for _, road in roads.iterrows():
    if all(column in roads.columns for column in ["u", "v", "key"]):
        u, v, key = int(road["u"]), int(road["v"]), int(road["key"])

        if flood_graph.has_edge(u, v, key):
            flood_graph.remove_edge(u, v, key)
            removed += 1

print("Edges removed:", removed)

# Find settlements that can reach a hospital AFTER disruption
print("Checking disrupted road network...")
flood_reachable = set(
    nx.multi_source_dijkstra_path_length(
        flood_graph.reverse(copy=False),
        set(hospital_nodes),
        weight="length"
    ).keys()
)

# Only count settlements connected before but disconnected afterwards
cut_off_indices = []

for i, node in enumerate(settlement_nodes):
    if node in normal_reachable and node not in flood_reachable:
        cut_off_indices.append(i)

cut_off = settlements.iloc[cut_off_indices].copy()

os.makedirs("data/outputs", exist_ok=True)

cut_off.to_file(
    "data/outputs/potentially_cut_off_settlements.geojson",
    driver="GeoJSON"
)

print()
print("========== CONNECTIVITY RESULTS ==========")
print("Settlements assessed:", len(settlements))
print("Connected to a hospital before:", sum(
    node in normal_reachable for node in settlement_nodes
))
print("Connected to a hospital after:", sum(
    node in flood_reachable for node in settlement_nodes
))
print("Newly potentially cut-off settlements:", len(cut_off))
print("Affected edges removed:", removed)
print("Saved: data/outputs/potentially_cut_off_settlements.geojson")

for index in cut_off_indices:
    print(settlements.iloc[index].geometry)

