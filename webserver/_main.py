from flask_restful import Api
from flask import Flask
import argparse
from .resources import Lidar, RawGPS, GPSPosition
import sqlite3
from .database import create, insert_lidar, insert_pos, insert_rawgps


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, default='/home/ccaruser/data',
                        help='Directory for output data. Must have subdirectory for location, containing subdirectories'
                             ' for data types.')
    args = parser.parse_args()

    dname = '/home/ccaruser/gpslidar.db'

    # Create database
    with sqlite3.connect(dname) as conn:
        create(conn)

    # Create application and api
    app = Flask(__name__)
    api = Api(app)

    # Add three resources to web server
    api.add_resource(Lidar, '/lidar/<string:loc>', resource_class_kwargs={'dname': dname})
    api.add_resource(RawGPS, '/rawgps/<string:loc>', resource_class_kwargs={'dname': dname})
    api.add_resource(GPSPosition, '/posgps/<string:loc>', resource_class_kwargs={'dname': dname})
    app.run(debug=False)  # Run web server
