#!/usr/bin/python3
# -*-coding: utf-8 -*-

"""
QT packages
"""
try:
	from PyQt5.Qt import *
	from pyqtgraph.Qt import QtCore, QtGui
	from PyQt5 import QtWidgets
	import pyqtgraph as pq
except ImportError:
	raise RuntimeError(
		'cannot import all necessary \033[1;31mpyqt5\033[0m packages, make sure they are installed.'
		)

"""
lsl package
"""
try:
	from pylsl import StreamInlet, resolve_stream
except ImportError:
	raise RuntimeError(
		'Can not import \033[1;31mpylsl\033[0m, make sure \033[1;31mpylsl\033[0m package is installed.'
		)

"""
torch
"""
try:
	import torch
except ImportError:
    raise RuntimeError('cannot import torch packages, make sure pytorch was installed')

"""
another packages
"""
import sys
import warnings
warnings.filterwarnings("ignore")
import os
import platform
from module.tools import *
from smk import SIGNAL
from module.CW_CNN import CNN
import numpy as np
from pylsl import StreamInfo, StreamOutlet
import time
import scipy.io as io

class DataMonitor(QWidget, SIGNAL):
	"""
	DataMonitor: 
	The initial window to show EMG signal and angle data in real-time.
	Signals will be received by pylsl
	"""

	def __init__(self, app):
		self.app = app
		self.datatype = Params.DATA_TYPE_RAW
		self.receiving_lsl = False
		self.start_angle_prediction = False
		self.start_to_control_robot = False
		self.trigger = [Params.TRIGGER_NOT_REALTIME]
		self.temp_angles = [0, 0, 0]
		self.temp_kalman = []

		SIGNAL().__init__()
		super().__init__()
		self._window_setting()
		self._push_button_setting()
		self._layout_setting()
		self._addPlot()
		self._curve()
		self._timer()

	def lsl_outlet(self):
		self.outlet_trigger = StreamOutlet(
			StreamInfo(
				'Stimulus PC Real Time', 
				'Trigger', 
				1, 
				0, 
				'int16', 
				'trigger'
				)
			)
		self.outlet_angles = StreamOutlet(
			StreamInfo(
				'Estimated Angle', 
				'Estimated Angle', 
				3, 
				100, 
				'float32', 
				'Estimated Angle'
				)
			)
		self.outlet_angles_kalman = StreamOutlet(
			StreamInfo(
				'Kalman Filtered Angle', 
				'Kalman Filtered Angle', 
				3, 
				100, 
				'float32', 
				'Kalman Filtered Angle'
				)
			)


	def _window_setting(self):
		self.resize(Params.WINDOW_WIDTH, Params.WINDOW_HEIGHT)
		self.setWindowTitle("Real Time Control System: Data Monitor")

		# plot widget
		# for angle plot widget, at first it should be hidden,
		# if user connect angle data and choose to show, then it will apear.

		self.plotWidget_emg = pq.GraphicsLayoutWidget(show=True)
		self.plotWidget_emg.setBackground('w')

		self.plotWidget_angle = pq.GraphicsLayoutWidget(show=True)
		self.plotWidget_angle.setBackground('w')
		self.plotWidget_angle.setFixedHeight(400)
		self.plotWidget_angle.hide()

	def _push_button_setting(self):
		self.switch_btn = QtWidgets.QPushButton("Start")
		self.data_btn = QtWidgets.QPushButton("raw sEMG")
		self.MVC_btn = QtWidgets.QPushButton("Start MVC Collection")
		self.smk_btn = QtWidgets.QPushButton("Start SMK Device")
		self.model_select_btn = QtWidgets.QPushButton("Model Selection")
		self.angle_btn = QtWidgets.QPushButton("Joint Angle Estimation")
		self.connect_to_robot_btn = QtWidgets.QPushButton("Connect to Robot")
		self.data_acquisition_btn = QtWidgets.QPushButton("Data Collection")
		self.quitBtn = QtWidgets.QPushButton("Quit")

		self.switch_btn.setEnabled(False)
		self.MVC_btn.setEnabled(False)
		self.data_btn.setEnabled(False)
		self.model_select_btn.setEnabled(False)
		self.connect_to_robot_btn.setEnabled(False)
		self.angle_btn.hide()
		self.data_acquisition_btn.hide()

		self.switch_btn.clicked.connect(self.Switch_Btn)
		self.data_btn.clicked.connect(self.Data_Btn)
		self.MVC_btn.clicked.connect(self.MVC_Btn)
		self.smk_btn.clicked.connect(self.SMK_LSL_START)
		self.model_select_btn.clicked.connect(self.Model_Select_Btn)
		self.angle_btn.clicked.connect(self.Angle_Estimation)
		self.connect_to_robot_btn.clicked.connect(self.ConnectToRobotBtn)
		self.data_acquisition_btn.clicked.connect(self.RealTimeDataAcquisition)
		self.quitBtn.clicked.connect(self.Quit_Btn)

	def _layout_setting(self):
		self.layout = QtWidgets.QGridLayout()
		# button
		self.layout.addWidget(self.switch_btn, 0, 1)
		self.layout.addWidget(self.data_btn, 0, 3)
		self.layout.addWidget(self.MVC_btn, 0, 2)
		self.layout.addWidget(self.smk_btn, 0, 0)
		self.layout.addWidget(self.model_select_btn, 0, 4)
		self.layout.addWidget(self.angle_btn, 0, 4)
		self.layout.addWidget(self.connect_to_robot_btn, 0, 5)
		self.layout.addWidget(self.data_acquisition_btn, 0, 5)
		self.layout.addWidget(self.quitBtn, 0, 6)
		# plot screen
		self.layout.addWidget(self.plotWidget_emg, 1, 0, 1, 7)
		self.layout.addWidget(self.plotWidget_angle, 2, 0, 1, 7)

		self.setLayout(self.layout)

	def Switch_Btn(self):
		if self.switch_btn.text() == "Start":
			if not self.receiving_lsl:
				self.lsl()
				self.receiving_lsl = True
			self.MVC_btn.setEnabled(True)
			self.switch_btn.setText("Stop")
			self.timer.start(50)
			self.switch_btn.setEnabled(False)
		elif self.switch_btn.text() == "Stop":
			self.switch_btn.setText("Start")
			self.MVC_btn.setEnabled(False)
			self.timer.stop()

	def Data_Btn(self):
		if self.data_btn.text() == "raw sEMG":
			self.data_btn.setText("filtered sEMG")
			self.datatype = Params.DATA_TYPE_FILTERED
			self.P_emg = update_YRange(self.datatype, self.P_emg)
			
		elif self.data_btn.text() == "filtered sEMG":
			self.data_btn.setText("raw sEMG")
			self.datatype = Params.DATA_TYPE_RAW
			self.P_emg = update_YRange(self.datatype, self.P_emg)

	def MVC_Btn(self):
		if not self.MVC_RUN:
			self.initMVC()
			self.MVC_RUN = True
			self.MVC_btn.setText("Stop MVC Collection")

			self.data_btn.setText("raw sEMG")
			self.data_btn.setEnabled(False)
			self.datatype = Params.DATA_TYPE_RAW
			self.P_emg = update_YRange(self.datatype, self.P_emg)

		else:
			self.MVC_RUN = False
			self.MVC_btn.setText("Start MVC Collection")
			self.data_btn.setEnabled(True)
			MVC_filtered, zf = KoikeFilter(self.MVC, self.koike_params)
			self.MVC_min = MVC_filtered.min(axis=0)
			self.MVC_max = MVC_filtered.max(axis=0)
			self.MVC_stopped = True

	def SMK_LSL_START(self):
		self.smk_btn.setEnabled(False)
		self.switch_btn.setEnabled(True)
		self.MVC_btn.setEnabled(True)

		"""
		We deleted the SerialPort() function from smk.py
		so please complete your own data acquisition program based on LSL, 
		and open another terminal to run, just refer to the following comment part 
		and remove the following print line:
		"""
		print('Please complete your own data acquisition program based on LSL, and delete this sentence from line 229 in module/GUI.py')

		# """
		# start another terminal to run smk program
		# - If the system is Linux Ubuntu, use "gnome-terminal".
		#   My Linux system is Ubuntu Mate, so I use "mate-terminal"
		# - If the system is Windows, use "start powershell.exe"
		# - If the system is Mac OS, you should install applescript.
		# """
		# if platform.system() == 'Linux':
		# 	os.system("mate-terminal -e 'bash -c \"python smk.py; exec bash\"'")
		# elif platform.system() == 'Windows':
		# 	os.system("start powershell.exe cmd /k 'python smk.py'")
		# elif platform.system() == 'Darwin':
		# 	try:
		# 		import applescript
		# 		applescript.app('Terminal').do_script("python smk.py")
		# 	except ImportError:
		# 		raise RuntimeError('Can not import \033[1;31mapplescript\033[0m, make sure \033[1;31mapplescript\033[0m package is installed.')

	def Model_Select_Btn(self):
		fileName, filetype = QFileDialog.getOpenFileName(self,
			"Choose model",
			"../model/",
			"model file (*.pkl)"
			)
		print(fileName, filetype)
		self.model_select = fileName
		print("Model was loaded successfully!")

		try:
			self.model = CNN()
			self.model.load_state_dict(torch.load(self.model_select, map_location=torch.device('cpu')))
		except ImportError:
			raise RuntimeError("Failed to load the model, please check the reasons.")
		self.model_select_btn.hide()
		self.angle_btn.show()

	def Angle_Estimation(self):
		self.plotWidget_angle.show()
		self.start_angle_prediction = True
		self.outlet_delay = StreamOutlet(StreamInfo('Calculation Delay', 'Calculation Delay', 1, 100, 'int16', 'Calculation Delay'))

		self.Kalman_init()

		self.connect_to_robot_btn.setEnabled(True)
		self.angle_btn.setEnabled(False)

	def ConnectToRobotBtn(self):
		self.start_to_control_robot = True
		self.lsl_outlet()

		self.connect_to_robot_btn.hide()
		self.data_acquisition_btn.show()

	def RealTimeDataAcquisition(self):
		if self.data_acquisition_btn.text() == "Data Collection":
			self.data_acquisition_btn.setText("Stop")
			self.trigger = [Params.TRIGGER_REALTIME]
		elif self.data_acquisition_btn.text() == "Stop":
			self.data_acquisition_btn.setText("Data Collection")
			self.trigger = [Params.TRIGGER_NOT_REALTIME]

	def Quit_Btn(self):
		if self.start_angle_prediction:
			self.Q = np.delete(self.Q, 0, 0)
			self.R = np.delete(self.R, 0, 0)
			io.savemat('Q.mat', {'transition_covariance': self.Q})
			io.savemat('R.mat', {'observation_covariance': self.R})
		self.app.quit()

	def _addPlot(self):
		self.P_emg = {}
		self.P_angle = {}
		# EMG plot setting
		for emg_ch in range(1, Params.EMG_ch+1):
			self.P_emg[str(emg_ch)] = self.plotWidget_emg.addPlot()
			self.P_emg[str(emg_ch)].setYRange(-20000, 20000)
			if emg_ch % 4 == 0:
				self.plotWidget_emg.nextRow()
		# Angle plot setting
		dof = ['WF/WE Joint', 'P/S Joint', 'HG/HO Joint']
		for angle_ch in range(1, Params.ANGLE_ch+1):
			self.P_angle[str(angle_ch)] = self.plotWidget_angle.addPlot(title=dof[angle_ch-1])
			self.P_angle[str(angle_ch)].setYRange(-100, 100)

			self.P_angle[str(angle_ch)].addLegend()

	def Kalman_filter(self):
		self.K1, self.P1, self.X1, self.Q1, self.R1 = kalman_filter(self.temp_angles[0], self.K1, self.P1, self.X1, self.t, self.Q1, self.R1, self.Q_est[0], self.R_est[0])
		self.K2, self.P2, self.X2, self.Q2, self.R2 = kalman_filter(self.temp_angles[1], self.K2, self.P2, self.X2, self.t, self.Q2, self.R2, self.Q_est[1], self.R_est[1])
		self.K3, self.P3, self.X3, self.Q3, self.R3 = kalman_filter(self.temp_angles[2], self.K3, self.P3, self.X3, self.t, self.Q3, self.R3, self.Q_est[2], self.R_est[2])
		self.t += 1

		self.temp_kalman = [self.X1, self.X2, self.X3]
		self.Q = np.vstack((self.Q, [self.Q1, self.Q2, self.Q3]))
		self.R = np.vstack((self.R, [self.R1, self.R2, self.R3]))
		self.Q_est = [estimated_var(self.Q[:,0]), estimated_var(self.Q[:,1]), estimated_var(self.Q[:,2])]
		self.R_est = [estimated_var(self.R[:,0]), estimated_var(self.R[:,1]), estimated_var(self.R[:,2])]

	def Kalman_init(self):
		self.K1, self.K2, self.K3 = 0, 0, 0
		self.X1, self.X2, self.X3 = 0, 0, 0
		self.P1, self.P2, self.P3 = 1, 1, 1

		self.Q1, self.Q2, self.Q3 = 0.05, 0.05, 0.05
		self.R1, self.R2, self.R3 = 0.5, 0.5, 0.5
		self.Q = np.array([self.Q1, self.Q2, self.Q3])
		self.R = np.array([self.R1, self.R2, self.R3])
		self.Q_est = [0, 0, 0]
		self.R_est = [0, 0, 0]
		self.t = 1

	def delay_calculator(self):
		self.end_time = time.time()
		self.delay = int((self.end_time - self.start_time) % 60 * 1000)
		self.outlet_delay.push_sample([self.delay])

	def update_ANGLE(self):
		self.temp_angles = self.model(arr2tensor_emg(self.temp_dataFiltered)).cpu().data.numpy()
		if self.temp_kalman == []:
			self.X1, self.X2, self.X3 = self.temp_angles[0], self.temp_angles[1], self.temp_angles[2]
			self.P1, self.P2, self.P3 = 1, 1, 1
		self.Kalman_filter()
		self.delay_calculator()

	def update_EMG(self):
		self.temp_data = self.GET_EMG_LSL()
		temp_data_Filtered, self.koike_params['zf'] = KoikeFilter(self.temp_data, self.koike_params)
		self.temp_dataFiltered = MVC_normalize(temp_data_Filtered, self.MVC_min, self.MVC_max)

	def update_data(self):
		if self.receiving_lsl:
			if self.MVC_RUN:
				self.MVC = np.vstack((self.MVC, self.temp_data))

			self.emg_data = np.delete(self.emg_data, list(range(0,Params.SLIDING_WINDOW_LEN)), 0)
			self.emg_Filtered = np.delete(self.emg_Filtered, list(range(0,Params.SLIDING_WINDOW_LEN)), 0)
			self.emg_data = np.vstack((self.emg_data, self.temp_data))
			self.emg_Filtered = np.vstack((self.emg_Filtered, self.temp_dataFiltered))
			if self.datatype == Params.DATA_TYPE_RAW:
				self.EMG_DATA = self.emg_data
			elif self.datatype == Params.DATA_TYPE_FILTERED:
				self.EMG_DATA = self.emg_Filtered

		if self.start_angle_prediction:
			self.ANGLE_DATA = np.delete(self.ANGLE_DATA, list(range(0,1)), 0)
			self.ANGLE_DATA_KALMAN = np.delete(self.ANGLE_DATA_KALMAN, list(range(0,1)), 0)
			self.ANGLE_DATA = np.vstack((self.ANGLE_DATA, self.temp_angles))
			self.ANGLE_DATA_KALMAN = np.vstack((self.ANGLE_DATA_KALMAN, self.temp_kalman))

	def refresh_curve(self):
		for ch in range(1, Params.EMG_ch+1):
			self.curve_emg[str(ch)].setData(self.EMG_DATA[:,ch-1])

		for dof in range(1, Params.ANGLE_ch+1):
			self.curve_angle[str(dof)].setData(self.ANGLE_DATA[:,dof-1])
			self.curve_angle_Kalman[str(dof)].setData(self.ANGLE_DATA_KALMAN[:,dof-1])

	def _curve(self):
		self.curve_emg = {}
		self.curve_angle = {}
		self.curve_angle_Kalman = {}

		for emg_ch in range(1, Params.EMG_ch+1):
			self.curve_emg[str(emg_ch)] = self.P_emg[str(emg_ch)].plot(self.EMG_DATA[:,emg_ch-1], name='ch'+str(emg_ch), pen=Params.COLOR_BLUE)
		for angle_ch in range(1, Params.ANGLE_ch+1):
			self.curve_angle[str(angle_ch)] = self.P_angle[str(angle_ch)].plot(self.ANGLE_DATA[:,angle_ch-1], name='Estimated DOF'+str(angle_ch), pen=Params.COLOR_BLUE)
			self.curve_angle_Kalman[str(angle_ch)] = self.P_angle[str(angle_ch)].plot(self.ANGLE_DATA_KALMAN[:,angle_ch-1], name='Kalman Filtered DOF'+str(angle_ch), pen=Params.COLOR_RED)

	def _timer(self):
		self.timer = pq.QtCore.QTimer()
		self.timer.start(50)
		self.timer.timeout.connect(self.update)

	def _test(self):
		if self.start_to_control_robot:
			if self.n < len(self.qb):
				self.softhand.move(0, self.qb[self.n][0])
				self.softhand.move(1, self.qb[self.n][1])
				self.softhand.move(2, self.qb[self.n][2])
				self.n += 1

	def update(self):
		if self.MVC_stopped:
			self.model_select_btn.setEnabled(True)

		if self.receiving_lsl:
			self.start_time = time.time()
			self.update_EMG()
		if self.start_angle_prediction:
			self.update_ANGLE()

		self.refresh_curve()
		self.update_data()

		if self.start_to_control_robot:
			self.outlet_angles.push_sample(self.temp_angles)
			self.outlet_angles_kalman.push_sample(self.temp_kalman)
			self.outlet_trigger.push_sample(self.trigger)

class mainWindow(QMainWindow):
	WINDOW_WIDTH = 400
	WINDOW_HEIGHT = 120

	def __init__(self, app, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.app = app
		self.setWindowTitle("Real Time Control System")
		self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

		self.centralwidget = QtWidgets.QWidget()
		self.setCentralWidget(self.centralwidget)
		self.layout = QtWidgets.QVBoxLayout(self.centralwidget)

		self.pushButton1 = QtWidgets.QPushButton()
		self.pushButton1.setText("Open Signal Monitor")
		self.layout.addWidget(self.pushButton1)

		self.pushButton2 = QtWidgets.QPushButton()
		self.pushButton2.setText("Quit")
		self.layout.addWidget(self.pushButton2)

		# status bar
		self.statusBar().showMessage("Koike&Yoshimura Lab; ver "+Params.VER+"                                  by "+Params.author)
		self.show()

		self.pushButton1.clicked.connect(self.on_pushButton_clicked)
		self.pushButton2.clicked.connect(self.quit)

	windowList = []
	def on_pushButton_clicked(self):
		RealTimeSystem = DataMonitor(self.app)
		self.windowList.append(RealTimeSystem)
		self.close()
		RealTimeSystem.show()
		
	def quit(self):
		self.app.quit()
