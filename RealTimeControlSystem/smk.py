#!/usr/bin/python3
# -*-coding: utf-8 -*-

"""
- SMK LSL acquisition system v2.1 -

written by @QIN ZIXUAN
update: 2022/05/13
qin.z.aa@m.titech.ac.jp
Tokyo Institute of Technology

"""

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    raise RuntimeError('cannot import serial, make sure serial package is installed')

try:
    from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
except ImportError:
    raise RuntimeError('cannot import pylsl, make sure pylsl package is installed')

from datetime import datetime
import numpy as np
import time
from module.tools import KoikeParameters, KoikeFilter, Params, MVC_normalize

"""
"SIGNAL" is a module while using Real-Time-Control-System.
If only use this file to acquire EMG signal, you can use "python smk.py" directly
or just import the whole file to python and call the "SerialPort"
"""
class SIGNAL:
    def __init__(self):
        self.koike_params = KoikeParameters(Params.SLIDING_WINDOW_LEN)
        # self.lsl()
        self.data()

    def lsl(self):
        self.streams = resolve_stream('type','EMG')
        self.inlet = StreamInlet(self.streams[0])

    def data(self):
        self.MVC_RUN = False
        self.initMVC()

        # EMG data
        self.emg_data = np.zeros((Params.SAMPLING_RATE_EMG, Params.EMG_ch))
        self.emg_Filtered, self.koike_params['zf'] = KoikeFilter(self.emg_data, self.koike_params)
        self.emg_Filtered = MVC_normalize(self.emg_Filtered, self.MVC_min, self.MVC_max)
        self.EMG_DATA = self.emg_data

        # ANGLE data
        self.ANGLE_DATA = np.zeros((Params.SAMPLING_RATE_ANGLE, Params.ANGLE_ch))
        self.ANGLE_DATA_KALMAN = np.zeros((Params.SAMPLING_RATE_ANGLE, Params.ANGLE_ch))

    def GET_EMG_LSL(self):
        EMG = []
        for t in range(Params.SLIDING_WINDOW_LEN):
            sample, timestamp = self.inlet.pull_sample()
            EMG.append(sample)

        return np.array(EMG)

    def initMVC(self):
        self.MVC_min = np.zeros((1, Params.EMG_ch))
        self.MVC_max = np.zeros((1, Params.EMG_ch))
        self.MVC = (np.zeros((1, Params.EMG_ch)))
        self.MVC_stopped = False


"""
Due to the Confidential Agreement, the AT Commands of multi-array eletrode are secret.
We deleted the class named "SerialPort". Please build your own EMG acquisition program 
based on LSL.
"""


# if __name__ == '__main__':
    #smk = SerialPort()
    #smk.EMG()