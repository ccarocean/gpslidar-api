from flask_restful import request, Resource, Api
from flask import Flask
import jwt
import datetime as dt
from save import save_lidar, save_gps_pos, save_raw_gps


def read_key(fname):
    with open(fname, 'r') as f:
        key = f.read()
    return key


keys = {'harv': read_key('../../lidar-read/harv.key.pub')}


def decode_msg(m, loc):
    time = jwt.decode(m, keys[loc], algorithm='RS256')['t']
    td = ((dt.datetime.utcnow() - dt.datetime(1970, 1, 1)).total_seconds() - float(time))
    print(td)
    if td < 10:
        return True
    return False


app = Flask(__name__)
api = Api(app)
data_directory = '/home/raspex/data'

class Lidar(Resource):
    def post(self, loc):
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_lidar(request.data, data_directory, loc)
            print('LiDAR data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class RawGPS(Resource):
    def post(self, loc):
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            print('Raw GPS data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?


class GPSPosition(Resource):
    def post(self, loc):
        signature = request.headers['Bearer']
        if decode_msg(signature, loc) and request.headers['Content-Type'] == "application/octet-stream":
            save_gps_pos(request.data, data_directory, loc)
            print('GPS Position data from ' + loc)
            return '', 201
        else:
            return '', 404  # What error should this be?

api.add_resource(Lidar, '/lidar/<string:loc>')
api.add_resource(RawGPS, '/rawgps/<string:loc>')
api.add_resource(GPSPosition, '/posgps/<string:loc>')

if __name__ == "__main__":
    app.run(debug=True)
