from flask_restful import request, Resource, Api
from flask import Flask
import jwt
import datetime as dt
import numpy as np
import sys
from save import save_lidar, save_gps_pos, save_raw_gps


def read_key(fname):
    """ Function to read key from file. """
    try:
        with open(fname, 'r') as f:
            key = f.read()
    except FileNotFoundError:
        print('Incorrect key file location. ')
        sys.exit(0)
    return key


# Lookup table for keys
_LOOKUP_KEYS = {'harv': read_key('../../lidar-read/harv.key.pub')}


# Lookup table for latitude, longitude, and altitude
_LOOKUP_LATLONALT = {'harv': (34.468333 * np.pi / 180, (-120.671667 + 360) * np.pi / 180, 0)}


def decode_msg(m, loc):
    """ Function to decode message with the key. """
    try:
        time = jwt.decode(m, _LOOKUP_KEYS[loc], algorithm='RS256')['t']
        td = ((dt.datetime.utcnow() - dt.datetime(1970, 1, 1)).total_seconds() - float(time))
    except:
        return False
    if td < 10:
        return True
    return False


# Create application and api
app = Flask(__name__)
api = Api(app)
data_directory = '/home/ccaruser/data'  # Directory with data


class Lidar(Resource):
    """ Class for handling LiDAR post api request. """
    def post(self, loc):
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_lidar(request.data, data_directory, loc)
            print('LiDAR data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class RawGPS(Resource):
    """ Class for handling Raw GPS post api request. """
    def post(self, loc):
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            lat, lon, alt = _LOOKUP_LATLONALT[loc]
            save_raw_gps(request.data, data_directory, loc, lat, lon, alt)
            print('Raw GPS data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class GPSPosition(Resource):
    """ Class for handling GPS Position post api request. """
    def post(self, loc):
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_gps_pos(request.data, data_directory, loc)
            print('GPS Position data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


# Add three resources to web server
api.add_resource(Lidar, '/lidar/<string:loc>')
api.add_resource(RawGPS, '/rawgps/<string:loc>')
api.add_resource(GPSPosition, '/posgps/<string:loc>')

if __name__ == "__main__":
    app.run(debug=True)  # Run web server
