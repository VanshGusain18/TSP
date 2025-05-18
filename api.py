import heapq
from math import radians, cos, sin, asin, sqrt
from flask import Flask, request, jsonify, render_template
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
    road_type = db.Column(db.String(20), nullable=False)  # 'highway', 'street', etc.

road_speeds = {
    'highway': 100,  
    'street': 30,    
    'rural': 50,     
}

road_fuel_rates = {
    'highway': 0.05,  
    'street': 0.1,    
    'rural': 0.07,
}

def compute_time_and_fuel(distance, road_type):
    speed = road_speeds.get(road_type, 40)       
    fuel_rate = road_fuel_rates.get(road_type, 0.08)  
    time = distance / speed
    fuel = distance * fuel_rate
    return time, fuel

def build_graph():
    graph = {}
    edges = Edge.query.all()
    for edge in edges:
        time, fuel = compute_time_and_fuel(edge.distance, edge.road_type)
        if edge.from_node not in graph:
            graph[edge.from_node] = []
        graph[edge.from_node].append((edge.to_node, edge.distance, time, fuel))
    return graph

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return 6371 * c

def heuristic(node, goal, metric):
    n1 = Node.query.filter_by(name=node).first()
    n2 = Node.query.filter_by(name=goal).first()
    if not n1 or not n2:
        return float('inf')
    dist = haversine(n1.latitude, n1.longitude, n2.latitude, n2.longitude)
    if metric == 'distance':
        return dist
    elif metric == 'time':
        max_speed = max(road_speeds.values())
        return dist / max_speed
    elif metric == 'fuel':
        min_fuel_rate = min(road_fuel_rates.values())
        return dist * min_fuel_rate

def a_star_algorithm(graph, start, goal, metric):
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal, metric), 0, start, [start], 0, 0, 0))
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
                if metric == 'distance':
                    cost = dist
                elif metric == 'time':
                    cost = time_
                else:  # fuel
                    cost = fuel

                new_g_cost = g_cost + cost
                new_dist = total_dist + dist
                new_time = total_time + time_
                new_fuel = total_fuel + fuel
                new_f = new_g_cost + heuristic(neighbor, goal, metric)
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
    
@app.route('/get-graph')
def get_graph():
    nodes = Node.query.all()
    edges = Edge.query.all()

    node_index_map = {node.name: idx for idx, node in enumerate(nodes)}

    nodes_data = [{'x': node.longitude, 'y': node.latitude} for node in nodes]

    edges_data = []
    for edge in edges:
        if edge.from_node in node_index_map and edge.to_node in node_index_map:
            edges_data.append([node_index_map[edge.from_node], node_index_map[edge.to_node]])

    return jsonify({'nodes': nodes_data, 'edges': edges_data})


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
