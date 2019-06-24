from abc import ABC
from dataclasses import dataclass
from collections import defaultdict


_LOOKUP_GPS = {0: 'G', 1: 'S', 2: 'E', 3: 'C', 6: 'R'}


def x2bool(num, val):
    return tuple((val & 2**i) != 0 for i in range(num-1, -1, -1))


class Packet(ABC):
    id = 0x0000
    longname = 'Unknown Packet'


class ReceivedPacket(Packet, ABC):
    pass


@dataclass(frozen=True)
class RxmRawxData:
    prMeas: float
    cpMeas: float
    doMeas: float
    gnssId: int
    svId: int
    sigId: int
    freqId: int
    locktime: int
    cno: int
    prStdev: float
    cpStdev: float
    doStdev: float
    subHalfCyc: bool
    halfCyc: bool
    cpValid: bool
    prValid: bool
    key: str


class RxmRawx(ReceivedPacket):
    id = 0x1502
    longname = 'Multi GNSS raw measurement data'

    def __init__(self, rcvTOW, week, leapS, numMeas, pseudorange, carrier_phase, doppler, gnssId, svId, sigId, cno):
        self._rcvTow = float(rcvTOW)
        self._week = int(week)
        self._leapS = int(leapS)
        self._numMeas = numMeas
        dc = []

        for i in range(self._numMeas):
            id_ = _LOOKUP_GPS[gnssId[i]]
            if id_ == 'R' and svId[i] == 255:
                key = ''
            else:
                if id_ == 'S':
                    id2 = svId[i] - 100
                else:
                    id2 = svId[i]
                key = f'{id_}{id2:02d}'

            dc.append(RxmRawxData(pseudorange[i], carrier_phase[i], doppler[i], gnssId[i], svId[i], sigId[i], cno[i],
                                        key))
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
        return [sat for sublist in self._satellites for sat in sublist]
