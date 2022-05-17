import sys, os, random, math, array, fractions,time,datetime,pickle

import PyQt4.QtCore as QtC   #instead, had to import PyQt4 like this 
import PyQt4.QtGui as QtG    ##later had to add QtC. or QtG. before certain functions e.g. line 52



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
#from tables import *
from lib import iqsweep


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)


Icentre = 0
Qcentre = 0
L_phase = 16 #must be greater than 4 
L_IQ = 16
bin_data_IQ = ''
bin_data_Phase = ''
bin_data_Phase_2 = ''
bin_data_IQ_ord = []
bin_data_IQ_hex = []

ch_we_IQ = 24
ch_we_Phase = 43



roach.write_int('conv_phase_ch_we_IQ', ch_we_IQ)
roach.write_int('conv_phase_ch_we_Phase', ch_we_Phase)


starttime = time.time()

steps = 1
for n in range(steps):
	starttime = time.time()
	roach.write_int('conv_phase_startSnapIQ', 0)
	roach.write_int('conv_phase_startSnapPhase', 0)
	starttime = time.time()
	roach.write_int('conv_phase_snapIQ_ctrl', 1)
	roach.write_int('conv_phase_snapPhase_ctrl', 1)
	print("------%s seconds-----" % (time.time() - starttime))
	roach.write_int('conv_phase_snapIQ_ctrl', 0)
	roach.write_int('conv_phase_snapPhase_ctrl', 0)
	roach.write_int('conv_phase_startSnapIQ', 1)
	roach.write_int('conv_phase_startSnapPhase', 1)
	#print("------%s seconds-----" % (time.time() - starttime))
	#bin_data_IQ = bin_data_IQ + roach.read('conv_phase_snapIQ_bram', 4*2*L_IQ)
	bin_data_Phase = bin_data_Phase + roach.read('conv_phase_snapPhase_bram', 4*L_phase)

phaseraw = []

for m in range(steps*L_phase):
		phaseraw.append(struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0])	
phasefpga = np.array(phaseraw)*360./2**16*4/np.pi
#phasecpu = 360*(np.arctan2(Iraw, Qraw)) / 2*np.pi

for k in range(len(phasefpga)):
	if phasefpga[k] < 0:
		phasefpga[k] = phasefpga[k] + 360 

#plt.figure()
#plt.plot(phasefpga, '.')
#plt.title('Phase Vs Time')
#plt.xlabel('Time')
#plt.ylabel('Phase')
#plt.grid()

#print("Phase = ", phasefpga)

time.sleep(2)
bin_data_Phase_2 = roach.read('conv_phase_snapPhase_bram', 4*L_phase)

phaseraw2 = []

for m in range(steps*L_phase):
		phaseraw2.append(struct.unpack('>h', bin_data_Phase_2[4*m+2:4*m+4])[0])	
phasefpga2 = np.array(phaseraw2)*360./2**16*4/np.pi
#phasecpu = 360*(np.arctan2(Iraw, Qraw)) / 2*np.pi

for k in range(len(phasefpga)):
	if phasefpga2[k] < 0:
		phasefpga2[k] = phasefpga2[k] + 360 

#print("Phase 2 = ", phasefpga2)

#for n in range(steps):
#	bin_data_IQ = bin_data_IQ + roach.read('conv_phase_snapIQ_bram', 4*2*L_IQ)




#for j in range(steps*L_IQ*4*2):
	#print("j = ", j)
#	bin_data_IQ_ord.append(ord(bin_data_IQ[j]))
#	bin_data_IQ_hex.append("0x{:02x}".format(bin_data_IQ_ord[j]))	


#Iraw = []
#Qraw = []



#for k in range((steps*L_IQ*2) / 4):

#	I0 = bin_data_IQ_hex[6+16*k][3] + bin_data_IQ_hex[7+16*k][2:4] + bin_data_IQ_hex[8+16*k][2]
#	I0 = twos_comp(int(I0,16), 16)
#	Iraw.append(I0)

#	I1 = bin_data_IQ_hex[11+16*k][3] + bin_data_IQ_hex[12+16*k][2:4] + bin_data_IQ_hex[13+16*k][2]
#	I1 = twos_comp(int(I1,16), 16)
#	Iraw.append(I1)

#	Q0 = bin_data_IQ_hex[9+16*k][2:4] + bin_data_IQ_hex[10+16*k][2:4]
#	Q0 = twos_comp(int(Q0,16), 16)
#	Qraw.append(Q0)

#	Q1 = bin_data_IQ_hex[14+16*k][2:4] + bin_data_IQ_hex[15+16*k][2:4]
#	Q1 = twos_comp(int(Q1,16), 16)
#	Qraw.append(Q1)


#print"Iraw = ", Iraw
#print"Qraw = ", Qraw
#print"Phaseraw = ", phaseraw
#print"Phasefpga = ", phasefpga
#print""

#plt.figure()
#plt.plot(Iraw, '.')
#plt.title('Iraw Vs Time')
#plt.xlabel('Time')
#plt.ylabel('Iraw')
#plt.grid()

#plt.figure()
#plt.plot(Qraw, '.')
#plt.title('Qraw Vs Time')
#plt.xlabel('Time')
#plt.ylabel('Qraw')
#plt.grid()



#plt.figure()
#plt.plot(Iraw, Qraw, '.')
#plt.title('Iraw Vs Qraw')
#plt.xlabel('Iraw')
#plt.ylabel('Qraw')
#plt.grid()



#plt.figure()
#plt.plot(phasecpu, '.')
#plt.title('Phase (CPU) Vs Time')
#plt.xlabel('Time')
#plt.ylabel('Phase')
#plt.grid()

plt.show()

print"Done!"






