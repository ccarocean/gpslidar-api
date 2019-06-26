from abc import ABC
from dataclasses import dataclass
from collections import defaultdict


# Lookup table for GPS codes
_LOOKUP_GPS = {0: 'G', 1: 'S', 2: 'E', 3: 'C', 6: 'R'}


class Packet(ABC):
    """ Packet class for inheritance. """
    id = 0x0000
    longname = 'Unknown Packet'


class ReceivedPacket(Packet, ABC):
    """ Received packet class for inheritance. """
    pass


@dataclass(frozen=True)
class RxmRawxData:
    """ Dataclass for raw measurement data from single satellite. """
    prMeas: float
    cpMeas: float
    doMeas: float
    gnssId: int
    svId: int
    sigId: int
    cno: int
    key: str


class RxmRawx(ReceivedPacket):
    """ Class for handling raw data packet from api and returning a data structure containing an entire measurement. """
    id = 0x1502
    longname = 'Multi GNSS raw measurement data'

    def __init__(self, rcvTOW, week, leapS, numMeas, pseudorange, carrier_phase, doppler, gnssId, svId, sigId, cno):
        self._rcvTow = rcvTOW
        self._week = week
        self._leapS = leapS
        self._numMeas = numMeas
        dc = []

        for i in range(self._numMeas):
            # Create key for RINEX
            id_ = _LOOKUP_GPS[gnssId[i]]
            if id_ == 'R' and svId[i] == 255:
                key = ''
            else:
                if id_ == 'S':
                    id2 = svId[i] - 100
                else:
                    id2 = svId[i]
                key = f'{id_}{id2:02d}'

            # Add dataclass for satellite data to list
            dc.append(RxmRawxData(pseudorange[i], carrier_phase[i], doppler[i], gnssId[i], svId[i], sigId[i], cno[i],
                                        key))

        # Sort list based on satellite and combine L1 and L2 measurements for same satellite.
        dd = defaultdict(list)
        self._satellites = []
        for i in dc:
            dd[i.key].append(i)
        for i in dd.items():
            i[1].sort(key=lambda x: x.sigId)
            self._satellites.append(i[1])
        self._satellites.sort(key=lambda x: x[0].key)

    def __str__(self):
        return (f'Received Packet:     {self.longname}, ID: {self.id}\n' 
                f'Receiver Time of Week:    {self.rcvTow}\n' 
                f'Week Number               {self.week}\n' 
                f'Leap Second offset:       {self.leapS}\n' 
                f'Number of Measurements:   {self.numMeas}\n' 
                f'Leap seconds determined?: {self.leapSecBool}\n'
                f'Clock reset applied?:     {self.clkResetBool}\n'
                f'Satellite Measurements:   {self.satellites}\n')

    @property
    def rcvTow(self):
        return self._rcvTow

    @property
    def week(self):
        return self._week

    @property
    def leapS(self):
        return self._leapS

    @property
    def numMeas(self):
        return self._numMeas

    @property
    def satellites(self):
        return self._satellites
