import struct
import sqlite3


def create(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stations (id INTEGER PRIMARY KEY, 
name varchar[4] NOT NULL, latitude float NOT NULL, longitude float NOT NULL, 
altitude float NOT NULL, file_publickey text NOT NULL, UNIQUE (name, file_publickey));''')

    c.execute('''INSERT OR IGNORE INTO stations (name, latitude, longitude, altitude,  
file_publickey) VALUES ("harv", 34.468333, 239.328333, 
0, "/home/ccaruser/keys/harv.key.pub");''')

    c.execute('''INSERT OR IGNORE INTO stations (name, latitude, longitude, altitude, 
file_publickey) VALUES ("cata", 33.445066, 241.515673, 
0, "/home/ccaruser/keys/cata.key.pub");''')

    c.execute('''INSERT OR IGNORE INTO stations (name, latitude, longitude, altitude, 
file_publickey) VALUES ("ucbo", 40.009874, 254.755720, 
1600, "/home/ccaruser/keys/harv.key.pub");''')

    c.execute('''CREATE TABLE IF NOT EXISTS gps_raw (id INTEGER PRIMARY KEY, rcv_tow int NOT NULL,  
week int NOT NULL, leap_seconds int NOT NULL, station_id int NOT NULL, 
FOREIGN KEY (station_id) REFERENCES stations(id), UNIQUE (rcv_tow));''')

    c.execute('''CREATE TABLE IF NOT EXISTS gps_measurement (id INTEGER PRIMARY KEY, 
pseudorange double NOT NULL, carrier_phase double NOT NULL, 
doppler_shift float NOT NULL, gnss_id int NOT NULL, sv_id int NOT NULL, 
signal_id int NOT NULL, cno int NOT NULL, gps_raw_id int NOT NULL, 
FOREIGN KEY (gps_raw_id) REFERENCES gps_raw(id));''')

    c.execute('''CREATE TABLE IF NOT EXISTS gps_position (id INTEGER PRIMARY KEY, 
i_tow int NOT NULL, week int NOT NULL, longitude float NOT NULL, 
latitude float NOT NULL, height float NOT NULL, station_id int NOT NULL, 
FOREIGN KEY (station_id) REFERENCES stations(id), UNIQUE (i_tow));''')

    c.execute('''CREATE TABLE IF NOT EXISTS lidar (id INTEGER PRIMARY KEY, unix_time double NOT NULL,  
centimeters int NOT NULL, station_id int NOT NULL, FOREIGN KEY (station_id) REFERENCES stations(id), 
UNIQUE (unix_time));''')

    conn.commit()


def insert_lidar(data, dname, loc):
    sql = ''' INSERT INTO lidar (unix_time, centimeters, station_id) VALUES (?,?,?);'''
    with sqlite3.connect(dname) as conn:
        c = conn.cursor()
        c.execute('''SELECT id FROM stations WHERE name=?''', loc)
        sid = c.fetchone()

        if len(data) > 8:
            unix_time = struct.unpack('<q', data[0:8])[0]  # First thing is unix time
            num = (len(data)-8)/6  # Number of measurements
            for i in range(int(num)):
                t, meas = struct.unpack('<LH', data[8+i*6:8+(i+1)*6])  # Unpack data
                c.execute(sql, (unix_time + t * 10**-6, meas, sid))  # Insert into database
            conn.commit()


def insert_rawgps(data, dname, loc):
    sql_main = ''' INSERT INTO gps_raw (rcv_tow, week, leap_seconds, station_id) VALUES (?,?,?,?);'''
    sql_meas = ''' INSERT INTO gps_measurement (pseudorange, carrier_phase, doppler_shift, gnss_id, sv_id, signal_id, 
cno, gps_raw_id) VALUES (?,?,?,?,?,?,?,?);'''
    with sqlite3.connect(dname) as conn:
        c = conn.cursor()
        c.execute('''SELECT id FROM stations WHERE name=?''', loc)
        sid = c.fetchone()

        counter = 0
        end = len(data)
        while counter < end:
            rcv_tow, week, leap_s, num_meas = struct.unpack('<dHbB', data[counter:counter+12])
            c.execute(sql_main, (rcv_tow, week, leap_s, sid))
            c.execute('''SELECT id FROM gps_raw WHERE rcv_tow=? AND week=?''', (rcv_tow, week))
            gpsid = c.fetchone()
            counter += 12
            for i in range(num_meas):
                pr, cp, do, other = struct.unpack('ddfH', data[counter:counter+22])
                gnss_id = (other >> 12) & 0x07
                sv_id = (other >> 6) & 0x3f
                sig_id = (other >> 3) & 0x07
                cno = other & 0x07
                c.execute(sql_meas, (pr, cp, do, gnss_id, sv_id, sig_id, cno, gpsid))
                counter += 22
        conn.commit()


def insert_pos(data, dname, loc):
    sql = '''INSERT INTO gps_position (i_tow, week, longitude, latitude, height, station_id) VALUES (?,?,?,?,?,?);'''
    with sqlite3.connect(dname) as conn:
        c = conn.cursor()
        c.execute('''SELECT id FROM stations WHERE name=?''', loc)
        sid = c.fetchone()

        if len(data) == 30:
            i_tow, week, lon, lat, height = struct.unpack('<IHddd', data)
            c.execute(sql, (i_tow, week, lon, lat, height, sid))
        conn.commit()
