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
from matplotlib.animation import FuncAnimation
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

savedirIQ = '/home/labuser/Data/2022/2022_01_27/TestingAnimation/IQ/'
savedirPhase = '/home/labuser/Data/2022/2022_01_27/TestingAnimation/Phase/'

roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)

ch_we_IQ = 24
ch_we_Phase = 43
roach.write_int('conv_phase_ch_we_IQ', ch_we_IQ)
roach.write_int('conv_phase_ch_we_Phase', ch_we_Phase)

 


Icentre = 0
Qcentre = 0
L_phase = 16384 #must be greater than 4 
L_IQ = 16384
steps_phase = 1
steps_IQ = 1
meanlength = 10
pulselength = 1000

phase_threshold = 100
number_of_seconds = 1

final_pulse_count = 0

number_of_phase_values = L_phase * steps_phase

def animate(q):
	x = 0
	x = x + 1
	bin_data_IQ = ''
	bin_data_Phase = ''
	bin_data_IQ_ord = []
	bin_data_IQ_hex = []
	phaseraw = []
	finalphasearray = []
	pulsenumberarray = np.zeros(400)
	pulsenumberarray = pulsenumberarray.tolist()

	total_pulses = 0



	
	
	for n in range(steps_phase):

		roach.write_int('conv_phase_startSnapPhase', 0)
		roach.write_int('conv_phase_startSnapIQ', 0)
		roach.write_int('conv_phase_snapPhase_ctrl', 1)
		roach.write_int('conv_phase_snapIQ_ctrl', 1)
		roach.write_int('conv_phase_snapPhase_ctrl', 0)
		roach.write_int('conv_phase_snapIQ_ctrl', 0)
		roach.write_int('conv_phase_startSnapPhase', 1)
		roach.write_int('conv_phase_startSnapIQ', 1)

		bin_data_Phase = bin_data_Phase + roach.read('conv_phase_snapPhase_bram', 4*L_phase)
		bin_data_IQ = bin_data_IQ + roach.read('conv_phase_snapIQ_bram', 4*L_IQ)
	

	for m in range(steps_phase*L_phase):
		phaseraw.append(struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0])	
	phasevalues = np.array(phaseraw)*360./2**16*4/np.pi
		
	
	#add 360 to negative values
	for k in range(number_of_phase_values):
		if phasevalues[k] < 0:
			phasevalues[k] = phasevalues[k] + 360
	#print'Phase Calculated!'
     


	for j in range(steps_IQ*L_IQ*4):
		#print("j = ", j)
		bin_data_IQ_ord.append(ord(bin_data_IQ[j]))
		bin_data_IQ_hex.append("0x{:02x}".format(bin_data_IQ_ord[j]))	
	

	Iraw = []
	Qraw = []


	for k in range((steps_IQ*L_IQ) / 4):

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

	#print'IQ Calculated!'

	




	george = 0
	bob = 100+meanlength
	 
    
    
	while bob < number_of_phase_values:	
		#print'Looking for pulses'
		#print'bob = ', bob

		if bob+pulselength > number_of_phase_values:
			break
			
		rollingaverage = np.mean(phasevalues[bob-meanlength:bob])
		
		bob_array = phasevalues[bob-100:bob+pulselength] #data to be saved


		counter1 = 0		

		#print'time = ', time.time()
		
		#print'q = ', q
		#print'x = ', x
		x = x + 1
	
		if abs(rollingaverage - phasevalues[bob]) > phase_threshold: 
			print'Pulse!'

			george = george + 1	
                
		
		
			phasefilename = savedirPhase + 'pulse_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'	
			np.savetxt(phasefilename,bob_array,fmt='%.2f')
			#print "Pulse saved!"	
			#total_pulses = total_pulses + 1
			#print'Number of pulses = ', total_pulses
			final_pulse_count = final_pulse_count + 1	
			bob = bob + pulselength
			
		else:
						
			print'No pulse!'				
			
        		bob = bob + 1	
					
		
	plt.cla()
	plt.plot(Iraw, Qraw, '.')
	plt.title('Iraw Vs Qraw')
	plt.xlabel('Iraw')
	plt.ylabel('Qraw')
	plt.grid()

#print("------%s seconds-----" % (time.time() - starttime))	
x = 0
ani = FuncAnimation(plt.gcf(), animate, interval=1000)
plt.show()	
print("Total number of pulses = ", final_pulse_count)   


	
  















































