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


roach.write_int('conv_phase_snapIQ_ctrl', 0)
#roach.write_int('conv_phase_snapQ_ctrl', 0)
roach.write_int('conv_phase_snapIQ_ctrl', 1)
#roach.write_int('conv_phase_snapQ_ctrl', 1)

#roach.write_int('conv_phase_snapI_ctrl', 2)
#roach.write_int('conv_phase_snapI_ctrl', 4)
#roach.write_int('conv_phase_snapI_ctrl', 8)


#roach.write_int('conv_phase_snapI_ctrl', 0)

time.sleep(0.001)

testI = roach.read('conv_phase_snapIQ_bram', 4096)
#testQ = roach.read('conv_phase_snapQ_bram', 2048)


#bin_data_I = bin_data_I + str(self.roach.read_int('conv_phase_snapI_bram'))
#print "Length testI = ", len(testI)
print "Type testI = ", type(testI)

print("testI = ", testI)
print 

#Iraw.append(struct.unpack('>h', testI[2:4])[0])
#Qraw.append(struct.unpack('>h', testQ[2:4])[0])

Iraw = []
#Qraw = []
for m in range(1024):
	Iraw.append(struct.unpack('>h', testI[4*m+2:4*m+4])[0])
	#Qraw.append(struct.unpack('>h', testQ[4*m+2:4*m+4])[0])
	#Iraw.append(struct.unpack('>h', testI[4*m:4*m+2])[0]) 
	print "m = ", m, "Iraw = ", struct.unpack('>h', testI[4*m+2:4*m+4])[0] #, "    Qraw = ", struct.unpack('>h', testQ[4*m+2:4*m+4])[0]
	#print 

#print
#print "Iraw = ", Iraw






