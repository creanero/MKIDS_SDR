import sys, os, random, math, array, fractions,time,datetime,pickle
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import socket
import matplotlib, corr, time, struct
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(suppress=True)
from datetime import datetime
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from tables import *
from lib import iqsweep


roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)

L = 16


#ch_we = 27
#ch_we = 31


for ch_we in range(256): 
	bin_data_IQ = ''
	bin_data_Phase = ''
	#time.sleep(0.5)
	print"ch_we = ", ch_we, 
	roach.write_int('conv_phase_ch_we_IQ', ch_we)
	roach.write_int('conv_phase_ch_we_Phase', ch_we)


	steps = 1
	for n in range(steps):

		roach.write_int('conv_phase_startSnapIQ', 0)
		roach.write_int('conv_phase_startSnapPhase', 0)
		roach.write_int('conv_phase_snapIQ_ctrl', 1)
		roach.write_int('conv_phase_snapPhase_ctrl', 1)
		roach.write_int('conv_phase_snapIQ_ctrl', 0)
		roach.write_int('conv_phase_snapPhase_ctrl', 0)
		roach.write_int('conv_phase_startSnapIQ', 1)
		roach.write_int('conv_phase_startSnapPhase', 1)

		bin_data_IQ = bin_data_IQ + roach.read('conv_phase_snapIQ_bram', 4*L)
		bin_data_Phase = bin_data_Phase + roach.read('conv_phase_snapPhase_bram', 4*L)

	#print("bin_data_I = ", bin_data_I)
	#print("bin_data_Q = ", bin_data_Q)

	print 

	IQraw = []
	phaseraw = []
	
	for m in range(steps*L):
		IQraw.append(struct.unpack('>h', bin_data_IQ[4*m+2:4*m+4])[0])
		phaseraw.append(struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0])	

		print"IQraw = ", struct.unpack('>h', bin_data_IQ[4*m+2:4*m+4])[0], "phaseraw = ", struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0]
		
	 



#phase_cpu = 360 * (np.arctan2(Qraw, Iraw)) / (2*np.pi)
#phase_fpga = np.array(phaseraw)*360./2**16*4/np.pi

#print "Phase = ", phase

#for k in range(steps*L):
#	print "I = ", Iraw[k], "Q = ", Qraw[k], "	phase cpu = ", round(phase_cpu[k], 2), " degrees", "	phase fpga = ", phase_fpga[k], " degrees" 
	
print "done"
#print("------%s seconds-----" % (time.time() - starttime))






