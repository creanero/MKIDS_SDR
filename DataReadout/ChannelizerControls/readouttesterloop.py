import sys, os, random, math, array, fractions,time,datetime,pickle
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import socket
import matplotlib, corr, time, struct
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(suppress=True)
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

roach.write_int('conv_phase_snapI_ctrl', 1)
roach.write_int('conv_phase_snapQ_ctrl', 1)

bin_data_I = ''
bin_data_Q = ''
#steps = 131072

steps = 128
for n in range(steps):
	roach.write_int('conv_phase_snapI_ctrl', 0)
	roach.write_int('conv_phase_snapQ_ctrl', 0)
	roach.write_int('conv_phase_snapI_ctrl', 2)
	roach.write_int('conv_phase_snapQ_ctrl', 2)
	#roach.write_int('conv_phase_snapI_ctrl', 0)
	#time.sleep(0.001)

	bin_data_I = bin_data_I + roach.read('conv_phase_snapI_bram', 4096)
	bin_data_Q = bin_data_Q + roach.read('conv_phase_snapQ_bram', 4096)

#roach.write_int('conv_phase_snapI_ctrl', 0)
print "Length bin_data_I = ", len(bin_data_I)
print "Type bin_data_I = ", type(bin_data_I)
print "Length bin_data_Q = ", len(bin_data_Q)
print "Type bin_data_Q = ", type(bin_data_Q)


#print("bin_data_I = ", bin_data_I)
print 

#Iraw.append(struct.unpack('>h', testI[2:4])[0])
#Qraw.append(struct.unpack('>h', testQ[2:4])[0])

Iraw = []
Qraw = []
for m in range(steps*1024):
	Iraw.append(struct.unpack('>h', bin_data_I[4*m+2:4*m+4])[0])
	Qraw.append(struct.unpack('>h', bin_data_Q[4*m+2:4*m+4])[0])
	#Qraw.append(struct.unpack('>h', testQ[4*m+2:4*m+4])[0])
	#Iraw.append(struct.unpack('>h', testI[4*m:4*m+2])[0]) 
	print "m = ", m, "Iraw = ", struct.unpack('>h', bin_data_I[4*m+2:4*m+4])[0], "    Qraw = ", struct.unpack('>h', bin_data_Q[4*m+2:4*m+4])[0]
	#print 

#print

Irawfirst256 = Iraw[0:256]
Qrawfirst256 = Qraw[0:256]

Ifirst256mean = np.mean(Irawfirst256)
Qfirst256mean = np.mean(Qrawfirst256)


Imean = np.mean(Iraw)
Qmean = np.mean(Qraw)
print "mean Iraw = ", Imean 
print "mean Qraw = ", Qmean

inumber = 0
qnumber = 0

iqvalues = np.zeros([steps*4, 3])



for j in range(len(Irawfirst256)): 
	if np.abs(Irawfirst256[j] - Ifirst256mean) > 25:
		#print "inumber = ", inumber, "I = ", Iraw[j]
		Ifirstindex = j
		print "Ifirst = ", Irawfirst256[j]
		print "Ifirstindex = ", Ifirstindex

for k in range(len(Qrawfirst256)): 
	if np.abs(Qrawfirst256[k] - Qfirst256mean) > 25:
		#print "inumber = ", inumber, "I = ", Iraw[j]
		Qfirstindex = k
		print "Qfirst = ", Qrawfirst256[k]
		print "Qfirstindex = ", Qfirstindex

for l in range(4*steps):
	iqvalues[l, 0] = l
	iqvalues[l, 1] = Iraw[Ifirstindex + 256*l]
	iqvalues[l, 2] = Qraw[Qfirstindex + 256*l]





print "iqvalues = "
print iqvalues
print "done"






