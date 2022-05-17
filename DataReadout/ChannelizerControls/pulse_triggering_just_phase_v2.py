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


savedirPhase = '/home/labuser/Data/2022/2022_02_15/Testing/Phase/'

roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)


ch_we_Phase = 43
roach.write_int('conv_phase_ch_we_Phase', ch_we_Phase)

L_phase = 16384 #must be greater than 4 
steps_phase = 1
meanlength = 20
pulselength = 1000
phase_threshold = 50
number_of_seconds = 10

time_completed = 0 #counting time that has run 

#final_pulse_count = 0
total_pulses = 0
number_of_phase_values = L_phase * steps_phase

#starttime = time.time()

for i in range(64*number_of_seconds):
	
	#total_pulses = 0

	

	bin_data_IQ = ''
	bin_data_Phase = ''
	bin_data_IQ_ord = []
	bin_data_IQ_hex = []
	phaseraw = []
	finalphasearray = []
	pulsenumberarray = np.zeros(400)
	pulsenumberarray = pulsenumberarray.tolist()

	



	try:
	
		for n in range(steps_phase):

			roach.write_int('conv_phase_startSnapPhase', 0)
			roach.write_int('conv_phase_snapPhase_ctrl', 1)
			roach.write_int('conv_phase_snapPhase_ctrl', 0)
			roach.write_int('conv_phase_startSnapPhase', 1)

			bin_data_Phase = bin_data_Phase + roach.read('conv_phase_snapPhase_bram', 4*L_phase)
	

		for m in range(steps_phase*L_phase):
			phaseraw.append(struct.unpack('>h', bin_data_Phase[4*m+2:4*m+4])[0])	
		phasevalues = np.array(phaseraw)*360./2**16*4/np.pi

	

	
    
		#add 360 to negative values
		#for k in range(number_of_phase_values):
		#	if phasevalues[k] < 0:
		#		phasevalues[k] = phasevalues[k] + 360
     
		george = 0
		bob = 100+meanlength
	 
    
    
		while bob < number_of_phase_values:	
			

			if bob+pulselength > number_of_phase_values:
				break
			
			rollingaverage = np.mean(phasevalues[bob-meanlength:bob])
		
			bob_array = phasevalues[bob-100:bob+pulselength] #data to be saved
			
			if abs(rollingaverage - phasevalues[bob]) > phase_threshold: 

				george = george + 1			

				phasefilename = savedirPhase + 'pulse_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'	
				np.savetxt(phasefilename,bob_array,fmt='%.2f')
				#print "Phase saved!"	
				total_pulses = total_pulses + 1
				#print'Number of pulses = ', total_pulses
				#final_pulse_count = final_pulse_count + total_pulses
				#print'Pulse saved' 	
				bob = bob + pulselength
			
			else:
        			bob = bob + 1			
		
	
		if np.mod(i, 64) == 0:
			print''
			print'time = ', time_completed, ' seconds'
			print'pulses per second = ', total_pulses
			total_pulses = 0
			#print''
			time_completed = time_completed + 1 

	
	except RuntimeError:
		print'RuntimeError, skipping this iteration'
		continue #changed break to continue

	
	
	

#print("------%s seconds-----" % (time.time() - starttime))		
#print("Total number of pulses = ", final_pulse_count)   


	
  

    
#plt.show()













































