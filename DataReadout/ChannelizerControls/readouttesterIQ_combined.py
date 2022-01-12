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


Icentre = 0
Qcentre = 0
L = 16
bin_data_IQ = ''
bin_data_Phase = ''

ch_we_IQ = 27
ch_we_Phase = 43



roach.write_int('conv_phase_ch_we_IQ', ch_we_IQ)
roach.write_int('conv_phase_ch_we_Phase', ch_we_Phase)


starttime = time.time()

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

print("bin_data_IQ = ", bin_data_IQ)

for n in range(L):
	print("n = ", n)
	print("bin_data_IQ = ", bin_data_IQ[n:n+2]) 
	print("bin_data_IQ unpacked = ", struct.unpack('>h', bin_data_IQ[n:n+2])[0])	
	
	
print "done"
#print("------%s seconds-----" % (time.time() - starttime))






