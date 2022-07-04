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
import csv

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

savedirIQ = '/home/labuser/Data/2022/Ty220411-C_4.10.4_noplasma/3876/test/IQ/'
savedirPhase = '/home/labuser/Data/2022/Ty220411-C_4.10.4_noplasma/3876/test/Phase/'

roach = corr.katcp_wrapper.FpgaClient('192.168.4.10')
time.sleep(2)


ch_we_IQ = 24
roach.write_int('conv_phase_ch_we_IQ', ch_we_IQ)

L_IQ = 16384 #must be greater than 4 
steps_IQ = 1
meanlength = 20
pulselength = 1000
phase_threshold =  30
number_of_seconds = 3

time_completed = 0 #counting time that has run 

#final_pulse_count = 0
total_pulses = 0


#starttime = time.time()

#Icentre = -8870
#Qcentre = 420



#read in IQ loop centre 

foldername = '/home/labuser/Data/IQSweeps/'    
filename = 'IQcentre.txt'
fullname = foldername + filename

#start reader and calculate length of file
with open(fullname, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    row_count = sum(1 for row in csv_reader)  # fileObject is your csv.reader
    
#sweepIvalues = np.zeros(row_count)
#sweepQvalues = np.zeros(row_count)

#print'csv_reader = ', csv_reader
#print'row_count = ', row_count

with open(fullname) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    
    line_count = 0
    for row in csv_reader:    
    	Icentre = row[0] #saves data to array from csv file
    	Qcentre = row[1] #saves data to array from csv file
            
        line_count = line_count + 1   

Icentreint = int(Icentre)
Qcentreint = int(Qcentre)
print'Icentre = ', Icentreint
print'Qcentre = ', Qcentreint

for i in range(64*number_of_seconds):
	
	#total_pulses = 0

	

	bin_data_IQ = ''
	#bin_data_Phase = ''
	bin_data_IQ_ord = []
	bin_data_IQ_hex = []
	#phaseraw = []
	#finalphasearray = []
	#pulsenumberarray = np.zeros(400)
	#pulsenumberarray = pulsenumberarray.tolist()

	



	try:
	
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

	
		Irawarray = np.array(Iraw)			
		Qrawarray = np.array(Qraw)
		phasevalues = -360 * (np.arctan2((Qrawarray-Qcentreint), (Irawarray-Icentreint))) / (2*np.pi)
    		#phasevalues = -360 * (np.arctan2((Qrawarray), (Irawarray))) / (2*np.pi)
		#add 360 to negative values
		#for k in range(number_of_phase_values):
		#	if phasevalues[k] < 0:
		#		phasevalues[k] = phasevalues[k] + 360
     
		george = 0
		bob = 100+meanlength
	 
    
    		number_of_phase_values = len(phasevalues)

		while bob < number_of_phase_values:	
			

			if bob+pulselength > number_of_phase_values:
				break
			
			rollingaverage = np.mean(phasevalues[bob-meanlength:bob])
		
			bob_array = phasevalues[bob-100:bob+pulselength] #data to be saved
			#I_bob_array = Irawarray[bob-100:bob+pulselength] #data to be saved			
			#Q_bob_array = Qrawarray[bob-100:bob+pulselength] #data to be saved			


			if abs(rollingaverage - phasevalues[bob]) > phase_threshold: 

				george = george + 1			

				timestr = datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3]
				phasefilename = savedirPhase + 'pulse_'+timestr +'.txt'	
				np.savetxt(phasefilename,bob_array,fmt='%.2f')
				#print "Phase saved!"
				I_bob_array = Irawarray[bob-100:bob+pulselength] #data to be saved			
				Q_bob_array = Qrawarray[bob-100:bob+pulselength] #data to be saved			
				IQfilename = savedirIQ + 'IQ_'+timestr +'.txt'
				savearray = [I_bob_array, Q_bob_array]	
				np.savetxt(IQfilename,np.column_stack(savearray),fmt='%i ' ' %i' )
				
	
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













































