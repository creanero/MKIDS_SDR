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


savedir = '/home/labuser/Data/2021/2021_12_16/4578MHz/BlueLaser/'
#savedir = '/home/labuser/Data/2021/2021_12_16/Setup/'

filename = savedir + 'IQ_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'


roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)

L = 32768
bin_data_I = ''
bin_data_Q = ''

ch_we = 27

roach.write_int('conv_phase_ch_we_IQ', ch_we)


steps = 32
for n in range(steps):

	#time.sleep(0.001)

	roach.write_int('conv_phase_startSnapI', 0)
	roach.write_int('conv_phase_startSnapQ', 0)
	
	roach.write_int('conv_phase_snapI_ctrl', 1)
	roach.write_int('conv_phase_snapQ_ctrl', 1)
	
	roach.write_int('conv_phase_snapI_ctrl', 0)
	roach.write_int('conv_phase_snapQ_ctrl', 0)
	
	roach.write_int('conv_phase_startSnapI', 1)
	roach.write_int('conv_phase_startSnapQ', 1)
	

	bin_data_I = bin_data_I + roach.read('conv_phase_snapI_bram', 4*L)
	bin_data_Q = bin_data_Q + roach.read('conv_phase_snapQ_bram', 4*L)


#print 

Iraw = []
Qraw = []
	
for m in range(steps*L):
	Iraw.append(struct.unpack('>h', bin_data_I[4*m+2:4*m+4])[0])
	Qraw.append(struct.unpack('>h', bin_data_Q[4*m+2:4*m+4])[0])	

#for k in range(steps*L):
#	print "k = ", k, "I = ", Iraw[k], "Q = ", Qraw[k]

#print "filename = ", filename

savearray = [Iraw, Qraw]
np.savetxt(filename,np.column_stack(savearray),fmt='%i ' ' %i' )
print "saved!"


#print "done"






