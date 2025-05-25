import csv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

class Edge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_node = db.Column(db.String(100), db.ForeignKey('node.name'), nullable=False)
    to_node = db.Column(db.String(100), db.ForeignKey('node.name'), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    road_type = db.Column(db.String(20), nullable=False)

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  

with app.app_context():
    db.drop_all()
    db.create_all()

    with open('nodes.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Place Name'].strip()
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            db.session.add(Node(name=name, latitude=lat, longitude=lon))
        db.session.commit()

    with open('edges.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            from_name = row['from'].strip()
            to_name = row['to'].strip()
            road_type = row['road_type'].strip()

            from_node = Node.query.filter_by(name=from_name).first()
            to_node = Node.query.filter_by(name=to_name).first()

            if from_node and to_node:
                dist = round(haversine(from_node.latitude, from_node.longitude,
                                    to_node.latitude, to_node.longitude), 2)
                
                db.session.add(Edge(from_node=from_name, to_node=to_name,
                                    distance=dist, road_type=road_type))
                db.session.add(Edge(from_node=to_name, to_node=from_name,
                                    distance=dist, road_type=road_type))
        db.session.commit()


    print("Database initialized from CSV files successfully!")
