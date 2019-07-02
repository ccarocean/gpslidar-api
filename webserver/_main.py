from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import struct
import os
import jwt
import datetime as dt
import json


dname = 'sqlite:////home/ccaruser/gpslidar4.db'

# Create application and api
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = dname
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def read_key(fname):
    """ Function to read key from file. """
    try:
        with open(fname, 'r') as f:
            key = f.read()
    except FileNotFoundError:
        print('Incorrect key file location. ')
        os._exit(1)
    return key


def decode_msg(m, key):
    """ Function to decode message with the key. """
    try:
        time = jwt.decode(m, key, algorithm='RS256')['t']
        td = ((dt.datetime.utcnow() - dt.datetime(1970, 1, 1)).total_seconds() - float(time))
    except:
        return False
    if td < 10:
        return True
    return False


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


class gps_raw(db.Model):
    __tablename__ = 'gps_raw'
    id = db.Column('id', db.Integer, primary_key=True)
    rcv_tow = db.Column('rcv_tow', db.Integer(), nullable=False)
    week = db.Column('week', db.Integer(), nullable=False)
    leap_seconds = db.Column('leap_seconds', db.Integer(), nullable=False)
    station_id = db.Column('station_id',   db.Integer(), db.ForeignKey('stations.id'), nullable=False)

    def __init__(self, t, week, leap_s, sid):
        self.rcv_tow = t
        self.week = week
        self.leap_seconds = leap_s
        self.station_id = sid


class gps_measurement(db.Model):
    __tablename__ = 'gps_measurement'
    id = db.Column('id', db.Integer, primary_key=True)
    pseudorange = db.Column('pseudorange', db.Float(), nullable=False)
    carrier_phase = db.Column('carrier_phase', db.Float(), nullable=False)
    doppler_shift = db.Column('doppler_shift', db.Float(), nullable=False)
    gnss_id = db.Column('gnss_id', db.Integer(), nullable=False)
    sv_id = db.Column('sv_id', db.Integer(), nullable=False)
    signal_id = db.Column('signal_id', db.Integer(), nullable=False)
    cno = db.Column('cno', db.Integer(), nullable=False)
    gps_raw_id = db.Column('gps_raw_id', db.Integer(), db.ForeignKey('gps_raw.id'), nullable=False)

    def __init__(self, pr, cp, do, gnss_id, sv_id, sig_id, cno, gpsid):
        self.pseudorange = pr
        self.carrier_phase = cp
        self.doppler_shift = do
        self.gnss_id = gnss_id
        self.sv_id = sv_id
        self.signal_id = sig_id
        self.cno = cno
        self.gps_raw_id = gpsid


class gps_position(db.Model):
    __tablename__ = 'gps_position'
    id = db.Column('id', db.Integer(), primary_key=True)
    i_tow = db.Column('i_tow', db.Integer(), nullable=False)
    week = db.Column('week', db.Integer(), nullable=False)
    longitude = db.Column('longitude', db.Float(), nullable=False)
    latitude = db.Column('latitude', db.Float(), nullable=False)
    height = db.Column('height', db.Float(), nullable=False)
    station_id = db.Column('station_id', db.Integer(), db.ForeignKey('stations.id'), nullable=False)

    def __init__(self, itow, week, lon, lat, height, sid):
        self.i_tow = itow
        self.week = week
        self.longitude = lon
        self.latitude = lat
        self.height = height
        self.station_id = sid


@app.route('/lidar/<string:loc>', methods=['POST'])
def save_lidar(loc):
    """ Class for handling LiDAR post api request. """
    if request.method == 'POST' and len(request.data) > 8:
        key = read_key(stations.query.filter_by(name=loc).first().file_publickey)
        signature = request.headers['Bearer']

        if decode_msg(signature, key) and request.headers['Content-Type'] == "application/octet-stream":
            unix_time = struct.unpack('<q', request.data[0:8])[0]  # First thing is unix time
            num = (len(request.data) - 8) / 6  # Number of measurements
            sid = stations.query.filter_by(name=loc).first().id
            list_vals = []
            for i in range(int(num)):
                t, meas = struct.unpack('<LH', request.data[8 + i * 6:8 + (i + 1) * 6])  # Unpack data
                list_vals.append({'unix_time': unix_time + t * 10**-6, 'centimeters': meas, 'station_id': sid})

            db.session.bulk_insert_mappings(lidar, list_vals)
            db.session.commit()
            return '', 201
    return '', 404


@app.route('/rawgps/<string:loc>', methods=['POST'])
def save_rawgps(loc):
    if request.method == 'POST':
        key = read_key(stations.query.filter_by(name=loc).first().file_publickey)
        signature = request.headers['Bearer']

        if decode_msg(signature, key) and request.headers['Content-Type'] == "application/octet-stream":
            meas_list = []
            sid = stations.query.filter_by(name=loc).first().id

            counter = 0
            end = len(request.data)
            while counter < end:
                rcv_tow, week, leap_s, num_meas = struct.unpack('<dHbB', request.data[counter:counter+12])

                db.session.add(gps_raw(rcv_tow, week, leap_s, sid))
                db.session.flush()

                gpsid = gps_raw.query.filter_by(rcv_tow=rcv_tow, week=week).all()[-1].id

                counter += 12
                for i in range(num_meas):
                    pr, cp, do, other = struct.unpack('ddfH', request.data[counter:counter+22])
                    gnss_id = (other >> 12) & 0x07
                    sv_id = (other >> 6) & 0x3f
                    sig_id = (other >> 3) & 0x07
                    cno = other & 0x07
                    meas_list.append({'pseudorange': pr, 'carrier_phase': cp, 'doppler_shift': do, 'gnss_id': gnss_id,
                                     'sv_id': sv_id, 'signal_id': sig_id, 'cno': cno, 'gps_raw_id': gpsid})
                    counter += 22
            db.session.bulk_insert_mappings(gps_measurement, meas_list)
            db.session.commit()
            return '', 201
    return '', 404


@app.route('/posgps/<string:loc>', methods=['POST'])
def save_position(loc):
    if request.method == 'POST' and len(request.data) == 30:
        key = read_key(stations.query.filter_by(name=loc).first().file_publickey)
        signature = request.headers['Bearer']

        if decode_msg(signature, key) and request.headers['Content-Type'] == "application/octet-stream":
            sid = stations.query.filter_by(name=loc).first().id
            i_tow, week, lon, lat, height = struct.unpack('<IHddd', request.data)
            db.session.add(gps_position(i_tow, week, lon, lat, height, sid))
            db.session.commit()
            return '', 201
    return '', 404


def main():
    db.create_all()
    jsonfile = './stations.json'
    with open(jsonfile, 'r') as f:
        data = json.load(f)
    for i in data:
        if not stations.query.filter_by(name=i).first():
            db.session.add(stations(i, data[i]['latitude'], data[i]['longitude'], data[i]['altitude'],
                                    './keys/' + i + '.key.pub'))
            db.session.commit()
    app.run(debug=False)  # Run web server
