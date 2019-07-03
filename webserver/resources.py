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