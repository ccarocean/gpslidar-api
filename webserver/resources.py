from flask_restful import request, Resource
from .save import save_lidar, save_gps_pos, save_raw_gps
import sys
import jwt
import datetime as dt

def read_key(fname):
    """ Function to read key from file. """
    try:
        with open(fname, 'r') as f:
            key = f.read()
    except FileNotFoundError:
        print('Incorrect key file location. ')
        sys.exit(0)
    return key


# Station lookup
_STATIONS = {'harv': {'public-key':   read_key('../../lidar-read/harv.key.pub'),
                      'private-key':  read_key('../../lidar-read/harv.key'),
                      'lat':          34.468333,
                      'lon':          360 - 120.671667,
                      'alt':          0
                      }
             }


def decode_msg(m, loc):
    """ Function to decode message with the key. """
    try:
        time = jwt.decode(m, _STATIONS[loc]['public-key'], algorithm='RS256')['t']
        td = ((dt.datetime.utcnow() - dt.datetime(1970, 1, 1)).total_seconds() - float(time))
    except:
        return False
    if td < 10:
        return True
    return False


class Lidar(Resource):
    """ Class for handling LiDAR post api request. """
    def post(self, loc, **kwargs):
        data_directory = kwargs['dir']
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_lidar(request.data, data_directory, loc)
            print('LiDAR data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class RawGPS(Resource):
    """ Class for handling Raw GPS post api request. """
    def post(self, loc, **kwargs):
        data_directory = kwargs['dir']
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_raw_gps(request.data, data_directory, loc,
                         _STATIONS[loc]['lat'], _STATIONS[loc]['lon'], _STATIONS[loc]['alt'])
            print('Raw GPS data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class GPSPosition(Resource):
    """ Class for handling GPS Position post api request. """
    def post(self, loc, **kwargs):
        data_directory = kwargs['dir']
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_gps_pos(request.data, data_directory, loc)
            print('GPS Position data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?
