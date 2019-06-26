from flask_restful import Api
from flask import Flask
import argparse
from .resources import Lidar, RawGPS, GPSPosition


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, default='/home/ccaruser/data',
                        help='Directory for output data. Must have subdirectory for location, containing subdirectories'
                             ' for data types.')
    args = parser.parse_args()

    # Create application and api
    app = Flask(__name__)
    api = Api(app)

    # Add three resources to web server
    api.add_resource(Lidar, '/lidar/<string:loc>')#, resource_class_kwargs={'dir': args.directory})
    api.add_resource(RawGPS, '/rawgps/<string:loc>')#, resource_class_kwargs={'dir': args.directory})
    api.add_resource(GPSPosition, '/posgps/<string:loc>')#, resource_class_kwargs={'dir': args.directory})
    app.run(debug=True)  # Run web server
