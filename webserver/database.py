import struct
import sqlalchemy as db


def create(dname):
    engine = db.create_engine(dname)
    metadata = db.MetaData()
    connection = engine.connect()
    if not engine.dialect.has_table(engine, 'stations'):
        stations = db.Table('stations', metadata,
                            db.Column('id',             db.Integer(),   primary_key=True),
                            db.Column('name',           db.String(4),   nullable=False),
                            db.Column('latitude',       db.Float(),     nullable=False),
                            db.Column('longitude',      db.Float(),     nullable=False),
                            db.Column('altitude',       db.Float(),     nullable=False),
                            db.Column('file_publickey', db.String(255), nullable=False)
                            )
        metadata.create_all(engine)
        query = db.insert(stations).values(name='harv', latitude=34.468333, longitude=239.328333, altitude=0,
                                           file_publickey='/home/ccaruser/.keys/harv.key.pub')
        ResultProxy = connection.execute(query)
        query = db.insert(stations).values(name='cata', latitude=33.445066, longitude=241.515673, altitude=0,
                                           file_publickey='/home/ccaruser/.keys/cata.key.pub')
        ResultProxy = connection.execute(query)
        query = db.insert(stations).values(name='ucbo', latitude=40.009874, longitude=254.755720, altitude=1600,
                                           file_publickey='/home/ccaruser/.keys/ucbo.key.pub')
        ResultProxy = connection.execute(query)
        print('Station Table Created')

    if not engine.dialect.has_table(engine, 'gps_raw'):
        gps_raw = db.Table('gps_raw', metadata,
                           db.Column('id',           db.Integer(), primary_key=True),
                           db.Column('rcv_tow',      db.Integer(), nullable=False),
                           db.Column('week',         db.Integer(), nullable=False),
                           db.Column('leap_seconds', db.Integer(), nullable=False),
                           db.Column('station_id',   db.Integer(), db.ForeignKey('stations.id'), nullable=False)
                           )
        metadata.create_all(engine)
        print('Raw GPS Table Created')

    if not engine.dialect.has_table(engine, 'gps_measurement'):
        gps_measurement = db.Table('gps_measurement', metadata,
                                   db.Column('id',            db.Integer(), primary_key=True),
                                   db.Column('pseudorange',   db.Float(),   nullable=False),
                                   db.Column('carrier_phase', db.Float(),   nullable=False),
                                   db.Column('doppler_shift', db.Float(),   nullable=False),
                                   db.Column('gnss_id',       db.Integer(), nullable=False),
                                   db.Column('sv_id',         db.Integer(), nullable=False),
                                   db.Column('signal_id',     db.Integer(), nullable=False),
                                   db.Column('cno',           db.Integer(), nullable=False),
                                   db.Column('gps_raw_id',    db.Integer(), db.ForeignKey('gps_raw.id'), nullable=False)
                                   )
        metadata.create_all(engine)
        print('Raw GPS Measurement Table Created')

    if not engine.dialect.has_table(engine, 'gps_position'):
        gps_position = db.Table('gps_position', metadata,
                                db.Column('id',         db.Integer(), primary_key=True),
                                db.Column('i_tow',      db.Integer(), nullable=False),
                                db.Column('week',       db.Integer(), nullable=False),
                                db.Column('longitude',  db.Float(),   nullable=False),
                                db.Column('latitude',   db.Float(),   nullable=False),
                                db.Column('height',     db.Float(),   nullable=False),
                                db.Column('station_id', db.Integer(), db.ForeignKey('stations.id'), nullable=False)
                                )
        metadata.create_all(engine)
        print('GPS Position Table Created')

    if not engine.dialect.has_table(engine, 'lidar'):
        lidar = db.Table('lidar', metadata,
                         db.Column('id',          db.Integer(), primary_key=True),
                         db.Column('unix_time',   db.Float(),   nullable=False),
                         db.Column('centimeters', db.Integer(), nullable=False),
                         db.Column('station_id',  db.Integer(), db.ForeignKey('stations.id'), nullable=False)
                         )
        metadata.create_all(engine)
        print('LiDAR Table Created')


