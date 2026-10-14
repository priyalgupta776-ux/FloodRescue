import networkx as nx

graph = nx.read_graphml(
    "data/processed/road_network.graphml"
)

print("Road network loaded.")
print("Nodes:", len(graph.nodes))
print("Edges:", len(graph.edges))
