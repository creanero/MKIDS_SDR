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

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is


#savedir = '/home/labuser/Data/2022/2022_01_18/4578MHz/BlueLaser/'
savedir = '/home/labuser/Data/2022/2022_01_19/ClosedLoop/'

filename = savedir + 'IQ_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'


roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)

L = 65536
#bin_data_I = ''
#bin_data_Q = ''

bin_data_IQ = ''
#bin_data_Phase = ''
bin_data_IQ_ord = []
bin_data_IQ_hex = []

ch_we_IQ = 24
#ch_we_Phase = 43



roach.write_int('conv_phase_ch_we_IQ', ch_we_IQ)


steps = 32
for n in range(steps):

	#time.sleep(0.001)

	roach.write_int('conv_phase_startSnapIQ', 0)
	roach.write_int('conv_phase_snapIQ_ctrl', 1)
	roach.write_int('conv_phase_snapIQ_ctrl', 0)
	roach.write_int('conv_phase_startSnapIQ', 1)
	

	bin_data_IQ = bin_data_IQ + roach.read('conv_phase_snapIQ_bram', 4*L)

for j in range(steps*L*4):
	#print("j = ", j)
	bin_data_IQ_ord.append(ord(bin_data_IQ[j]))
	bin_data_IQ_hex.append("0x{:02x}".format(bin_data_IQ_ord[j]))	
	




Iraw = []
Qraw = []
	
for k in range((steps*L) / 4):

	I0 = bin_data_IQ_hex[6+16*k][3] + bin_data_IQ_hex[7+16*k][2:4] + bin_data_IQ_hex[8+16*k][2]
	I0 = twos_comp(int(I0,16), 16)
	Iraw.append(I0)

	I1 = bin_data_IQ_hex[11+16*k][3] + bin_data_IQ_hex[12+16*k][2:4] + bin_data_IQ_hex[13+16*k][2]
	I1 = twos_comp(int(I1,16), 16)
	Iraw.append(I1)

	Q0 = bin_data_IQ_hex[9+16*k][2:4] + bin_data_IQ_hex[10+16*k][2:4]
	Q0 = twos_comp(int(Q0,16), 16)
	Qraw.append(Q0)

	Q1 = bin_data_IQ_hex[14+16*k][2:4] + bin_data_IQ_hex[15+16*k][2:4]
	Q1 = twos_comp(int(Q1,16), 16)
	Qraw.append(Q1)

#for k in range(steps*L):
#	print "k = ", k, "I = ", Iraw[k], "Q = ", Qraw[k]

#print "filename = ", filename

savearray = [Iraw, Qraw]
np.savetxt(filename,np.column_stack(savearray),fmt='%i ' ' %i' )
print "saved!"


#print "done"






