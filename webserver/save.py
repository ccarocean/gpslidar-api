import datetime as dt
import os
import struct
import sys
from .output import fix_hppos, RinexWrite
from .msg import RxmRawx


def save_lidar(data, data_directory, loc):
    """ Function for saving lidar data from API. """
    if len(data) < 8:
        print("No data in LiDAR packet. ")
        return
    unix_time = struct.unpack('<q', data[0:8])[0]  # First thing is unix time
    hour = dt.datetime(1970, 1, 1) + dt.timedelta(seconds=unix_time)  # Find day and hour
    t_vec, meas_vec = [], []  # Initialization
    num = (len(data)-8)/6  # Number of measurements
    for i in range(int(num)):
        t, meas = struct.unpack('<LH', data[8+i*6:8+(i+1)*6])  # Unpack data
        t_vec.append(hour + dt.timedelta(microseconds=t))
        meas_vec.append(meas)
    try:
        with open(os.path.join(data_directory, loc, 'lidar', hour.strftime('%Y-%m-%d.txt')), 'a+') as f:
            for i, j in zip(t_vec, meas_vec):
                f.write(f'{i} {j}\n')
    except FileNotFoundError:
        print("Data directory is bad. Try again. ")
        sys.exit(0)


def save_raw_gps(data, data_directory, loc, lat, lon, alt):
    """ Function for saving raw GPS data to a file. """
    # TODO: too slow
    counter = 0
    end = len(data)
    # Do the rinex thing
    while counter < end:
        rcv_tow, week, leap_s, num_meas = struct.unpack('<dHbB', data[counter:counter+12])
        counter += 12
        print('Save 40:', dt.datetime.utcnow())
        writer = RinexWrite(os.path.join(data_directory, loc, 'rawgps'), lat, lon, alt, week, rcv_tow, leap_s, loc)
        print('Save 42:', dt.datetime.utcnow())
        pseudorange, carrier_phase, doppler, gnss_id, sv_id, sig_id, cno = [], [], [], [], [], [], []
        for i in range(num_meas):
            pr, cp, do, other = struct.unpack('ddfH', data[counter:counter+22])
            counter += 22
            pseudorange.append(pr)
            carrier_phase.append(cp)
            doppler.append(do)
            gnss_id.append((other >> 12) & 0x07)
            sv_id.append((other >> 6) & 0x3f)
            sig_id.append((other >> 3) & 0x07)
            cno.append(other & 0x07)
        p = RxmRawx(rcv_tow, week, leap_s, num_meas, pseudorange, carrier_phase, doppler, gnss_id, sv_id, sig_id, cno)
        writer.write_data(p)


def save_gps_pos(data, data_directory, loc):
    """ Function for saving the gps position data. """
    if len(data) != 30:
        print("Data is incorrect. ")
        return
    i_tow, week, lon, lat, height = struct.unpack('<IHddd', data)
    t = dt.datetime(1980, 1, 6) + dt.timedelta(days=7*week, microseconds=i_tow*1000)
    f_name = os.path.join(data_directory, loc, 'position', t.strftime('%Y-%m-%d.txt'))
    if os.path.isfile(f_name):  # If file exists make sure it doesnt need to be fixed
        fix_hppos(f_name)
    try:
        with open(f_name, 'a+') as f:
            f.write(f'{t} {lat} {lon} {height}\n')  # Write to file
    except FileNotFoundError:
        print('Data directory is bad. Try again. ')
        sys.exit(0)
