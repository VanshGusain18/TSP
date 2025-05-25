import pandas as pd
import random

# Load node names from CSV
nodes_df = pd.read_csv("nodes.csv")
place_names = nodes_df["Place Name"].tolist()

# Road types to choose from
road_types = [
    'highway', 'street', 'rural',
    'mountain', 'offroad', 'expressway',
    'city_traffic', 'dirt_road'
]

edges_set = set()

# For each node, randomly connect to up to 10 unique other nodes
for node in place_names:
    possible_connections = [n for n in place_names if n != node]
    connections = random.sample(possible_connections, min(3, len(possible_connections)))

    for conn in connections:
        edge = tuple(sorted([node, conn]))  # to avoid duplicates like (A,B) and (B,A)
        edges_set.add(edge)

# Build final edge list with random road types
edges = [
    {"from": a, "to": b, "road_type": random.choice(road_types)}
    for a, b in edges_set
]

# Save to edges.csv
edges_df = pd.DataFrame(edges)
edges_df.to_csv("edges.csv", index=False)
print(f"✅ Created {len(edges)} undirected edges with random road types.")
