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

savedirIQ = '/home/labuser/Data/2022/2022_01_21/Setup/IQ/'
savedirPhase = '/home/labuser/Data/2022/2022_01_21/Setup/Phase/'

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
averagelength = 128
phase_threshold = 20
number_of_iterations = 5


for i in range(number_of_iterations):
	print'i = ', i
	#print''
	bin_data_IQ = ''
	bin_data_Phase = ''
	bin_data_IQ_ord = []
	bin_data_IQ_hex = []
	phaseraw = []
	finalphasearray = []
	pulsenumberarray = np.zeros(400)
	pulsenumberarray = pulsenumberarray.tolist()

	total_pulses = 0



	steps_phase = 1
	steps_IQ = 1
	for n in range(steps_phase):

		roach.write_int('conv_phase_startSnapPhase', 0)
		roach.write_int('conv_phase_snapPhase_ctrl', 1)
		roach.write_int('conv_phase_snapPhase_ctrl', 0)
		roach.write_int('conv_phase_startSnapPhase', 1)

		bin_data_Phase = bin_data_Phase + roach.read('conv_phase_snapPhase_bram', 4*L_phase)



	for m in range(steps_phase*L_phase):
		phaseraw.append(struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0])	
	phasevalues = np.array(phaseraw)*360./2**16*4/np.pi

	#plt.figure()
	#plt.plot(phasevalues, '.')
	#plt.title('Phase Vs Time')
	#plt.xlabel('Time')
	#plt.ylabel('Phase')
	#plt.grid()

	number_of_phase_values = len(phasevalues)
    
	#add 360 to negative values
	for k in range(number_of_phase_values):
		if phasevalues[k] < 0:
			phasevalues[k] = phasevalues[k] + 360
     
	george = 0
	bob = 100
	numberofaverages = int((L_phase*steps_phase)/averagelength) 
	phase_means = np.zeros(numberofaverages)
    
	for j in range(numberofaverages):
		phase_means[j] = np.mean(phasevalues[(averagelength*(j+1) - averagelength):averagelength*(j+1)])
           
    
    
	while bob < number_of_phase_values:	
		whichmean = bob//averagelength	

		if bob+300 > number_of_phase_values:
			break
			
		bob_array = phasevalues[bob-100:bob+300]
			
		if abs(phase_means[whichmean] - phasevalues[bob]) > phase_threshold: 
		

			for n in range(steps_IQ):
				roach.write_int('conv_phase_startSnapIQ', 0)
				roach.write_int('conv_phase_snapIQ_ctrl', 1)
				roach.write_int('conv_phase_snapIQ_ctrl', 0)
				roach.write_int('conv_phase_startSnapIQ', 1)
		
				bin_data_IQ = bin_data_IQ + roach.read('conv_phase_snapIQ_bram', 4*L_IQ)


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

			savearray = [Iraw, Qraw]
			IQfilename = savedirIQ + 'IQ_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'	
			np.savetxt(IQfilename,np.column_stack(savearray),fmt='%i ' ' %i' )
			#print "IQ saved!"




			george = george + 1			

			total_pulses*np.ones(400)
			pulsenumber = total_pulses*np.ones(400)
			pulsenumber = pulsenumber.tolist()
				

			#if total_pulses == 0:
			#	finalphasearray.extend(bob_array)
			
					
			#else:
			#	finalphasearray.extend(bob_array)
			#	pulsenumberarray.extend(pulsenumber)
                
		

			#plt.figure()
			#plt.plot(bob_array, '.')
			#plt.title("Pulse " + str(total_pulses))
			#plt.xlabel("Time")		
			#plt.ylabel("Phase (degrees)")
			#plt.grid()
		
			pulsefilename = savedirPhase + 'pulse_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'	
			np.savetxt(pulsefilename,bob_array,fmt='%.2f')
			#print "Phase saved!"	
			total_pulses = total_pulses + 1
			print'Number of pulses = ', total_pulses	
			bob = bob + 200
			
		else:
        		bob = bob + 1			
		
#print("Total number of pulses = ", total_pulses)   


	
  

    
plt.show()













































