from flask_restful import Api
from flask import Flask
import argparse
from .resources import Lidar, RawGPS, GPSPosition
import sqlalchemy as db
from .database import create


def main():
    dname = 'sqlite:////home/ccaruser/gpslidar3.db'

    # Create database
    create(dname)

    # Create application and api
    app = Flask(__name__)
    api = Api(app)

    # Add three resources to web server
    api.add_resource(Lidar, '/lidar/<string:loc>', resource_class_kwargs={'dname': dname})
    api.add_resource(RawGPS, '/rawgps/<string:loc>', resource_class_kwargs={'dname': dname})
    api.add_resource(GPSPosition, '/posgps/<string:loc>', resource_class_kwargs={'dname': dname})
    app.run(debug=False)  # Run web server