def insert_lidar(data, stations, lidar, connection, loc):
    #engine = db.create_engine(dname)
    #metadata = db.MetaData()
    #connection = engine.connect()
    #stations = db.Table('stations', metadata, autoload=True, autoload_with=engine)
    #lidar = db.Table('lidar', metadata, autoload=True, autoload_with=engine)

    query = db.select([stations.columns.id]).where(stations.columns.name == loc)
    ResultProxy = connection.execute(query)
    sid = ResultProxy.fetchall()[0][0]

    query = db.insert(lidar)
    values_list = [] # [{'Id':'2', 'name':'ram', 'salary':80000, 'active':False},
                     #  {'Id':'3', 'name':'ramesh', 'salary':70000, 'active':True}]

    if len(data) > 8:
        unix_time = struct.unpack('<q', data[0:8])[0]  # First thing is unix time
        num = (len(data)-8)/6  # Number of measurements
        print(num)
        for i in range(int(num)):
            t, meas = struct.unpack('<LH', data[8+i*6:8+(i+1)*6])  # Unpack data
            values_list.append({'unix_time': unix_time+t*10**-6, 'centimeters': meas, 'station_id': sid})

        ResultProxy = connection.execute(query, values_list)


def insert_rawgps(data, dname, loc):
    engine = db.create_engine(dname)
    metadata = db.MetaData()
    connection = engine.connect()
    stations = db.Table('stations', metadata, autoload=True, autoload_with=engine)
    gps_raw = db.Table('gps_raw', metadata, autoload=True, autoload_with=engine)
    gps_measurement = db.Table('gps_measurement', metadata, autoload=True, autoload_with=engine)

    query = db.select([stations.columns.id]).where(stations.columns.name == loc)
    ResultProxy = connection.execute(query)
    sid = ResultProxy.fetchall()[0][0]

    counter = 0
    end = len(data)
    while counter < end:
        rcv_tow, week, leap_s, num_meas = struct.unpack('<dHbB', data[counter:counter+12])

        query = db.insert(gps_raw).values(rcv_tow=rcv_tow, week=week, leap_seconds=leap_s, station_id=sid)
        ResultProxy = connection.execute(query)

        query = db.select([gps_raw.columns.id]).where(
            gps_raw.columns.rcv_tow == rcv_tow and gps_raw.columns.week == week)
        ResultProxy = connection.execute(query)
        gpsid = ResultProxy.fetchall()[-1][0]

        counter += 12
        for i in range(num_meas):
            pr, cp, do, other = struct.unpack('ddfH', data[counter:counter+22])
            gnss_id = (other >> 12) & 0x07
            sv_id = (other >> 6) & 0x3f
            sig_id = (other >> 3) & 0x07
            cno = other & 0x07

            query = db.insert(gps_measurement).values(pseudorange=pr, carrier_phase=cp, doppler_shift=do,
                                                      gnss_id=gnss_id, sv_id=sv_id, signal_id=sig_id, cno=cno,
                                                      gps_raw_id=gpsid)
            ResultProxy = connection.execute(query)
            counter += 22


def insert_pos(data, dname, loc):
    engine = db.create_engine(dname)
    metadata = db.MetaData()
    connection = engine.connect()
    stations = db.Table('stations', metadata, autoload=True, autoload_with=engine)
    gps_position = db.Table('gps_position', metadata, autoload=True, autoload_with=engine)

    query = db.select([stations.columns.id]).where(stations.columns.name == loc)
    ResultProxy = connection.execute(query)
    sid = ResultProxy.fetchall()[0][0]

    if len(data) == 30:
        i_tow, week, lon, lat, height = struct.unpack('<IHddd', data)
        query = db.insert(gps_position).values(i_tow=i_tow, week=week, longitude=lon, latitude=lat, height=height,
                                               station_id=sid)
        ResultProxy = connection.execute(query)
