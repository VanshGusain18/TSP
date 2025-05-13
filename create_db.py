from api import app, db, Node, Edge
from math import radians, cos, sin, asin, sqrt

# Coordinates
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

# Edges (no weights needed now)
edges = [
    ('A', 'B'), ('A', 'C'),
    ('B', 'C'), ('B', 'D'),
    ('C', 'D'), ('C', 'F'),
    ('D', 'E'), ('E', 'G'),
    ('F', 'G'), ('F', 'H'),
    ('G', 'I'), ('H', 'I'),
    ('I', 'J'), ('H', 'J')
]

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # in km

with app.app_context():
    db.drop_all()
    db.create_all()

    for name, (lat, lon) in coordinates.items():
        if not Node.query.filter_by(name=name).first():
            db.session.add(Node(name=name, latitude=lat, longitude=lon))

    existing_edges = {(e.from_node, e.to_node) for e in Edge.query.all()}

    for from_n, to_n in edges:
        if (from_n, to_n) not in existing_edges:
            n1 = Node.query.filter_by(name=from_n).first()
            n2 = Node.query.filter_by(name=to_n).first()
            if n1 and n2:
                distance = round(haversine(n1.latitude, n1.longitude, n2.latitude, n2.longitude), 4)
                db.session.add(Edge(from_node=from_n, to_node=to_n, weight=distance))
                db.session.add(Edge(from_node=to_n, to_node=from_n, weight=distance))  # reverse edge

    db.session.commit()
