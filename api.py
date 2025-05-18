import heapq
from math import radians, cos, sin, asin, sqrt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from collections import OrderedDict

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
    distance = db.Column(db.Float, nullable=False)
    time = db.Column(db.Float, nullable=False)
    fuel = db.Column(db.Float, nullable=False)

# Graph loader with all weights
def build_graph():
    graph = {}
    edges = Edge.query.all()
    for edge in edges:
        if edge.from_node not in graph:
            graph[edge.from_node] = []
        graph[edge.from_node].append((edge.to_node, edge.distance, edge.time, edge.fuel))
    return graph

# Haversine heuristic
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return 6371 * c

def heuristic(node, goal):
    n1 = Node.query.filter_by(name=node).first()
    n2 = Node.query.filter_by(name=goal).first()
    return haversine(n1.latitude, n1.longitude, n2.latitude, n2.longitude) if n1 and n2 else float('inf')

# A* algorithm tracking all weights
def a_star_algorithm(graph, start, goal, metric):
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, [start], 0, 0, 0))  # f, g, node, path, dist, time, fuel
    visited = set()

    while open_set:
        f, g, current, path, total_dist, total_time, total_fuel = heapq.heappop(open_set)
        if current == goal:
            return path, total_dist, total_time, total_fuel
        if current in visited:
            continue
        visited.add(current)
        for neighbor, dist, time_, fuel in graph.get(current, []):
            if neighbor not in visited:
                new_dist = total_dist + dist
                new_time = total_time + time_
                new_fuel = total_fuel + fuel
                new_g = {'distance': new_dist, 'time': new_time, 'fuel': new_fuel}[metric]
                new_f = new_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor], new_dist, new_time, new_fuel))
    return None, 0, 0, 0

# API to get path with all weights
@app.route('/path/<string:metric>/<string:start>/<string:goal>')
def get_path(metric, start, goal):
    if metric not in ['distance', 'time', 'fuel']:
        return jsonify({'error': 'Invalid metric'}), 400

    graph = build_graph()
    path, total_dist, total_time, total_fuel = a_star_algorithm(graph, start, goal, metric)

    if path:
        response = OrderedDict()
        response['path'] = path
        response['distance'] = f"{round(total_dist, 2)} km"
        response['time'] = f"{round(total_time, 2)} hours"
        response['fuel'] = f"{round(total_fuel, 2)} liters"
        return jsonify(response)
    else:
        return jsonify({'error': 'No path found'}), 404

@app.route('/')
def root():
    return '<p>hello there!</p>'

if __name__ == '__main__':
    app.run(debug=True)
