import sys, os, random, math, array, fractions,time,datetime,pickle
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import socket
import matplotlib, corr, time, struct
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(suppress=True)
from datetime import datetime
import matplotlib.pyplot as plt
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
savedir = '/home/labuser/Data/2022/2022_01_25/Setup/Phase/'

filename = savedir + 'phase_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'


roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)

L_phase = 16384
#bin_data_I = ''
#bin_data_Q = ''

#bin_data_IQ = ''
bin_data_Phase = ''
phaseraw = []
ch_we_Phase = 43



roach.write_int('conv_phase_ch_we_Phase', ch_we_Phase)


steps = 128
for n in range(steps):

	#time.sleep(0.001)

	roach.write_int('conv_phase_startSnapPhase', 0)
	roach.write_int('conv_phase_snapPhase_ctrl', 1)
	roach.write_int('conv_phase_snapPhase_ctrl', 0)
	roach.write_int('conv_phase_startSnapPhase', 1)

	bin_data_Phase = bin_data_Phase + roach.read('conv_phase_snapPhase_bram', 4*L_phase)

for m in range(L_phase*steps):
	phaseraw.append(struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0])	
phasefpga = np.array(phaseraw)*360./2**16*4/np.pi


for k in range(len(phasefpga)):
	if phasefpga[k] < 0:
		phasefpga[k] = phasefpga[k] + 360 

np.savetxt(filename, phasefpga, fmt='%.3f')
print "saved!"


phaseaverage = np.mean(phasefpga[0:100])

phasenormalized = phasefpga - phaseaverage


print"Phase average = ", phaseaverage 
print"Max phasenormalized = ", np.max(phasenormalized), " Min phasenormalized = ", np.min(phasenormalized)

#print "done"

#plt.figure()
#plt.plot(phasenormalized, '.')
#plt.title('Phase Vs Time')
#plt.xlabel('Time')
#plt.ylabel('Phase')
#plt.grid()

#plt.show()





