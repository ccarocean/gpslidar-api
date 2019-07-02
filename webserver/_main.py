from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import struct


dname = 'sqlite:////home/ccaruser/gpslidar3.db'  # ?check_same_thread=False'

# Create application and api
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = dname
db = SQLAlchemy(app)


class stations(db.Model):
    __tablename__ = 'stations'
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(4), nullable=False)
    latitude = db.Column('latitude', db.Float(), nullable=False)
    longitude = db.Column('longitude', db.Float(), nullable=False)
    altitude = db.Column('altitude', db.Float(), nullable=False)
    file_publickey = db.Column('file_publickey', db.String(255), nullable=False)

    def __init__(self, name, lat, lon, alt, f):
        self.name = name
        self.latitude = lat
        self.longitude = lon
        self.altitude = alt
        self.file_publickey = f


class lidar(db.Model):
    __tablename__ = 'lidar'
    id = db.Column('id', db.Integer, primary_key=True)
    unix_time = db.Column('unix_time', db.Float(), nullable=False)
    centimeters = db.Column('centimeters', db.Integer(), nullable=False)
    station_id = db.Column('station_id', db.Integer, db.ForeignKey('stations.id'), nullable=False)

    def __init__(self, t, cm, sid):
        self.unix_time = t
        self.centimeters = cm
        self.station_id = sid


@app.route('/lidar/<string:loc>', methods=['POST'])
def save_lidar(loc):
    """ Class for handling LiDAR post api request. """
    if request.method == 'POST' and len(request.data) > 8:
        unix_time = struct.unpack('<q', request.data[0:8])[0]  # First thing is unix time
        num = (len(request.data)-8)/6  # Number of measurements
        sid = stations.query.filter_by(name=loc).first().id
        for i in range(int(num)):
            t, meas = struct.unpack('<LH', request.data[8+i*6:8+(i+1)*6])  # Unpack data
            db.session.add(lidar(unix_time + t*10**-6, meas, sid))
        db.session.commit()


def main():

    '''
    # Create database
    engine = db.create_engine(dname)
    metadata = db.MetaData()
    connection = engine.connect()
    create(engine, metadata, connection)
    stations = db.Table('stations', metadata, autoload=True, autoload_with=engine)
    lidar = db.Table('lidar', metadata, autoload=True, autoload_with=engine)
    gps_raw = db.Table('gps_raw', metadata, autoload=True, autoload_with=engine)
    gps_measurement = db.Table('gps_measurement', metadata, autoload=True, autoload_with=engine)
    gps_position = db.Table('gps_position', metadata, autoload=True, autoload_with=engine)



    # Add three resources to web server
    api.add_resource(Lidar, '/lidar/<string:loc>', resource_class_kwargs={'stations': stations, 'lidar': lidar,
                                                                          'connection': connection})
    api.add_resource(RawGPS, '/rawgps/<string:loc>', resource_class_kwargs={'stations': stations, 'gps_raw': gps_raw,
                                                                            'gps_measurement': gps_measurement,
                                                                            'connection': connection})
    api.add_resource(GPSPosition, '/posgps/<string:loc>', resource_class_kwargs={'stations': stations,
                                                                                 'gps_position': gps_position,
                                                                                 'connection': connection})
    '''
    db.create_all()
    app.run(debug=False)  # Run web server
