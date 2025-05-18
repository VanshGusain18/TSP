from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

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
    road_type = db.Column(db.String(20), nullable=False)  # e.g., 'highway', 'street'

coordinates = {
    'A': (28.6139, 77.2090),
    'B': (28.7041, 77.1025),
    'C': (28.5355, 77.3910),
    'D': (28.4089, 77.3178),
    'E': (28.4595, 77.0266),
    'F': (28.9845, 77.7064),
    'G': (28.6692, 77.4538),
    'H': (28.9845, 77.7064),
    'I': (28.5355, 77.3910),
    'J': (28.4089, 77.3178)
}

edges = [
    ('A', 'B', 'street'), 
    ('A', 'C', 'highway'),
    ('B', 'C', 'street'), 
    ('B', 'D', 'street'),
    ('C', 'D', 'highway'), 
    ('C', 'F', 'highway'),
    ('D', 'E', 'street'), 
    ('E', 'G', 'street'),
    ('F', 'G', 'highway'), 
    ('F', 'H', 'highway'),
    ('G', 'I', 'street'), 
    ('H', 'I', 'highway'),
    ('I', 'J', 'street'), 
    ('H', 'J', 'street')
]

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # km

with app.app_context():
    db.drop_all()
    db.create_all()

    for name, (lat, lon) in coordinates.items():
        db.session.add(Node(name=name, latitude=lat, longitude=lon))

    db.session.commit()

    for from_n, to_n, road_type in edges:
        n1 = Node.query.filter_by(name=from_n).first()
        n2 = Node.query.filter_by(name=to_n).first()
        if n1 and n2:
            dist = round(haversine(n1.latitude, n1.longitude, n2.latitude, n2.longitude), 2)
            db.session.add(Edge(from_node=from_n, to_node=to_n, distance=dist, road_type=road_type))

    db.session.commit()
    print("Database initialized successfully!")
