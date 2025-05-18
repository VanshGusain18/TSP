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

# Graph loader
def build_graph():
    graph = {}
    edges = Edge.query.all()
    for edge in edges:
        if edge.from_node not in graph:
            graph[edge.from_node] = []
        graph[edge.from_node].append((edge.to_node, edge.distance, edge.time, edge.fuel))
    return graph

# Haversine heuristic (always distance-based)
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
    # Always return distance heuristic regardless of metric
    return haversine(n1.latitude, n1.longitude, n2.latitude, n2.longitude) if n1 and n2 else float('inf')

# A* algorithm: cost metric calculation fixed to always use distance for pathfinding cost
def a_star_algorithm(graph, start, goal, metric):
    open_set = []
    # f, g_cost (cost_so_far), current_node, path, total_dist, total_time, total_fuel
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, [start], 0, 0, 0))
    visited = set()

    while open_set:
        f, g_cost, current, path, total_dist, total_time, total_fuel = heapq.heappop(open_set)

        if current == goal:
            return path, total_dist, total_time, total_fuel

        if current in visited:
            continue
        visited.add(current)

        for neighbor, dist, time_, fuel in graph.get(current, []):
            if neighbor not in visited:
                # FIX: Always use distance as cost for comparison
                new_g_cost = g_cost + dist  # cost metric is always distance
                
                new_dist = total_dist + dist
                new_time = total_time + time_
                new_fuel = total_fuel + fuel
                
                new_f = new_g_cost + heuristic(neighbor, goal)
                heapq.heappush(open_set, (
                    new_f, new_g_cost, neighbor,
                    path + [neighbor],
                    new_dist, new_time, new_fuel
                ))

    return None, 0, 0, 0

# API route
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
