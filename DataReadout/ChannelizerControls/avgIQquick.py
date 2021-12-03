import sys, os, random, math, array, fractions,time,datetime,pickle
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import socket
import matplotlib, corr, time, struct, numpy
from datetime import datetime
#from bitstring import BitArray
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from tables import *
from lib import iqsweep


roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)

#roach.write_int('startAccumulator', 0)
roach.write_int('avgIQ_ctrl', 1)
roach.write_int('avgIQ_ctrl', 0)
#roach.write_int('startAccumulator', 1)
time.sleep(0.001)
data = roach.read('avgIQ_bram', 64)

print "Type data = ", type(data)

print "Length data = ", len(data)

print("data = ", data)

for n in range(10):
	I = struct.unpack('>l', data[4*n:4*n+4])[0]

	print "I = ", I




