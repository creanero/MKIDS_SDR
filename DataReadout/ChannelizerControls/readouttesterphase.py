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

phaseraw = []

ch_we = 0
roach.write_int('ch_we', ch_we)

roach.write_int('startSnap', 0)
roach.write_int('snapPhase_ctrl', 0)
roach.write_int('snapPhase_ctrl', 1)
roach.write_int('startSnap', 1)

time.sleep(0.001)

testphase = roach.read('snapPhase_bram', 128)


#bin_data_I = bin_data_I + str(self.roach.read_int('conv_phase_snapI_bram'))
#print "Length testI = ", len(testI)
#print "Type testphase = ", type(testphase)

print("testphase = ", testphase)

print 



#phaseraw.append(struct.unpack('>h', testphase[2:4])[0])
#Qraw.append(struct.unpack('>h', testQ[2:4])[0])
phase = []
for m in range(32):
	#phaseraw.append(struct.unpack('>h', testphase[4*m+2:4*m+4])[0])
	#print("testphase1 = ", testphase[4*m+2:4*m+4])
	#print("testphase2 = ", testphase[4*m:4*m+2])
	#print"phaseraw1 = ", struct.unpack('>h', testphase[4*m+2:4*m+4])[0]
	#print"phaseraw2 = ", struct.unpack('>h', testphase[4*m:4*m+2])[0] 
	phase.append(struct.unpack('>h', testphase[4*m+2:4*m+4])[0])
	phase.append(struct.unpack('>h', testphase[4*m:4*m+2])[0])


print

#print("phasestring = ", phase)

phase = numpy.array(phase)*360./2**16*4/numpy.pi
print("phase = ", phase)

#testI0 = testI[3]

#testI0.decode("utf-8")

#print "testI0 decoded = ", testI0

print("Bins register = ", roach.read_int('bins'))


