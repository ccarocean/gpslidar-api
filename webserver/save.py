import datetime as dt
import os
import struct
from output import fix_hppos, RinexWrite
from msg import RxmRawx


def save_lidar(data, data_directory, loc):
    unix_time = struct.unpack('<q', data[0:8])[0]
    dayhour = dt.datetime(1970, 1, 1) + dt.timedelta(seconds=unix_time)
    tvec, measvec = [], []
    num = (len(data)-8)/6
    for i in range(int((len(data)-8)/6)):
        t, meas = struct.unpack('<LH', data[8+i*6:8+(i+1)*6])
        tvec.append(t)
        measvec.append(meas)
    with open(os.path.join(data_directory, loc, 'lidar', dayhour.strftime('%Y-%m-%d.txt')), 'a+') as f:
        for i, j in zip(tvec, measvec):
            f.write(f'{i} {j}\n')


def save_raw_gps(data, data_directory, loc, lat, lon, alt):
    unix_time = struct.unpack('<q', data[0:8])[0]
    dayhour = dt.datetime(1970, 1, 1) + dt.timedelta(seconds=unix_time)
    counter = 8
    while counter < len(data):
        rcvTOW, week, leapS, numMeas = struct.unpack('<dHbB', data[counter:counter+12])
        counter = counter+12
        wrtr = RinexWrite(os.path.join(data_directory, loc, 'rawgps'), lat, lon, alt, week, rcvTOW, leapS, loc)
        pseudorange, carrier_phase, doppler, gnssId, svId, sigId, cno = ([] for i in range(7))
        for i in range(numMeas):
            pr, cp, do, other = struct.unpack('ddfH', data[counter:counter+22])
            counter = counter + 22
            pseudorange.append(pr)
            carrier_phase.append(cp)
            doppler.append(do)
            gnssId.append((other >> 12) & 0x07)
            svId.append((other >> 6) & 0x3f)
            sigId.append((other >> 3) & 0x07)
            cno.append(other & 0x07)
        p = RxmRawx(rcvTOW, week, leapS, numMeas, pseudorange, carrier_phase, doppler, gnssId, svId, sigId, cno)
        wrtr.write_data(p)


def save_gps_pos(data, data_directory, loc):
    unix_time, itow, week, lon, lat, height = struct.unpack('<qIHddd', data)
    dayhour = dt.datetime(1970, 1, 1) + dt.timedelta(seconds=unix_time)
    t = dt.datetime(1980, 1, 6) + \
        dt.timedelta(days=7*week) + \
        dt.timedelta(seconds=itow)
    today = dt.datetime(t.year, t.month, t.day)
    secs = (t-today).total_seconds()
    fname = os.path.join(data_directory, loc, 'position', dayhour.strftime('%Y-%m-%d.txt'))
    print(fname)
    if os.path.isfile(fname):
        fix_hppos(fname)
    with open(fname, 'a+') as f:
        f.write(f'{secs} {lat} {lon} {height}\n')
