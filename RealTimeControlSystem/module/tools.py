#!/usr/bin/python3
# -*-coding: utf-8 -*-

import scipy.signal
import numpy as np
import math
try:
	import torch
	import torch.nn as nn
	from torch.autograd import Variable
except ImportError:
    raise RuntimeError('cannot import torch packages, make sure pytorch was installed')

class Params:
	author="Zixuan QIN"
	VER = "3.0"
	COLOR_BLACK = (0, 0, 0)
	COLOR_WHITE = (255, 255, 255)
	COLOR_BLUE = (0, 0, 255)
	COLOR_RED = (139, 0, 0)
	DATA_TYPE_RAW = 1
	DATA_TYPE_FILTERED = 2
	WINDOW_WIDTH = 1500
	WINDOW_HEIGHT = 1000
	EMG_ch = 32
	ANGLE_ch = 3
	SLIDING_WINDOW_LEN = 60
	SAMPLING_RATE_EMG = 500
	SAMPLING_RATE_ANGLE = 120

	TRIGGER_NOT_REALTIME = 0
	TRIGGER_REALTIME = 1

def LoadQssFile(path, app):
	with open(path, encoding="utf-8") as f:
		qss = f.read()
		app.setStyleSheet(qss)

	return app

def update_YRange(datatype, P):
	if datatype == Params.DATA_TYPE_RAW:
		for i in range(Params.EMG_ch):
			P[str(i+1)].setYRange(-20000,20000)
	elif datatype == Params.DATA_TYPE_FILTERED:
		for i in range(Params.EMG_ch):
			P[str(i+1)].setYRange(0,1.2)

	return P

def KoikeParameters(sf):
	time = np.arange(0, 1, 1/sf)
	M1 = -10.8*time
	M2 = -16.52*time
	coef = []
	for i in range(sf):
		M1[i] = math.exp(M1[i])
		M2[i] = math.exp(M2[i])
		coef.append(6.44 * (M1[i] - M2[i]))

	total = sum(coef)

	zi = scipy.signal.lfilter_zi(coef, 1)
	zf = np.ones([sf-1, 32])
	for i in range(sf-1):
		for j in range(32):
			zf[i,j] = zf[i,j] * zi[i]

	params = {}
	params['coef'] = coef
	params['total'] = total
	params['zf'] = zf

	return params

def KoikeFilter(emg, params):
	coef = params['coef']
	total = params['total']
	zf = params['zf']

	y = np.zeros([emg.shape[0], emg.shape[1]])
	for i in range(32):
		xn = np.abs(emg[:,i]/total)
		y[:,i], zf[:,i] = scipy.signal.lfilter(coef, 1.0, xn, axis=-1, zi=zf[:,i])

	return y, zf

def MVC_normalize(data, MVC_min, MVC_max):
	return (data - MVC_min) / (MVC_max - MVC_min)

def CorrelationCoefficient(pred, truth):
	angle_p_1 = pred[:,0]
	angle_p_2 = pred[:,1]
	angle_p_3 = pred[:,2]

	angle_t_1 = truth[:,0]
	angle_t_2 = truth[:,1]
	angle_t_3 = truth[:,2]

	cc1 = np.corrcoef(angle_p_1, angle_t_1)[0, 1]
	cc2 = np.corrcoef(angle_p_2, angle_t_2)[0, 1]
	cc3 = np.corrcoef(angle_p_3, angle_t_3)[0, 1]

	return cc1, cc2, cc3

def arr2tensor_emg(x):
	x = torch.from_numpy(x)
	x = Variable(torch.unsqueeze(x, dim=0).float(), requires_grad=False)
	x = x.view(-1, 1, 1)

	return x

def estimated_var(a):
	return np.sqrt(((a - np.mean(a)) ** 2).sum() / (a.size))

def kalman_filter(data, K, P, X, t, Q, R, Q_var, R_var):
	e = data - X
	pre_P = P

	K = P / (P + R)
	X = X + K * (data - X)
	P = P - K * P + Q

	R = 1/t * (R_var - R) + R
	Q = 1/t * (Q_var - Q) + Q

	return K, P, X, Q, R