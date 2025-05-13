import heapq
from math import radians, cos, sin, asin, sqrt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)

# Models
class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

class Edge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_node = db.Column(db.String(1), db.ForeignKey('node.name'), nullable=False)
    to_node = db.Column(db.String(1), db.ForeignKey('node.name'), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Changed to Float

# Graph loader
graph = {}

def build_graph():
    global graph
    graph = {}
    edges = Edge.query.all()
    for edge in edges:
        if edge.from_node not in graph:
            graph[edge.from_node] = []
        graph[edge.from_node].append((edge.to_node, edge.weight))

# Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return 6371 * c  # Earth radius in km

def heuristic(node, goal):
    n1 = Node.query.filter_by(name=node).first()
    n2 = Node.query.filter_by(name=goal).first()
    if n1 and n2:
        return haversine(n1.latitude, n1.longitude, n2.latitude, n2.longitude)
    return float('inf')

# A* Algorithm
def a_star_algorithm(graph, start, goal):
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, [start]))
    visited = set()

    while open_set:
        f, g, current, path = heapq.heappop(open_set)

        if current == goal:
            return path, g

        if current in visited:
            continue
        visited.add(current)

        for neighbor, weight in graph.get(current, []):
            if neighbor not in visited:
                new_g = g + weight
                new_f = new_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor]))

    return None, float('inf')

# API Route
@app.route('/shortest_path/<string:start>/<string:goal>')
def get_shortest_path(start, goal):
    build_graph()
    path, cost = a_star_algorithm(graph, start, goal)
    if path:
        return jsonify({'path': path, 'cost': cost})
    else:
        return jsonify({'error': 'Path not found'}), 404

@app.route('/')
def root():
    return '<p>hello there hehe</p>'

if __name__ == '__main__':
    app.run(debug=True)
