#!/usr/bin/python3
# -*-coding: utf-8 -*-

"""
- Real Time Control System v3.0 -

written by @QIN ZIXUAN
* update: 2022/04/03
* email: qin.z.aa@m.titech.ac.jp
@ Koike & Yoshimura Lab, Tokyo Institute of Technology
"""

import sys
from module.GUI import *
from module.tools import LoadQssFile

def main():
	app = QApplication(sys.argv)
	app = LoadQssFile('button.qss', app)

	main = mainWindow(app)

	sys.exit(app.exec())

if __name__ == '__main__':
	main()