from setuptools import setup, find_packages
import os
import re


def read(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as infile:
        text = infile.read()
    return text


def read_version(filename):
    return re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
            read(filename), re.MULTILINE).group(1)


setup(
    name='gpslidar-api',
    version=read_version('webserver/__init__.py'),
    author='Adam Dodge',
    author_email='Adam.Dodge@Colorado.edu',
    description='Set of tools for creating web server for receiving data from the GPS LiDAR system. ',
    long_description=read('README.rst'),
    scripts=['bin/gpslidar-api'],
    license='custom',
    url='https://github.com/ccarocean/gpslidar-api',
    packages=find_packages(),
    install_requires=[
        'pyjwt[crypto]',
        'flask',
        'flask_sqlalchemy',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: GIS'
    ],
    zip_safe=False
)
