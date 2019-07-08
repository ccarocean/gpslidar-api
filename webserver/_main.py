from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import struct
import json
import jwt
import os
import datetime as dt


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


# Create application and api
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['GPSLIDAR_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class stations(db.Model):
    __tablename__ = 'stations'
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(4), nullable=False, unique=True)
    latitude = db.Column('latitude', db.Float(), nullable=False)
    longitude = db.Column('longitude', db.Float(), nullable=False)
    altitude = db.Column('altitude', db.Float(), nullable=False)
    file_publickey = db.Column('file_publickey', db.String(255), nullable=False)
    lidars = db.relationship('lidar', backref='station', lazy=True)
    gps_raws = db.relationship('gps_raw', backref='station', lazy=True)
    gps_positions = db.relationship('gps_position', backref='station', lazy=True)


class lidar(db.Model):
    __tablename__ = 'lidar'
    id = db.Column('id', db.Integer, primary_key=True)
    unix_time = db.Column('unix_time', db.Float(), nullable=False)
    centimeters = db.Column('centimeters', db.Integer(), nullable=False)
    station_id = db.Column('station_id', db.Integer, db.ForeignKey('stations.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('unix_time', 'station_id', name='time_station_lidar'),)


class gps_raw(db.Model):
    __tablename__ = 'gps_raw'
    id = db.Column('id', db.Integer, primary_key=True)
    rcv_tow = db.Column('rcv_tow', db.Float(), nullable=False)
    week = db.Column('week', db.Integer(), nullable=False)
    leap_seconds = db.Column('leap_seconds', db.Integer(), nullable=False)
    station_id = db.Column('station_id',   db.Integer(), db.ForeignKey('stations.id'), nullable=False)
    measurements = db.relationship('gps_measurement', backref='gps_raw', lazy=True)
    __table_args__ = (db.UniqueConstraint('rcv_tow', 'week', 'station_id', name='time_station_raw'),)


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
    __table_args__ = (db.UniqueConstraint('gps_raw_id', 'gnss_id', 'signal_id', name='sat_measurement'),)


class gps_position(db.Model):
    __tablename__ = 'gps_position'
    id = db.Column('id', db.Integer(), primary_key=True)
    i_tow = db.Column('i_tow', db.Integer(), nullable=False)
    week = db.Column('week', db.Integer(), nullable=False)
    longitude = db.Column('longitude', db.Float(), nullable=False)
    latitude = db.Column('latitude', db.Float(), nullable=False)
    height = db.Column('height', db.Float(), nullable=False)
    station_id = db.Column('station_id', db.Integer(), db.ForeignKey('stations.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('i_tow', 'week', 'station_id', name='time_station_pos'),)


@app.route('/lidar/<string:loc>', methods=['POST'])
def save_lidar(loc):
    """ Class for handling LiDAR post api request. """
    if len(request.data) > 8 and request.headers['Content-Type'] == "application/octet-stream":
        key = read_key(stations.query.filter_by(name=loc).first().file_publickey)
        signature = request.headers['Bearer']

        if decode_msg(signature, key):
            unix_time = struct.unpack('<q', request.data[0:8])[0]  # First thing is unix time
            num = (len(request.data) - 8) / 6  # Number of measurements
            sid = stations.query.filter_by(name=loc).first()
            if not sid:
                return '', 404
            sid = sid.id

            list_vals = []
            for i in range(int(num)):
                t, meas = struct.unpack('<LH', request.data[8 + i * 6:8 + (i + 1) * 6])  # Unpack data
                list_vals.append({'unix_time': unix_time + t * 10**-6, 'centimeters': meas, 'station_id': sid})
            try:
                db.session.bulk_insert_mappings(lidar, list_vals)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            return '', 201
        return '', 401
    return '', 400


@app.route('/rawgps/<string:loc>', methods=['POST'])
def save_rawgps(loc):
    key = read_key(stations.query.filter_by(name=loc).first().file_publickey)
    signature = request.headers['Bearer']

    if decode_msg(signature, key):
        if request.headers['Content-Type'] == "application/octet-stream":
            meas_list = []
            sid = stations.query.filter_by(name=loc).first()
            if not sid:
                return '', 404
            sid = sid.id

            counter = 0
            end = len(request.data)
            while counter < end:
                rcv_tow, week, leap_s, num_meas = struct.unpack('<dHbB', request.data[counter:counter+12])

                tmp = gps_raw(rcv_tow=rcv_tow, week=week, leap_seconds=leap_s, station_id=sid)
                db.session.add(tmp)
                db.session.flush()
                db.session.refresh(tmp)
                gpsid = tmp.id

                counter += 12
                for i in range(num_meas):
                    pr, cp, do, other = struct.unpack('ddfH', request.data[counter:counter+22])
                    gnss_id = (other >> 12) & 0x07
                    sv_id = (other >> 6) & 0x3f
                    sig_id = (other >> 3) & 0x07
                    cno = other & 0x07
                    print(gnss_id, sv_id, cno)
                    meas_list.append({'pseudorange': pr, 'carrier_phase': cp, 'doppler_shift': do, 'gnss_id': gnss_id,
                                     'sv_id': sv_id, 'signal_id': sig_id, 'cno': cno, 'gps_raw_id': gpsid})
                    counter += 22
            try:
                db.session.bulk_insert_mappings(gps_measurement, meas_list)
                db.session.commit()
            except IntegrityError as e:
                print(e)
                db.session.rollback()
                return '', 400
            return '', 201
        return '', 400
    return '', 401


@app.route('/posgps/<string:loc>', methods=['POST'])
def save_position(loc):
    if len(request.data) == 30 and request.headers['Content-Type'] == "application/octet-stream":
        key = read_key(stations.query.filter_by(name=loc).first().file_publickey)
        signature = request.headers['Bearer']

        if decode_msg(signature, key):
            sid = stations.query.filter_by(name=loc).first()
            if not sid:
                return '', 404
            sid = sid.id

            i_tow, week, lon, lat, height = struct.unpack('<IHddd', request.data)
            try:
                db.session.add(gps_position(i_tow=i_tow, week=week, longitude=lon, latitude=lat, height=height,
                                            station_id=sid))
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            return '', 201
        return '', 401
    return '', 400


def init_db(app, db):
    db.create_all()
    with app.app_context():
        jsonfile = './stations.json'
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        for i in data:
            if stations.query.filter_by(name=i).count() == 0:
                s = stations(name=i, latitude=data[i]['latitude'], longitude=data[i]['longitude'],
                             altitude=data[i]['altitude'], file_publickey='./keys/' + i + '.key.pub')
                try:
                    db.session.add(s)
                    db.session.commit()
                    print(f'added {i}')
                except IntegrityError:
                    db.session.rollback()
            else:
                s = stations.query.filter_by(name=i).one()

                db.session.add(s)
                db.session.commit()


init_db(app, db)


def main():
    app.run(debug=True)
