from flask_restful import request, Resource
from .database import insert_rawgps, insert_pos, insert_lidar
import os
import jwt
import datetime as dt
import sqlite3


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
    print(key)
    #try:
    time = jwt.decode(m, key, algorithm='RS256')['t']
    td = ((dt.datetime.utcnow() - dt.datetime(1970, 1, 1)).total_seconds() - float(time))
    #except:
    #    return False
    if td < 10:
        return True
    return False


class Lidar(Resource):
    """ Class for handling LiDAR post api request. """
    def __init__(self, dname):
        self._dname = dname

    def post(self, loc):
        signature = request.headers['Bearer']
        with sqlite3.connect(self._dname) as conn:
            c = conn.cursor()
            c.execute('SELECT file_publickey FROM stations WHERE name=?', (loc,))
            key = read_key(c.fetchone()[0])

        if decode_msg(signature, key) and request.headers['Content-Type'] == "application/octet-stream":
            insert_lidar(request.data, self._dname, loc)
            print('LiDAR data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class RawGPS(Resource):
    """ Class for handling Raw GPS post api request. """
    def __init__(self, dname):
        self._dname = dname

    def post(self, loc):
        signature = request.headers['Bearer']
        with sqlite3.connect(self._dname) as conn:
            c = conn.cursor()
            c.execute('SELECT file_publickey FROM stations WHERE name=?', (loc,))
            key = read_key(c.fetchone()[0])

        if decode_msg(signature, key) and request.headers['Content-Type'] == "application/octet-stream":
            insert_rawgps(request.data, self._dname, loc)
            print('Raw GPS data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class GPSPosition(Resource):
    """ Class for handling GPS Position post api request. """
    def __init__(self, dname):
        self._dname = dname

    def post(self, loc):
        signature = request.headers['Bearer']
        with sqlite3.connect(self._dname) as conn:
            c = conn.cursor()
            c.execute('SELECT file_publickey FROM stations WHERE name=?', (loc,))
            key = read_key(c.fetchone()[0])

        if decode_msg(signature, key) and request.headers['Content-Type'] == "application/octet-stream":
            insert_pos(request.data, self._dname, loc)
            print('GPS Position data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?
