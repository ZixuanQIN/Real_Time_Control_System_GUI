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



# smk multi-array electrode data acquisition program
# receive signal from device via bluetooth, then send to lsl
class SerialPort:
    serial_port = serial.Serial()
    BAUDRATE = 460800
    SAMPLINGRATE = 500
    CHANNEL_NUM = 32
    COMMAND = "AT+EMGCONFIG=FFFFFFFF,"+str(SAMPLINGRATE)+"\r\n"

    def __init__(self, serial_port=None):
        # self.port = serial.Serial(port, baud)
        try:
            self.find_port(serial_port)
        except:
            print("connection fail, please manualy connect to serial port")

        self.lsl = False
        self.outlet = None
        self.port_close()
        self.port_open()
        self.send_data(self.COMMAND)

    def find_port(self, serial_port:serial.tools.list_ports_common.ListPortInfo):
        if serial_port is None:
            print("serial_port is not correct, initial manual serial port selection.")

            while serial_port is None:
                comlist = list_ports.comports()
                id = 0
                for element in comlist:
                    if element:
                        id += 1
                        print("ID: " + str(id) + " -- Portname: " + str(element) + "\n")
                port = int(input("Enter a port number: "))
                if port - 1 < len(comlist):
                    serial_port = comlist[port-1]
                else:
                    print("Wrong serial port selected, try again")

            self.connect2port(serial_port[0])
        elif type(serial_port) is serial.tools.list_ports_common.ListPortInfo:
            self.connect2port(serial_port[0])
        else:
            pass

    def connect2port(self, serial_port):
        self.port = serial.Serial(serial_port, self.BAUDRATE)

    def port_open(self):
        if not self.port.isOpen():
            self.port.open()

    def port_close(self):
        self.port.close()

    def send_data(self, command):
        self.port.write(command.encode())

    def read_data(self):
        data = self.port.readline()
        return data

    def IEMG(self):
        time.sleep(.200)
        feedback = []
        
        self.port.write("AT+IEMGSTRT\r\n".encode())
        print("Start to acquire IEMG signal\n")
        self.start_lsl()

        try:
            while True:
                count = self.port.inWaiting()
                if count > 0:
                    answer = self.port.read(count)
                    data = []
                    for i in range(len(answer)):
                        data.append(answer[i])
                    data = np.hstack((feedback, data))
                    feedback = self.save(data, 0x71)
                    # self.save(data, 0x71)
        except KeyboardInterrupt:
            self.stop()
            
    def EMG(self):
        time.sleep(.200)
        feedback = []
        
        self.port.write("AT+EMGSTRT\r\n".encode())
        print("\n\033[1;31mStart to acquire raw EMG signal\033[0m\n")
        self.start_lsl()

        try:
            while True:
                count = self.port.inWaiting()
                if count > 0:
                    answer = self.port.read(count)
                    data = []
                    for i in range(len(answer)):
                        data.append(answer[i])
                    data = np.hstack((feedback, data))
                    feedback = self.save(data, 0x74)
                    # self.save(data, 0x71)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.port.write("AT+STOP\r\n".encode())
        print("\n\033[1;31mStop Successfully!\033[0m\n")

    def start_lsl(self):
        self.outlet = StreamOutlet(
            StreamInfo(
                'SMK Array EMG system', 
                'EMG', 
                self.CHANNEL_NUM, 
                self.BAUDRATE, 
                'int16', 
                'mysmk'
                )
            )
        self.lsl = True

    def save(self, data, id):
        data_len = len(data)

        i = 0
        while (i < data_len - 1):
            if data[i] == id and i + 70 <= data_len:
                data_set = data[i:i + 70]
                # seq = data_set[1] * 256 + data_set[2]
                iemg = data_set[3:67]
                trigger = []
                trigger.append(data_set[67])
                trigger.append(data_set[68])
                trigger.append(data_set[69])
                iemg_value = []
                for j, k in zip(iemg[0::2], iemg[1::2]):
                    iemg_value.append(int(j * 256 + k))

                DATA = np.array(iemg_value)
                DATA_str = list(map(lambda x: str(x), DATA))

                if int(trigger[0]) == 0 and int(trigger[1]) == 0 and int(trigger[2]) == 0:
                    try:
                        if self.lsl:
                            print(DATA)
                            self.outlet.push_sample(DATA)
                    except Exception as e:
                        raise e

                i = i + 70
            elif data[i] == id and i + 70 > data_len:
                return data[i:data_len]
            else:
                i = i + 1

if __name__ == '__main__':
    smk = SerialPort()
    smk.EMG()