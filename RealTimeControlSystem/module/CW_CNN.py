#!/usr/bin/python3
# -*-coding: utf-8 -*-

try:
	import torch
	import torch.nn as nn
	from torch.autograd import Variable
except ImportError:
    raise RuntimeError('cannot import torch packages, make sure pytorch was installed')


class CNN(nn.Module):
	INPUT_NUM = 1
	INPUT_LEN = int(500*120/1000) # 120ms, 500Hz
	INPUT_CH = 32
	OUT_NUM_CONV = 6
	OUT_NUM_FC = 3
	FILTER_SIZE = (INPUT_LEN, 1)
	STRIDE = 1
	PADDING = 0

	def __init__(self):
		super(CNN, self).__init__()
		self.conv1 = nn.Sequential(
			nn.Conv2d(
				in_channels = self.INPUT_NUM,
				out_channels = self.OUT_NUM_CONV,
				kernel_size = self.FILTER_SIZE,
				stride = self.STRIDE,
				padding = self.PADDING
				),
			nn.Tanh(),
			)

		self.out = nn.Linear(self.INPUT_CH*self.OUT_NUM_CONV, self.OUT_NUM_FC)

	def forward(self, emg):
		x = emg.view(1, 1, self.INPUT_LEN, self.INPUT_CH)
		fm = self.conv1(x)
		# fm = fm.cpu().data.numpy()
		fm_ = fm.view(fm.size(0), -1)
		output = self.out(fm_)
		angles = output.view(output.size(1))

		return angles

"""
convert training data from numpy to tensor for torch.
"""
def arr2tensor(x, y):
	x = torch.from_numpy(x)
	y = torch.from_numpy(y)

	x = Variable(torch.unsqueeze(x, dim=0).float(), requires_grad=False).cuda()
	x = x.view(-1, 1, 1)

	y = Variable(torch.unsqueeze(y, dim=0).float(), requires_grad=False).cuda()
	y = y.view(CNN.OUT_NUM_FC)

	return x, y