import sys, os, random, math, array, fractions,time,datetime,pickle
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import socket
import matplotlib, corr, time, struct, numpy
from datetime import datetime
#from bitstring import BitArray
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from tables import *
from lib import iqsweep

#Things to update:
#DONE...make filename_NEW.txt only hold information for channel that is changed
#DONE...delete resonator (change FIR?)
#DONE...Do not add custom threshold when zooming or panning plot
#DONE...roughly calculate baseline from snapshot data and show on plot
#WORKING...show originally calculated median/threshold as faded line




class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Channelizer 2')
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        self.dacStatus = 'off'
	self.contsnapStatus = 'off'
        self.dramStatus = 'off'
        self.tapStatus = 'off'
        self.socketStatus = 'off'
        self.numFreqs=0
        self.ch_all = []
        self.attens = numpy.array([1. for i in range(256)])
        self.freqRes = 7812.5
        self.sampleRate = 512e6
        self.zeroChannels = [0]*256
        #writing threshold to register
        self.thresholds, self.medians = numpy.array([0.]*256), numpy.array([0.]*256)
        self.customThresholds = numpy.array([360.]*256)
        self.customResonators=numpy.array([[0.0,-1]]*256)   #customResonator[ch]=[freq,atten]
        
    def openClient(self):
        
	self.status_text.setText('connecting...')
	print 'connecting...'	
	
	self.roach = corr.katcp_wrapper.FpgaClient(self.textbox_roachIP.text(),7147)
	time.sleep(2)
	print 'programming roach...'
	
        self.roach.progdev('snap_raw_iq_0303_2021_Mar_03_1222.bof')
	#working boffile as of 16/12/2020: chan_snap_v3_2012_Oct_30_1216.bof
	#trying snap_rawIQ.bof and snap_raw_iq_2018_Dec_11_1630.bof on 16/12/2020
        #time.sleep(2)
        self.status_text.setText('connection established')
        print 'Connected to ',self.textbox_roachIP.text()
        self.button_openClient.setDisabled(True)

    def loadFIRcoeffs(self):
        N_freqs = len(map(float, unicode(self.textedit_DACfreqs.toPlainText()).split()))
        taps = 26
        
        for ch in range(N_freqs):
            # If the resonator's attenuation is >=99 then its FIR should be zeroed
            if self.zeroChannels[ch]:
                lpf = numpy.array([0.]*taps)*(2**11-1)
                print 'deleted ch ',ch
            else:
                lpf = numpy.array(self.fir)*(2**11-1)
                print ch
                #lpf = numpy.array([1.]+[0]*(taps-1))*(2**11-1)
        #    26 tap, 25 us matched fir
                #lpf = numpy.array([0.0875788844768 , 0.0840583257978 , 0.0810527406206 , 0.0779008825067 , 0.075106964962 , 0.0721712998256 , 0.0689723729398 , 0.066450095496 , 0.0638302570705 , 0.0613005685486 , 0.0589247737004 , 0.0565981917436 , 0.0544878914297 , 0.0524710948658 , 0.0503447054014 , 0.0483170854189 , 0.0463121066637 , 0.044504238059 , 0.0428469827102 , 0.0410615366471 , 0.0395570640218 , 0.0380071830756 , 0.0364836787854 , 0.034960959124 , 0.033456372241 , 0.0321854467182])*(2**11-1)
                #26 tap, 20 us matched fir
                #lpf = numpy.array([ 0.102806030245 , 0.097570344415 , 0.0928789946181 , 0.0885800360545 , 0.0841898850361 , 0.079995145104 , 0.0761649967857 , 0.0724892663141 , 0.0689470889358 , 0.0657584886557 , 0.0627766233242 , 0.0595952531565 , 0.0566356208278 , 0.053835736579 , 0.0510331408751 , 0.048623806127 , 0.0461240096904 , 0.0438134132285 , 0.0418265743203 , 0.0397546477453 , 0.0377809254888 , 0.0358044897245 , 0.0338686929847 , 0.0321034547839 , 0.0306255734188 , 0.0291036235859 ])*(2**11-1)
                #26 tap, 30 us matched fir
                #lpf = numpy.array([ 0.0781747107378 , 0.0757060398243 , 0.0732917718492 , 0.0708317694778 , 0.0686092845217 , 0.0665286923521 , 0.0643467681477 , 0.0621985982971 , 0.0600681642401 , 0.058054873199 , 0.0562486467178 , 0.0542955553149 , 0.0527148880657 , 0.05096365681 , 0.0491121116212 , 0.0474936094733 , 0.0458638771941 , 0.0443219286645 , 0.0429290438102 , 0.0415003391096 , 0.0401174498302 , 0.0386957715665 , 0.0374064708747 , 0.0362454802408 , 0.0350170176804 , 0.033873302383 ])*(2**11-1)
                #lpf = lpf[::-1]
                #    26 tap, lpf, 250 kHz,
                #lpf = numpy.array([-0 , 0.000166959420533 , 0.00173811663844 , 0.00420937801998 , 0.00333739357391 , -0.0056305703275 , -0.0212738104942 , -0.0318529375832 , -0.0193635986879 , 0.0285916612022 , 0.106763943766 , 0.18981814328 , 0.243495321192 , 0.243495321192 , 0.18981814328 , 0.106763943766 , 0.0285916612022 , -0.0193635986879 , -0.0318529375832 , -0.0212738104942 , -0.0056305703275 , 0.00333739357391 , 0.00420937801998 , 0.00173811663844 , 0.000166959420533 , -0])*(2**11-1)
                #    26 tap, lpf, 125 kHz.
                #lpf = numpy.array([0 , -0.000431898216436 , -0.00157886921107 , -0.00255492263971 , -0.00171727439076 , 0.00289724121972 , 0.0129123447233 , 0.0289345497995 , 0.0500906370566 , 0.0739622085341 , 0.0969821586979 , 0.115211955161 , 0.125291869266 , 0.125291869266 , 0.115211955161 , 0.0969821586979 , 0.0739622085341 , 0.0500906370566 , 0.0289345497995 , 0.0129123447233 , 0.00289724121972 , -0.00171727439076 , -0.00255492263971 , -0.00157886921107 , -0.000431898216436 , -0])*(2**11-1)
                #    Generic 40 tap matched filter for 25 us lifetime pulse
                #lpf = numpy.array([0.153725595011 , 0.141052390733 , 0.129753816201 , 0.119528429291 , 0.110045314901 , 0.101336838027 , 0.0933265803805 , 0.0862038188673 , 0.0794067694409 , 0.0729543134914 , 0.0674101836798 , 0.0618283869464 , 0.0567253144676 , 0.0519730940444 , 0.047978953698 , 0.043791412767 , 0.0404560656757 , 0.0372466775252 , 0.0345000956808 , 0.0319243455811 , 0.0293425115323 , 0.0268372778298 , 0.0245216835234 , 0.0226817116475 , 0.0208024488535 , 0.0189575043357 , 0.0174290665862 , 0.0158791788119 , 0.0144611054123 , 0.0132599563305 , 0.0121083419203 , 0.0109003580368 , 0.0100328742978 , 0.00939328253743 , 0.00842247241585 , 0.00789304712484 , 0.00725494259117 , 0.00664528407122 , 0.00606688645845 , 0.00552041438208])*(2**11-1)                
                #lpf = lpf[::-1]

            for n in range(taps/2):
                coeff0 = int(lpf[2*n])
                coeff1 = int(lpf[2*n+1])
                coeff0 = numpy.binary_repr(int(lpf[2*n]), 12)
                coeff1 = numpy.binary_repr(int(lpf[2*n+1]), 12)
                coeffs = int(coeff1+coeff0, 2)
                coeffs_bin = struct.pack('>l', coeffs)
                register_name = 'FIR_b' + str(2*n) + 'b' + str(2*n+1)
                self.roach.write(register_name, coeffs_bin)
                self.roach.write_int('FIR_load_coeff', (ch<<1) + (1<<0))
                self.roach.write_int('FIR_load_coeff', (ch<<1) + (0<<0))
        
        # Inactive channels will also be zeroed.
        lpf = numpy.array([0.]*taps)
        for ch in range(N_freqs, 256):
            for n in range(taps/2):
                #coeffs = struct.pack('>h', lpf[2*n]) + struct.pack('>h', lpf[2*n+1])
                coeffs = struct.pack('>h', lpf[2*n+1]) + struct.pack('>h', lpf[2*n])
                register_name = 'FIR_b' + str(2*n) + 'b' + str(2*n+1)
                self.roach.write(register_name, coeffs)
                self.roach.write_int('FIR_load_coeff', (ch<<1) + (1<<0))
                self.roach.write_int('FIR_load_coeff', (ch<<1) + (0<<0))
                
        print 'done loading fir.'
        self.status_text.setText('FIRs loaded')
     
    def find_nearest(self, array, value):
        idx=(numpy.abs(array-value)).argmin()
        return idx

    def loadCustomThresholds(self):
        freqFile =str(self.textbox_freqFile.text())
        if freqFile[-8:] == '_NEW.txt':
            freqFile=freqFile[:-8]+'_THRESHOLD.txt'
        else:
            freqFile=freqFile[:-4]+'_THRESHOLD.txt'
        try:
            x=numpy.loadtxt(freqFile)
            self.customThresholds = numpy.array([360.]*256)
            if type(x[0]) == numpy.ndarray:
                for arr in x:
                    self.customThresholds[int(arr[0])]=arr[1]
            else:
                self.customThresholds[int(x[0])]=x[1]
            print 'Custom Thresholds loaded from',freqFile
        except IOError:
            #No custom thresholds to load
            pass


    def rmCustomThreshold(self):
        ch = int(self.textbox_channel.text())
        if self.customThresholds[ch] != 360.0:
            self.customThresholds[ch]=360.0
            print "Custom Threshold from channel",ch,"removed."
            #self.loadSingleThreshold(ch)
            scale_to_angle = 360./2**16*4/numpy.pi
            self.roach.write_int('capture_threshold', int(self.thresholds[ch]/scale_to_angle))
            self.roach.write_int('capture_load_thresh', (ch<<1)+(1<<0))
            self.roach.write_int('capture_load_thresh', (ch<<1)+(0<<0))
            print "Old threshold updated to roach"

            freqFile =str(self.textbox_freqFile.text())
            if freqFile[-8:] == '_NEW.txt':
                freqFile=freqFile[:-8]+'_THRESHOLD.txt'
            else:
                freqFile=freqFile[:-4]+'_THRESHOLD.txt'
            try:
                x=numpy.loadtxt(freqFile)
                f=open(freqFile,'w')
                if type(x[0]) == numpy.ndarray:
                    for arr in x:
                        #print 'arr',arr
                        if arr[0]!=ch:
                            f.write(str(int(arr[0]))+'\t'+str(float(arr[1]))+'\n')
                else:
                    if x[0]!=ch:
                        f.write(str(int(x[0]))+'\t'+str(float(x[1]))+'\n')
                print "Removed Custom Threshold on channel ",ch," from ",freqFile
                self.status_text.setText("Removed Custom Threshold on channel "+str(ch)+" from "+str(freqFile))
                f.close()
            except IOError:
                print 'Unable to remove custom threshold from channel',ch
        else:
            print "No custom threshold set for channel",ch


    def setCustomThreshold(self,event):
        scale_to_angle = 360./2**16*4/numpy.pi
        ch = int(self.textbox_channel.text())
        newThreshold = event.ydata
        #print "Threshold selected:",newThreshold
        if event.ydata != None and self.mpl_toolbar.mode == '':
            self.loadSingleThreshold(ch)                #resets median
            newThreshold = newThreshold - self.medians[ch]      #for threshold adjusting firmware only!
            self.customThresholds[ch] = newThreshold
            newThreshold = int(newThreshold/scale_to_angle)
            #print "writing threshold to register:",newThreshold
            #print "median for channel ",ch,": ",self.medians[ch]
            #self.customThresholds[ch] = newThreshold
        
            #print "new threshold: ",newThreshold
            #print "old threshold: ",self.thresholds[ch]/scale_to_angle
        
            self.roach.write_int('capture_threshold', newThreshold)
            self.roach.write_int('capture_load_thresh', (ch<<1)+(1<<0))
            self.roach.write_int('capture_load_thresh', (ch<<1)+(0<<0))
            print "channel: ", ch, "median: ", self.medians[ch], "new threshold: ", scale_to_angle*newThreshold
            #print self.customThresholds[ch]
            #self.loadSingleThreshold(ch)

            freqFile =str(self.textbox_freqFile.text())
            if freqFile[-8:] == '_NEW.txt':
                freqFile=freqFile[:-8]+'_THRESHOLD.txt'
            else:
                freqFile=freqFile[:-4]+'_THRESHOLD.txt'
            try:
                f=open(freqFile,'a')
                f.write(str(int(ch))+'\t'+str(float(self.customThresholds[ch]))+'\n')
                f.close()
                print 'Saved custom threshold to',freqFile
            except IOError:
                print 'ERROR: There was a problem saving thresholds to',freqFile

    def loadThresholds(self):
        """    Takes two time streams and concatenates together for a longer sample.
                median is used instead of mean.
                """
        x = raw_input('Is the lamp off? ')
        Nsigma = float(self.textbox_Nsigma.text())
        N_freqs = len(map(float, unicode(self.textedit_DACfreqs.toPlainText()).split()))
        self.thresholds, self.medians = numpy.array([0.]*N_freqs), numpy.array([0.]*N_freqs)

        #for ch in range(N_freqs):
            #print 'attempting to load channel: ',ch
        #    self.loadSingleThreshold(ch)

        steps = int(self.textbox_timeLengths.text())
        L = 2**10
        scale_to_angle = 360./2**16*4/numpy.pi
        threshInfo = {}
        threshInfo['roachNum'] = roachNum
        threshInfo['scaleToAngle'] = scale_to_angle
        threshInfo['N_freqs'] = N_freqs
        now = datetime.datetime.now()
        threshInfo['now'] = now
        threshInfo['nowAscii'] = datetime.datetime.strftime(now,"%c")
        threshInfo['phase'] = {}
        threshInfo['phaseHg'] = {}
        threshInfo['phaseBins'] = {}


        for ch in range(N_freqs):
            bin_data_phase = ''
            for n in range(steps):
                self.roach.write_int('ch_we', ch)
                self.roach.write_int('startSnap', 0)
                self.roach.write_int('snapPhase_ctrl', 1)
                self.roach.write_int('snapPhase_ctrl', 0)
                self.roach.write_int('startSnap', 1)
                time.sleep(0.001)
                bin_data_phase = bin_data_phase + self.roach.read('snapPhase_bram', 4*L)    
            
            phase = []
            for m in range(steps*L):
                phase.append(struct.unpack('>h', bin_data_phase[m*4+2:m*4+4])[0])
                phase.append(struct.unpack('>h', bin_data_phase[m*4+0:m*4+2])[0])
            phase = numpy.array(phase)
            threshInfo['phase'][ch] = phase.copy()
            #phase_avg = numpy.median(self.phase)
            #sigma = self.phase.std()

            n,bins= numpy.histogram(phase,bins=100)
            threshInfo['phaseHg'][ch] = n.copy()
            threshInfo['phaseBins'][ch] = bins.copy()
            n = numpy.array(n,dtype='float32')/numpy.sum(n)
            tot = numpy.zeros(len(bins))
            for i in xrange(len(bins)):
                tot[i] = numpy.sum(n[:i])
            bins1 = .5*(bins[1:]+bins[:-1])
            med = bins[self.find_nearest(tot,0.5)]
            thresh = bins[self.find_nearest(tot,0.05)]
            #threshold = int(med-Nsigma*abs(med-thresh))
            threshold = int(-Nsigma*abs(med-thresh))    #for threshold adjusting firmware!
            
            
            #threshold = int((phase_avg - Nsigma*sigma))
            # -25736 = -180 degrees
            if threshold < -25736:
                threshold = -25736
            self.thresholds[ch] = scale_to_angle*threshold
            self.medians[ch] = scale_to_abngle*med

            if self.customThresholds[ch] != 360.0:
                threshold = self.customThresholds[ch]/scale_to_angle
                if threshold < -25736:
                    threshold = -25736
                print 'Channel '+str(ch)+' has a custom threshold'

            self.roach.write_int('capture_threshold', threshold)
            self.roach.write_int('capture_load_thresh', (ch<<1)+(1<<0))
            self.roach.write_int('capture_load_thresh', (ch<<1)+(0<<0))
            print "channel: ", ch, "median: ", scale_to_angle*med, "threshold: ", scale_to_angle*threshold
            #print "channel: ", ch, "avg: ", scale_to_angle*phase_avg, "sigma: ", scale_to_angle*sigma, "threshold: ", scale_to_angle*threshold

        threshInfo['medians'] = self.medians.copy()
        threshInfo['thresholds'] = self.thresholds.copy()
        nowStr = datetime.datetime.strftime(now,"%Y%m%d-%H%M%S")
        pklFileName = "thresh_%d_%s.pkl"%(roachNum,nowStr)
        #print 'Dump threshold infomation to ',os.path.join(os.environ['MKID_DATA_DIR'],pklFileName)
        #pickle.dump(threshInfo,open(os.path.join(os.environ['MKID_DATA_DIR'],pklFileName),'wb'))
        self.status_text.setText('Thresholds loaded and written to %s'%pklFileName)
        print 'Done loading thresholds'

    def loadSingleThreshold(self,ch):
        #print 'ch: ',ch
        L = 2**10
        scale_to_angle = 360./2**16*4/numpy.pi
        Nsigma = float(self.textbox_Nsigma.text())
        bin_data_phase = ''
        steps = int(self.textbox_timeLengths.text())
        for n in range(steps):
            self.roach.write_int('ch_we', ch)
            self.roach.write_int('startSnap', 0)
            self.roach.write_int('snapPhase_ctrl', 1)
            self.roach.write_int('snapPhase_ctrl', 0)
            self.roach.write_int('startSnap', 1)
            time.sleep(0.001)
            bin_data_phase = bin_data_phase + self.roach.read('snapPhase_bram', 4*L)    
            
        phase = []
        for m in range(steps*L):
            phase.append(struct.unpack('>h', bin_data_phase[m*4+2:m*4+4])[0])
            phase.append(struct.unpack('>h', bin_data_phase[m*4+0:m*4+2])[0])
        phase = numpy.array(phase)
        #phase_avg = numpy.median(phase)
        #sigma = phase.std()

        n,bins= numpy.histogram(phase,bins=100)
        n = numpy.array(n,dtype='float32')/numpy.sum(n)
        tot = numpy.zeros(len(bins))
        for i in xrange(len(bins)):
            tot[i] = numpy.sum(n[:i])
        bins1 = .5*(bins[1:]+bins[:-1])
        med = bins[self.find_nearest(tot,0.5)]
        thresh = bins[self.find_nearest(tot,0.05)]
        #threshold = int(med-Nsigma*abs(med-thresh))
        threshold = int(-Nsigma*abs(med-thresh))    #for threshold adjusting firmware!
            
            
        #threshold = int((phase_avg - Nsigma*sigma))
        # -25736 = -180 degrees
        if threshold < -25736:
            threshold = -25736
        self.thresholds[ch] = scale_to_angle*threshold
        self.medians[ch] = scale_to_angle*med

        if self.customThresholds[ch] != 360.0:
            threshold = self.customThresholds[ch]/scale_to_angle
            if threshold < -25736:
                threshold = -25736
            print 'Channel '+str(ch)+' has a custom threshold'

        self.roach.write_int('capture_threshold', threshold)
        self.roach.write_int('capture_load_thresh', (ch<<1)+(1<<0))
        self.roach.write_int('capture_load_thresh', (ch<<1)+(0<<0))
        print "channel: ", ch, "median: ", scale_to_angle*med, "threshold: ", scale_to_angle*threshold
        #print "channel: ", ch, "avg: ", scale_to_angle*phase_avg, "sigma: ", scale_to_angle*sigma, "threshold: ", scale_to_angle*threshold


    def snapshot(self):       
        self.displayResonatorProperties()
        ch_we = int(self.textbox_channel.text())
	#print ch_we
	#I0_we = 1
        self.roach.write_int('ch_we', ch_we)
	#self.roach.write_int('I0_we', I0_we)
	#self.roach.write_int('I1_we', ch_we)
        #print self.roach.read_int('ch_we')
        steps = int(self.textbox_snapSteps.text())
        L = 2**10
        bin_data_phase = ''
	bin_data_I = ''	

        for n in range(steps):
            self.roach.write_int('startSnap', 0)
            self.roach.write_int('snapPhase_ctrl', 1)
            self.roach.write_int('snapPhase_ctrl', 0)
            self.roach.write_int('startSnap', 1)	
            time.sleep(0.001)
            bin_data_phase = bin_data_phase + self.roach.read('snapPhase_bram', 4*L)
	       
        	
	for n in range(steps):
	    #self.roach.write_int('startSnap', 0)
            self.roach.write_int('conv_phase_snapI_ctrl', 1)
            self.roach.write_int('conv_phase_snapI_ctrl', 0)	
	    #self.roach.write_int('startSnap', 1)
	    time.sleep(0.001)
	    
	    bin_data_I = bin_data_I + self.roach.read('conv_phase_snapI_bram', 4*L)
	    #bin_data_I0 = bin_data_I0 + str(self.roach.read_uint('snapI0_bram'))
	    #bin_data_I = bin_data_I + str(self.roach.read_int('conv_phase_snapI_bram'))
	    #print('bin_data_I = ', bin_data_I0) 

	
    
        phase = []
        for m in range(steps*L):
            phase.append(struct.unpack('>h', bin_data_phase[m*4+2:m*4+4])[0])
            phase.append(struct.unpack('>h', bin_data_phase[m*4+0:m*4+2])[0])
	phase = numpy.array(phase)*360./2**16*4/numpy.pi
	#phase = numpy.array(phase)
	print 'phase: ', phase
	

	Iraw0 = []
	Iraw1 = []
	Iraw2 = []
	Iraw3 = []
	Iraw4 = []
	Iraw5 = []
	Iraw6 = []
	Iraw7 = []
	Iraw8 = []
	Iraw9 = []
	Iraw10 = []
	Iraw11 = []
	Iraw12 = []
	Iraw13 = []
	Iraw14 = []
	Iraw15 = []
	Iraw16 = []
	Iraw17 = []
	Iraw18 = []
	Iraw19 = []
	
	Iraw20 = []
	Iraw21 = []
	Iraw22 = []
	Iraw23 = []
	Iraw24 = []
	Iraw25 = []
	Iraw26 = []
	Iraw27 = []
	Iraw28 = []
	Iraw29 = []
	Iraw30 = []
	Iraw31 = []
	Iraw32 = []
	Iraw33 = []
	Iraw34 = []
	Iraw35 = []
	Iraw36 = []
	Iraw37 = []
	Iraw38 = []
	Iraw39 = []

	Iraw40 = []
	Iraw41 = []
	Iraw42 = []
	Iraw43 = []

	phaseraw = []
	

        for m in range(steps*L):
            Iraw0.append(struct.unpack('>l', bin_data_I[m*4:m*4+4])[0])
	    Iraw1.append(struct.unpack('>l', bin_data_I[m+1:m+5])[0])
	    Iraw2.append(struct.unpack('>l', bin_data_I[m+2:m+6])[0])
	    Iraw3.append(struct.unpack('>l', bin_data_I[m+3:m+7])[0])
	    Iraw4.append(struct.unpack('<l', bin_data_I[m*4:m*4+4])[0])
	    Iraw5.append(struct.unpack('<l', bin_data_I[m+1:m+5])[0])
	    Iraw6.append(struct.unpack('<l', bin_data_I[m+2:m+6])[0])
	    Iraw7.append(struct.unpack('<l', bin_data_I[m+3:m+7])[0])
	     
	    Iraw8.append(struct.unpack('>h', bin_data_I[m*2+2:m*2+4])[0])
	    Iraw9.append(struct.unpack('>h', bin_data_I[m*2+3:m*2+5])[0])
	    Iraw10.append(struct.unpack('<h', bin_data_I[m:m+2])[0])
	    Iraw11.append(struct.unpack('<h', bin_data_I[m+1:m+3])[0])

	    Iraw12.append(struct.unpack('>i', bin_data_I[m*4:m*4+4])[0])
	    Iraw13.append(struct.unpack('>i', bin_data_I[m+1:m+5])[0])
	    Iraw14.append(struct.unpack('>i', bin_data_I[m+2:m+6])[0])
	    Iraw15.append(struct.unpack('>i', bin_data_I[m+3:m+7])[0])
	    Iraw16.append(struct.unpack('<i', bin_data_I[m*4:m*4+4])[0])
	    Iraw17.append(struct.unpack('<i', bin_data_I[m+1:m+5])[0])
	    Iraw18.append(struct.unpack('<i', bin_data_I[m+2:m+6])[0])
	    Iraw19.append(struct.unpack('<i', bin_data_I[m+3:m+7])[0])
	    


	    Iraw20.append(struct.unpack('>L', bin_data_I[m*4:m*4+4])[0])
	    Iraw21.append(struct.unpack('>L', bin_data_I[m+1:m+5])[0])
	    Iraw22.append(struct.unpack('>L', bin_data_I[m+2:m+6])[0])
	    Iraw23.append(struct.unpack('>L', bin_data_I[m+3:m+7])[0])
	    Iraw24.append(struct.unpack('<L', bin_data_I[m*4:m*4+4])[0])
	    Iraw25.append(struct.unpack('<L', bin_data_I[m+1:m+5])[0])
	    Iraw26.append(struct.unpack('<L', bin_data_I[m+2:m+6])[0])
	    Iraw27.append(struct.unpack('<L', bin_data_I[m+3:m+7])[0])
	     
	    Iraw28.append(struct.unpack('>H', bin_data_I[m*2:m*2+2])[0])
	    Iraw29.append(struct.unpack('>H', bin_data_I[m+1:m+3])[0])
	    Iraw30.append(struct.unpack('<H', bin_data_I[m:m+2])[0])
	    Iraw31.append(struct.unpack('<H', bin_data_I[m+1:m+3])[0])

	    Iraw32.append(struct.unpack('>I', bin_data_I[m*4:m*4+4])[0])
	    Iraw33.append(struct.unpack('>I', bin_data_I[m+1:m+5])[0])
	    Iraw34.append(struct.unpack('>I', bin_data_I[m+2:m+6])[0])
	    Iraw35.append(struct.unpack('>I', bin_data_I[m+3:m+7])[0])
	    Iraw36.append(struct.unpack('<I', bin_data_I[m*4:m*4+4])[0])
	    Iraw37.append(struct.unpack('<I', bin_data_I[m+1:m+5])[0])
	    Iraw38.append(struct.unpack('<I', bin_data_I[m+2:m+6])[0])
	    Iraw39.append(struct.unpack('<I', bin_data_I[m+3:m+7])[0])

	    Iraw40.append(struct.unpack('>q', bin_data_I[m:m+8])[0])
	    Iraw41.append(struct.unpack('<q', bin_data_I[m:m+8])[0])
	    Iraw42.append(struct.unpack('>Q', bin_data_I[m:m+8])[0])
	    Iraw43.append(struct.unpack('<Q', bin_data_I[m:m+8])[0])

	    phaseraw.append(struct.unpack('>h', bin_data_phase[m*4:m*4+2])[0])


            #Iraw.append(struct.unpack('>h', bin_data_I[m*4+0:m*4+2])[0])
	
	Iraw0 = numpy.array(Iraw0)
	Iraw1 = numpy.array(Iraw1)
	Iraw2 = numpy.array(Iraw2)
	Iraw3 = numpy.array(Iraw3)
	Iraw4 = numpy.array(Iraw4)
	Iraw5 = numpy.array(Iraw5)
	Iraw6 = numpy.array(Iraw6)
	Iraw7 = numpy.array(Iraw7)
	Iraw8 = numpy.array(Iraw8)
	Iraw9 = numpy.array(Iraw9)
	Iraw10 = numpy.array(Iraw10)
	Iraw11 = numpy.array(Iraw11)
	Iraw12 = numpy.array(Iraw12)
	Iraw13 = numpy.array(Iraw13)
	Iraw14 = numpy.array(Iraw14)
	Iraw15 = numpy.array(Iraw15)
	Iraw16 = numpy.array(Iraw16)
	Iraw17 = numpy.array(Iraw17)
	Iraw18 = numpy.array(Iraw18)
	Iraw19 = numpy.array(Iraw19)

	Iraw20 = numpy.array(Iraw20)
	Iraw21 = numpy.array(Iraw21)
	Iraw22 = numpy.array(Iraw22)
	Iraw23 = numpy.array(Iraw23)
	Iraw24 = numpy.array(Iraw24)
	Iraw25 = numpy.array(Iraw25)
	Iraw26 = numpy.array(Iraw26)
	Iraw27 = numpy.array(Iraw27)
	Iraw28 = numpy.array(Iraw28)
	Iraw29 = numpy.array(Iraw29)
	Iraw30 = numpy.array(Iraw30)
	Iraw31 = numpy.array(Iraw31)
	Iraw32 = numpy.array(Iraw32)
	Iraw33 = numpy.array(Iraw33)
	Iraw34 = numpy.array(Iraw34)
	Iraw35 = numpy.array(Iraw35)
	Iraw36 = numpy.array(Iraw36)
	Iraw37 = numpy.array(Iraw37)
	Iraw38 = numpy.array(Iraw38)
	Iraw39 = numpy.array(Iraw39)

	Iraw40 = numpy.array(Iraw40)
	Iraw41 = numpy.array(Iraw41)
	Iraw42 = numpy.array(Iraw42)
	Iraw43 = numpy.array(Iraw43)
		

	phaseraw = numpy.array(phaseraw)	


	print('Iraw0 = ', Iraw0)	
	print('Iraw1 = ', Iraw1)	
	print('Iraw2 = ', Iraw2)	
	print('Iraw3 = ', Iraw3)	
	print('Iraw4 = ', Iraw4)	
	print('Iraw5 = ', Iraw5)	
	print('Iraw6 = ', Iraw6)	
	print('Iraw7 = ', Iraw7)	
	print('Iraw8 = ', Iraw8)	
	print('Iraw9 = ', Iraw9)	
	print('Iraw10 = ', Iraw10)	
	print('Iraw11 = ', Iraw11)
	print('Iraw12 = ', Iraw12)	
	print('Iraw13 = ', Iraw13)	
	print('Iraw14 = ', Iraw14)	
	print('Iraw15 = ', Iraw15)	
	print('Iraw16 = ', Iraw16)	
	print('Iraw17 = ', Iraw17)	
	print('Iraw18 = ', Iraw18)	
	print('Iraw19 = ', Iraw19)

	print('Iraw20 = ', Iraw20)	
	print('Iraw21 = ', Iraw21)	
	print('Iraw22 = ', Iraw22)	
	print('Iraw23 = ', Iraw23)	
	print('Iraw24 = ', Iraw24)	
	print('Iraw25 = ', Iraw25)	
	print('Iraw26 = ', Iraw26)	
	print('Iraw27 = ', Iraw27)	
	print('Iraw28 = ', Iraw28)	
	print('Iraw29 = ', Iraw29)	
	print('Iraw30 = ', Iraw30)	
	print('Iraw31 = ', Iraw31)
	print('Iraw32 = ', Iraw32)	
	print('Iraw33 = ', Iraw33)	
	print('Iraw34 = ', Iraw34)	
	print('Iraw35 = ', Iraw35)	
	print('Iraw36 = ', Iraw36)	
	print('Iraw37 = ', Iraw37)	
	print('Iraw38 = ', Iraw38)	
	print('Iraw39 = ', Iraw39)

	#print('Iraw40 = ', Iraw40)	
	#print('Iraw41 = ', Iraw41)	
	#print('Iraw42 = ', Iraw42)	
	#print('Iraw43 = ', Iraw43)
	

	print('phaseraw = ', phaseraw)		
	

	self.axes0.clear()
        self.axes1.clear()
        #self.axes1.plot(phase, '.-', [self.thresholds[ch_we]]*2*L*steps, 'r.', [self.medians[ch_we]]*2*L*steps, 'g.')
        saveDir = str('/home/labuser/Desktop/SDR-master/DataReadout/IQSnapshots/') #saves IQ data here
  



        if steps <= 1000:
       	    self.axes0.plot(Iraw8, 'b.', markersize=1) #changed to plot I0 versus time
	    self.axes1.plot(Iraw9, 'b.', markersize=1) #changed to plot I0 versus time
	    
	print 'Phase length = ', len(phase)

        	
        med=numpy.median(phase)
	sd = numpy.std(phase) #added to see if shifting LO has any effect on data

        print 'ch:',ch_we,'median:',med, 'standard deviation:', sd
	

        thresh=self.thresholds[ch_we]

        if self.customThresholds[ch_we] != 360.0:
            thresh=self.customThresholds[ch_we]
            #print "Custom Threshold: ", thresh,

        #self.axes1.plot([thresh+med]*2*L*steps,'r.',[med]*2*L*steps,'g.',alpha=1)

        med=self.medians[ch_we]
        self.canvas.draw()
        print "snapshot taken"

    def longsnapshot(self):        
        self.displayResonatorProperties()
        ch_we = int(self.textbox_channel.text())
        self.roach.write_int('ch_we', ch_we)
	self.roach.write_int('I0_we', ch_we)
        #print self.roach.read_int('ch_we')
        
        steps = int(self.textbox_snapSteps.text())
        L = 2**10
        numQDRSamples=2**19
        numBytesPerSample=4
        nLongsnapSamples = numQDRSamples*2*steps # 2 16-bit samples per 32-bit QDR word
        bin_data_phase = ''
        #qdr_data_str = ''
	I1_data_str = ''
	#IQdata = ''
	
	

        for n in range(steps):
            self.roach.write_int('snapPhase_ctrl', 0)
            self.roach.write_int('snapqdrI1_ctrl',0)
            self.roach.write_int('startSnap', 0)
	    self.roach.write_int('startSnapI1', 0)
            #self.roach.write_int('snapqdrI1_ctrl', 1)
            self.roach.write_int('startSnap', 1)
	    self.roach.write_int('startSnapI1', 1)
            time.sleep(2)
            bin_data_phase = bin_data_phase + self.roach.read('snapPhase_bram', 4*L)  
            I1_data_str = I1_data_str + self.roach.read('snapqdrI1_bram', 4*L)
	
	print 'bin_data_phase: ', bin_data_phase 
	print 'I1_data_str: ', I1_data_str	

	#print 'bin_data_phase: ', bin_data_phase
	#IQdata = self.roach.read('avgIQ_bram', 4*2*256) #attempting to save IQ data
	#I = struct.unpack('>l', IQdata[4*n:4*n+4])[0]-self.iq_centers[n].real
        #Q = struct.unpack('>l', IQdata[4*(n+256):4*(n+256)+4])[0]-self.iq_centers[n].imag
	#print 'I: ', I 
	#print 'Q: ', Q
	#print 'I centre: ', self.iq_centers[n].real
	#print 'Q centre: ', self.iq_centers[n].imag
    
        self.roach.write_int('snapPhase_ctrl', 0)
        self.roach.write_int('snapqdrI1_ctrl',0)
        self.roach.write_int('startSnap', 0)
	self.roach.write_int('startSnapI1', 0)
        
	phase = []
        for m in range(steps*L):
            phase.append(struct.unpack('>h', bin_data_phase[m*4+2:m*4+4])[0])
            phase.append(struct.unpack('>h', bin_data_phase[m*4+0:m*4+2])[0])
	
	I1 = []
        for m in range(steps*L):
            I1.append(struct.unpack('>h', I1_data_str[m*4+2:m*4+4])[0])
            I1.append(struct.unpack('>h', I1_data_str[m*4+0:m*4+2])[0])
	
	
	#print'Number of phase samples: ', len(phase) #delete this	

        #qdr_values = struct.unpack('>%dh'%(nLongsnapSamples),qdr_data_str)
        #qdr_phase_values = numpy.array(qdr_values)*360./2**16*4/numpy.pi
        
	phase = numpy.array(phase)*360./2**16*4/numpy.pi
	I1 = numpy.array(I1)

        #fqdr = open('ch_out_%d.txt'%ch_we,'w')
        #for q in qdr_phase_values:
        #    fqdr.write(str(q)+'\n')
        #fsnap = open('ch_snap_%d.txt'%ch_we,'w')
        #for q in phase:
        #    fsnap.write(str(q)+'\n')

        self.axes1.clear()
        #self.axes1.plot(phase, '.-', [self.thresholds[ch_we]]*2*L*steps, 'r.', [self.medians[ch_we]]*2*L*steps, 'g.')
        saveDir = str('/home/labuser/Desktop/SDR-master/DataReadout/PhaseData') #saves phase data here
        if saveDir != '':
            phasefilename = saveDir + '/snapshot_'+time.strftime("%Y%m%d-%H%M%S",time.localtime()) + str(self.textbox_roachIP.text())+'.txt'
            numpy.savetxt(phasefilename,phase,fmt='%.8f')                       #saves phase data #changed %e to %f
	    

        med=numpy.median(phase)
        sd = numpy.std(phase) #added to see if shifting LO has any effect on data

        print 'ch:',ch_we,'median:',med, 'standard deviation:', sd
        thresh=self.thresholds[ch_we]

        if self.customThresholds[ch_we] != 360.0:
            thresh=self.customThresholds[ch_we]
            #print "Custom Threshold: ", thresh,

        if steps < 2:
            self.axes1.plot(I1,'bo')
            #self.axes1.plot([thresh+med]*2*numQDRSamples*steps,'r-',[med]*2*numQDRSamples*steps,'g-',alpha=1)
            #med=self.medians[ch_we]
            #self.axes1.plot([thresh+med]*2*numQDRSamples*steps,'y-',[med]*2*numQDRSamples*steps,'y-',alpha=0.2)
	    self.axes1.set_xlabel('Time (us)')
	    self.axes1.set_ylabel('I1')

            #nFFTAverages = 100
            #nSamplesPerFFT = nLongsnapSamples/nFFTAverages
            #noiseFFT = numpy.zeros(nSamplesPerFFT)
            #noiseFFTFreqs = numpy.fft.fftfreq(nSamplesPerFFT)
	    #norm1 = float(self.textbox_normalisation.text()) #This normalisation factor is the input signal to the ADCs, in (Volts [V]). 
            #for iAvg in xrange(nFFTAverages):
            #    noise = numpy.fft.fft(qdr_phase_values[iAvg*nSamplesPerFFT:(iAvg+1)*nSamplesPerFFT])
            #    noise = numpy.abs(noise)
            #    noiseFFT += 20*(numpy.log10(noise/norm1/1e-6))
            #noiseFFT /= nFFTAverages
	    #fnoifreqs = open('ch_noifreqs_%d.txt'%ch_we,'w')
	    #for q in noiseFFTFreqs:
            #	fnoifreqs.write(str(q)+'\n')
	    #fnoise = open('ch_noise_%d.txt'%ch_we,'w')
	    #for q in noiseFFT:
            #	fnoise.write(str(q)+'\n')
            #self.axes0.clear()
            #nFFTfreqs = len(noiseFFTFreqs)
            #noiseFFTFreqs *= 1e6 #convert MHz to Hz
            #self.axes0.semilogx(noiseFFTFreqs[1:nFFTfreqs],noiseFFT[1:nFFTfreqs])
            #self.axes0.set_xlabel('Freq (Hz)')
            #self.axes0.set_ylabel('Phase Noise [dBc/Hz], nAverages=%d'%nFFTAverages)
	    #fnoispec = open('ch_noispec_%d.txt'%ch_we,'w')
	    


        #print "Threshold: ",self.thresholds[ch_we]

        self.canvas.draw()

	#print "I0 data: ", I0

        print "longsnapshot taken"





    def contsnapshot(self): 

	failsafe = 0
	maxloops = int(self.textbox_contsnapLoops.text()) #break if failsafe exceeds this. Stop button currently bugging. 

	

	while self.contsnapStatus == 'off':
       
		time.sleep(0.1) #might stop from becoming unresponsive 
		
        	self.displayResonatorProperties()
        	ch_we = int(self.textbox_channel.text())
        	self.roach.write_int('ch_we', ch_we)
        	#print self.roach.read_int('ch_we')
        
        	steps = int(self.textbox_contsnapSteps.text())
        	L = 2**10
        	numQDRSamples=2**19
        	numBytesPerSample=4
        	nContsnapSamples = numQDRSamples*2*steps # 2 16-bit samples per 32-bit QDR word
        	bin_data_phase = ''

        	qdr_data_str = ''

		IQdata = ''
		I = ''
		Q = ''

        	for n in range(steps):
            		self.roach.write_int('snapPhase_ctrl', 0)
            		self.roach.write_int('snapqdr_ctrl',0)
            		self.roach.write_int('startSnap', 0)
            		self.roach.write_int('snapqdr_ctrl',1)
            		self.roach.write_int('snapPhase_ctrl', 1)
            		self.roach.write_int('startSnap', 1)
            		time.sleep(1)
            		bin_data_phase = bin_data_phase + self.roach.read('snapPhase_bram', 4*L)  
            		qdr_data_str = qdr_data_str + self.roach.read('qdr0_memory',numQDRSamples*numBytesPerSample) #changing this
			

			#trying to save IQ data
			IQdata = IQdata + self.roach.read('avgIQ_bram', 4*2*256) #attempting to save IQ data
	        	I = I + str(struct.unpack('>l', IQdata[4*n:4*n+4])[0]-self.iq_centers[n].real)
                	Q = Q + str(struct.unpack('>l', IQdata[4*(n+256):4*(n+256)+4])[0]-self.iq_centers[n].imag)



		
	        print 'I: ', I 
	        #print 'Q: ', Q



        	self.roach.write_int('snapPhase_ctrl', 0)
        	self.roach.write_int('snapqdr_ctrl',0)
        	self.roach.write_int('startSnap', 0)
        	phase = []
        	for m in range(steps*L):
            		phase.append(struct.unpack('>h', bin_data_phase[m*4+2:m*4+4])[0])
            		phase.append(struct.unpack('>h', bin_data_phase[m*4+0:m*4+2])[0])
	
	
		#print'Number of phase samples: ', len(phase) #delete this	

        	qdr_values = struct.unpack('>%dh'%(nContsnapSamples),qdr_data_str)
        	qdr_phase_values = numpy.array(qdr_values)*360./2**16*4/numpy.pi
        	phase = numpy.array(phase)*360./2**16*4/numpy.pi


		phase_threshold = float(self.textbox_phasethreshold.text())
		#phase_threshold = -20          #using textbox now
		george = 0
		bob = 0 

		#qdr_phase_values = qdr_phase_values - numpy.median(qdr_phase_values)
		median_qdr_phase = numpy.median(qdr_phase_values)	


		while bob < len(qdr_phase_values):		
			#print 'QDR Phase Value: ', qdr_phase_values[bob]

			if bob+1500 > len(qdr_phase_values):
				break




					


			#need to add some extra requirements here to count a pulse
			#see matt strader thesis
			




			if abs(median_qdr_phase - qdr_phase_values[bob]) > phase_threshold:
				#print 'QDR Phase Value: ', qdr_phase_values[bob]
				george = george + 1			
				#saveDir = str('/home/labuser/Desktop/SDR-master/DataReadout/PhaseDataEoin/') #commenting out and adding line below to load saveDir from textbox
				saveDir = str(self.textbox_pulsesavepath.text())

				#if saveDir doesn't already exist, make it 
				if not os.path.exists(saveDir):
					os.makedirs(saveDir)

				pulsefilename = saveDir + 'pulses_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt' #changed to include milliseconds
 
				#saving off binary data to debug 
				qdrfilename = saveDir + 'qdr_'+datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')[:-3] +'.txt'

            			bob_array = [2001]
				bob_array = qdr_phase_values[bob-500:bob+1500]
				
				qdr_bob_array = [2001]
				qdr_bob_array = qdr_values[bob-500:bob+1500]

				numpy.savetxt(pulsefilename,bob_array,fmt='%.8f')                       #saves pulse data #changed %e to %f

				#print 'Binary Data Type: ', type(qdr_data_str)
				#numpy.savetxt(qdrfilename,qdr_bob_array)

				#print'I,Q Centre: ', iq_centers
				print'File saved!', george
				#print'Phase: ', qdr_phase_values[bob]
				#print'Phase Threshold: ', phase_threshold
			
				bob = bob + 1000
			else:
				bob = bob + 1			
				#print'Count= ', bob
		
		#if george == 0:
			#print'No pulses!'  #commented out to speed up process


        	#fqdr = open('ch_out_%d.txt'%ch_we,'w')
        	#for q in qdr_phase_values:
            		#fqdr.write(str(q)+'\n')
        	#fsnap = open('ch_snap_%d.txt'%ch_we,'w')
        	#for q in phase:
            		#fsnap.write(str(q)+'\n')

        	#self.axes1.clear()
        	#self.axes1.plot(phase, '.-', [self.thresholds[ch_we]]*2*L*steps, 'r.', [self.medians[ch_we]]*2*L*steps, 'g.')
        	#saveDir = str('/home/cbracken/Desktop/SDR-master/DataReadout/PhaseData/ContSnapShots') #saves phase data here
        	#if saveDir != '':
            		#phasefilename = saveDir + '/snapshot_'+time.strftime("%Y%m%d-%H%M%S",time.localtime()) + str(self.textbox_roachIP.text())+'.txt'
            		#numpy.savetxt(phasefilename,phase,fmt='%.8f')    #saves phase data, changed %e to %f #changed phase file being saved to 'ch_out_%d.txt'
	    

        	med=numpy.median(phase)
        	sd = numpy.std(phase) #added to see if shifting LO has any effect on data

        	#print 'ch:',ch_we,'median:',med,'standard deviation:', sd
        	thresh=self.thresholds[ch_we]

        	#if self.customThresholds[ch_we] != 360.0:
            		#thresh=self.customThresholds[ch_we]
            		#print "Custom Threshold: ", thresh,

        	#if steps < 2:
            		#self.axes1.plot(qdr_phase_values,'b-')
            		#self.axes1.plot([thresh+med]*2*numQDRSamples*steps,'r-',[med]*2*numQDRSamples*steps,'g-',alpha=1)
            		#med=self.medians[ch_we]
            		#self.axes1.plot([thresh+med]*2*numQDRSamples*steps,'y-',[med]*2*numQDRSamples*steps,'y-',alpha=0.2)
	    		#self.axes1.set_xlabel('Time (us)')
	    		#self.axes1.set_ylabel('Phase (Deg)')

            		#nFFTAverages = 100
            		#nSamplesPerFFT = nContsnapSamples/nFFTAverages
            		#noiseFFT = numpy.zeros(nSamplesPerFFT)
            		#noiseFFTFreqs = numpy.fft.fftfreq(nSamplesPerFFT)
            		#for iAvg in xrange(nFFTAverages):
                		#noise = numpy.fft.fft(qdr_phase_values[iAvg*nSamplesPerFFT:(iAvg+1)*nSamplesPerFFT])
                		#noise = numpy.abs(noise)**2
                		#noiseFFT += noise
            		#noiseFFT /= nFFTAverages
	    		#fnoifreqs = open('ch_noifreqs_%d.txt'%ch_we,'w')
	    		#for q in noiseFFTFreqs:
            			#fnoifreqs.write(str(q)+'\n')
	    		#fnoise = open('ch_noise_%d.txt'%ch_we,'w')
	    		#for q in noiseFFT:
            			#fnoise.write(str(q)+'\n')
            		#self.axes0.clear()
            		#nFFTfreqs = len(noiseFFTFreqs)/2
            		#noiseFFTFreqs *= 1e6 #convert MHz to Hz
            		#self.axes0.loglog(noiseFFTFreqs[1:nFFTfreqs],noiseFFT[1:nFFTfreqs])
            		#self.axes0.set_xlabel('Freq (Hz)')
            		#self.axes0.set_ylabel('FFT of snapshot, nAverages=%d'%nFFTAverages)
	    		#fnoispec = open('ch_noispec_%d.txt'%ch_we,'w')
	    


        	#print "Threshold: ",self.thresholds[ch_we]

        	#self.canvas.draw()
		#print 'longsnapshot taken'
		
		print 'Iteration: ', failsafe
		failsafe = failsafe + 1

		if failsafe > (maxloops - 1):
			#print 'Too many loops.'
			break 
			
        
	print "contsnapshot taken"



    def contsnapstop(self):
	
	if self.contsnapStatus == 'off':
		self.contsnapStatus = 'on'
		 
	else:
		self.contsnapStatus = 'off'

	print'Stop: ', self.contsnapStatus	

	#return stop





    def readPulses(self):
	N_freqs = len(map(float, unicode(self.textedit_DACfreqs.toPlainText()).split()))
        scale_to_degrees = 360./2**12*4/numpy.pi
        channel_count = [0]*256
        p1 = [[] for n in range(256)]
        timestamp = [[] for n in range(256)]
        baseline = [[] for n in range(256)]
        peaks = [[] for n in range(256)]
        seconds = int(self.textbox_seconds.text())
        nStepsPerSec = 10.
        steps = int(seconds*nStepsPerSec)
        self.roach.write_int('startBuffer', 1)
        time.sleep(1)
        for n in range(steps):
            addr0 = self.roach.read_int('pulses_addr')
            time.sleep(1./nStepsPerSec)
            addr1 = self.roach.read_int('pulses_addr')
            bin_data_0 = self.roach.read('pulses_bram0', 4*2**14)
            bin_data_1 = self.roach.read('pulses_bram1', 4*2**14)

            if addr1 >= addr0:
                total_counts = addr1-addr0
                for n in range(addr0, addr1):
                    raw_data_1 = struct.unpack('>L', bin_data_1[n*4:n*4+4])[0]
                    raw_data_0 = struct.unpack('>L', bin_data_0[n*4:n*4+4])[0]
                    ch = raw_data_1/2**24
                    channel_count[ch] = channel_count[ch] + 1
                    timestamp[ch].append(raw_data_0%2**20)
                    baseline[ch].append((raw_data_0>>20)%2**12)
                    peaks[ch].append((raw_data_1>>12)%2**12)

            else:
                total_counts = addr1+2**14-addr0
                for n in range(addr0, 2**14):
                    raw_data_1 = struct.unpack('>L', bin_data_1[n*4:n*4+4])[0]
                    raw_data_0 = struct.unpack('>L', bin_data_0[n*4:n*4+4])[0]
                    ch = raw_data_1/2**24
                    channel_count[ch] = channel_count[ch] + 1
                    p1[ch].append((raw_data_1%2**12 - 2**11)*scale_to_degrees)
                    timestamp[ch].append(raw_data_0%2**20)
                    baseline[ch].append((raw_data_0>>20)%2**12)
                    peaks[ch].append((raw_data_1>>12)%2**12)
                for n in range(0, addr1):
                    raw_data_1 = struct.unpack('>L', bin_data_1[n*4:n*4+4])[0]
                    raw_data_0 = struct.unpack('>L', bin_data_0[n*4:n*4+4])[0]
                    ch = raw_data_1/2**24
                    channel_count[ch] = channel_count[ch] + 1
                    p1[ch].append((raw_data_1%2**12 - 2**11)*scale_to_degrees)
                    timestamp[ch].append(raw_data_0%2**20)
                    baseline[ch].append((raw_data_0>>20)%2**12)
                    peaks[ch].append((raw_data_1>>12)%2**12)
            print total_counts
        self.roach.write_int('startBuffer', 0)

        print 'sorted indices by counts', numpy.argsort(channel_count)[::-1]
        print 'sorted by counts', numpy.sort(channel_count)[::-1]
        print 'total counts by channel: ',channel_count
        channel_count = numpy.array(channel_count)
        ch = int(self.textbox_channel.text())

        #numpy.savetxt('/home/sean/data/restest/test.dat', p1[ch])
        
        # With lamp off, run "readPulses."  If count rate is above 50, it's anamolous 
        # and it's FIR should be set to 0.
        #for n in range(256):
         #   if channel_count[n] > 100:
          #      self.zeroChannels[n] = 1   
        
        #x = numpy.arange(-270, 0, 3)
        #y = numpy.histogram(data, 90)
        base = numpy.array(baseline[ch],dtype='float')
        base = base/2.0**9-4.0
        base = base*180.0/numpy.pi
        times = numpy.array(timestamp[ch],dtype='float')/1e6
	timesCh = times/1
        peaksCh = numpy.array(peaks[ch],dtype = 'float')
        peaksCh = peaksCh/2.0**9-4.0
        peaksCh = peaksCh*180.0/numpy.pi
        peaksSubBase = peaksCh-basedf
        print 'count rate:',len(base)
        print 'mean baseline:',numpy.mean(base)
        print 'median baseline:',numpy.median(base) 
        print 'stddev baseline:',numpy.std(base)
        self.axes0.clear()
        #self.axes0.plot(timestamp[ch], '.')
        self.axes0.plot(times,base, 'g.')
        self.axes0.plot(times,peaksCh, 'b.')
        self.axes0.plot(times,peaksSubBase, 'r.')
        labels = self.axes0.get_xticklabels()
        for label in labels:
            label.set_rotation(-90)
        self.axes0.set_title("ch=%d b: peak  g:base  r: peak-base"%ch)
        self.axes0.set_xlabel("time within second (sec)")

        self.axes1.clear()
        baseMean = numpy.mean(base)
        baseStd = numpy.std(base)
        peakMean = numpy.mean(peaksCh)
        peakStd = numpy.std(peaksCh)
        psbMean = numpy.mean(peaksSubBase)
        psbStd = numpy.std(peaksSubBase)
        hTitle = "p:%.1f(%.1f) b:%.1f(%.1f) p-b:%.1f(%.1f)"%(peakMean,peakStd,baseMean,baseStd,psbMean,psbStd)
        print "hTitle=",hTitle
        r = (-150,10)
        nBin=40
        hgBase,bins = numpy.histogram(base,nBin,range=r, density=False)
        hgPeak,bins = numpy.histogram(peaksCh,nBin,range=r, density=False)
        hgPeakSubBase,bins = numpy.histogram(peaksSubBase,nBin,range=r, density=False)

        width = 0.7*(bins[1]-bins[0])
        center = (bins[:-1]+bins[1:])/2
        self.axes1.bar(center, hgBase, width, alpha=0.5, linewidth=0, color='g')
        self.axes1.bar(center, hgPeak, width, alpha=0.5, linewidth=0, color='b')
        self.axes1.bar(center, hgPeakSubBase, width, alpha=0.5, linewidth=0, color='r')
        self.axes1.set_xlabel("peak phase (degrees)")
        self.axes1.set_title(hTitle)
	saveDir = str('/home/labuser/Desktop/SDR-master/DataReadout/NewData/') #saves phase data here
        if saveDir != '':
            phasefilename1 = saveDir + 'Pulse_histogram_'+time.strftime("%Y%m%d-%H%M%S",time.localtime())+'.txt'
	    phasefilename2 = saveDir + 'Pulse_times_'+time.strftime("%Y%m%d-%H%M%S",time.localtime())+'.txt'
            numpy.savetxt(phasefilename1,peaksCh,fmt='%.8e')
	    numpy.savetxt(phasefilename2,timesCh,fmt='%.8e')


        self.canvas.draw()
    def channelInc(self):
        ch_we = int(self.textbox_channel.text())
        ch_we = ch_we + 1
        if ch_we >=self.numFreqs:
            ch_we=0
        self.textbox_channel.setText(str(ch_we))
        
    def toggleDAC(self):
        if self.dacStatus == 'off':
            print "Starting LUT...",
            self.roach.write_int('startDAC', 1)
            time.sleep(1)
            while self.roach.read_int('DRAM_LUT_rd_valid') != 0:
                self.roach.write_int('startDAC', 0)
                time.sleep(0.25)
                self.roach.write_int('startDAC', 1)
                time.sleep(1)
                print ".",
            print "done."
            #self.button_startDAC.setText('Stop DAC')
            self.dacStatus = 'on'
            self.status_text.setText('DAC turned on. ')       
        else:
            self.roach.write_int('startDAC', 0)
            #self.button_startDAC.setText('Start DAC')
            self.dacStatus = 'off'
        self.status_text.setText('DAC turned off. ')       

    def loadIQcenters(self):
        for ch in range(256):
            I_c = int(self.iq_centers[ch].real/2**3)
            Q_c = int(self.iq_centers[ch].imag/2**3)

            center = (I_c<<16) + (Q_c<<0)
            self.roach.write_int('conv_phase_centers', center)
            self.roach.write_int('conv_phase_load_centers', (ch<<1)+(1<<0))
            self.roach.write_int('conv_phase_load_centers', 0)

    def select_bins(self, readout_freqs):
        fft_len = 2**9
        bins = ''
        i = 0
        residuals = []
        for f in readout_freqs:
            fft_bin = int(round(f*fft_len/self.sampleRate))
            fft_freq = fft_bin*self.sampleRate/fft_len
            freq_residual = round((f - fft_freq)/self.freqRes)*self.freqRes
            residuals.append(freq_residual)
            bins = bins + struct.pack('>l', fft_bin)
            self.roach.write_int('bins', fft_bin)
            self.roach.write_int('load_bins', (i<<1) + (1<<0))
            self.roach.write_int('load_bins', (i<<1) + (0<<0))
            i = i + 1
        self.status_text.setText('done writing LUTs. ')
        return residuals
  
    def loadLUTs(self):
        self.scale_factor = 1.
        self.iq_centers = numpy.array([0.+0j]*256)
        
        # Loads the DAC and DDS LUTs from file.  As well as the IQ loop centers.
        if self.dacStatus == 'off':
            self.roach.write_int('startDAC', 0)
        else:
            self.toggleDAC()

        saveDir = str(self.textbox_lutDir.text())
        #saveDir = str(os.environ['PWD'] + '/'+ self.textbox_lutDir.text())            
        f = open(saveDir+'luts.dat', 'r')
        binaryData = f.read()

        self.roach.write('dram_memory', binaryData)

        x = numpy.loadtxt(saveDir+'centers.dat')
        N_freqs = len(x[:,0])
        for n in range(N_freqs):
            self.iq_centers[n] = complex(x[n,0], x[n,1])
        
        #    Select and write bins for first stage of channelizer.
        freqs = map(float, unicode(self.textedit_DACfreqs.toPlainText()).split())
        f_base = float(self.textbox_loFreq.text())
        for n in range(len(freqs)):
            if freqs[n] < f_base:
                freqs[n] = freqs[n] + 512e6
        freqs_dds = [0 for j in range(256)]
        for n in range(len(freqs)):
            freqs_dds[n] = round((freqs[n]-f_base)/self.freqRes)*self.freqRes
        freq_residuals = self.select_bins(freqs_dds)
        
        print 'LUTs and IQ centers loaded from file.'
        self.loadIQcenters()
        self.toggleDAC()
   
    def importFreqs(self):
        freqFile =str(self.textbox_freqFile.text())
        self.loadCustomAtten()
        try:
            x = numpy.loadtxt(freqFile) 
            x_string = ''
            for i in range(len(self.customResonators)):
                if self.customResonators[i][1]!=-1:
                    x[i+1,0]=self.customResonators[i][0]
                    x[i+1,3]=self.customResonators[i][1]
        
            self.previous_scale_factor = x[0,0] 
            N_freqs = len(x[1:,0])
            self.numFreqs=N_freqs
            for l in x[1:,0]:
                x_string = x_string + str(l*1e9) + '\n'
            
            self.iq_centers = numpy.array([0.+0j]*256)
            for n in range(N_freqs):
                #for n in range(256):
                self.iq_centers[n] = complex(x[n+1,1], x[n+1,2])
            
            self.attens = x[1:,3]
            self.textedit_DACfreqs.setText(x_string)
            self.findDeletedResonators()
            print 'Freq/Atten loaded from',freqFile
            self.status_text.setText('Freq/Atten loaded')
            
            self.loadCustomThresholds()
        except IOError:
            print 'No such file or directory:',freqFile
            self.status_text.setText('IOError')

    def findDeletedResonators(self):
        for i in range(len(self.customResonators)):
            if self.customResonators[i][1] >=99:
                self.zeroChannels[i] = 1
            else:
                self.zeroChannels[i] = 0 #needed so you can undelete resonators

    def loadCustomAtten(self):
        freqFile =str(self.textbox_freqFile.text())
        newFreqFile = freqFile[:-4] + '_NEW.txt'
        try:
            y=numpy.loadtxt(newFreqFile)
            self.customResonators=numpy.array([[0.0,-1]]*256)
            if type(y[0]) == numpy.ndarray:
                for arr in y:
                    self.customResonators[int(arr[0])]=arr[1:3]
            else:
                self.customResonators[int(y[0])]=y[1:3]
            print 'Loaded custom resonator freq/atten from',newFreqFile
        except IOError:
            pass

    def displayResonatorProperties(self):
        ch=int(self.textbox_channel.text())
        freqFile =str(self.textbox_freqFile.text())
        x = numpy.loadtxt(freqFile)
        #self.loadCustomAtten()
        for i in range(len(self.customResonators)):
            if self.customResonators[i][1]!=-1:
                x[i+1,0]=self.customResonators[i][0]
                x[i+1,3]=self.customResonators[i][1]
        
        #print 'atten: '+str(x[ch,3])
        self.label_attenuation.setText('attenuation: ' + str(int(x[ch+1,3])))
        self.label_frequency.setText('freq (GHz): ' + str(float(x[ch+1,0])))
        self.label_median.setText('median: '+str(self.medians[ch]))
        if self.customThresholds[ch] != 360.0:
            self.label_threshold.setText('threshold: '+str(self.customThresholds[ch]))
        else:
            self.label_threshold.setText('threshold: '+str(self.thresholds[ch]))

        
    def importFIRcoeffs(self):
        coeffsFile =str(self.textbox_coeffsFile.text())
        self.fir = numpy.loadtxt(coeffsFile)
        print self.fir
  
    def file_dialog(self):
        print 'add dialog box here'
        #self.newdatadir = QFileDialog.getExistingDirectory(self, str("Choose SaveDirectory"), "",QFileDialog.ShowDirsOnly)
         #if len(self.newdatadir) > 0:
          #   self.datadir = self.newdatadir
           #  print self.datadir
             #self.ui.data_directory_lineEdit.setText(self.datadir) #put new path name in line edit
            # self.button_saveDir.setText(str(self.datadir))
             
    def create_main_frame(self):
        self.main_frame = QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        self.dpi = 100
        self.fig = Figure((9.0, 5.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes0 = self.fig.add_subplot(121)
        self.axes1 = self.fig.add_subplot(122)
        cid=self.canvas.mpl_connect('button_press_event', self.setCustomThreshold)
        
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Roach board's IP address
        self.textbox_roachIP = QLineEdit('192.168.4.%d'%roachNum)
        self.textbox_roachIP.setMaximumWidth(200)
        label_roachIP = QLabel('Roach IP Address:')

        # Start connection to roach.
        self.button_openClient = QPushButton("(1)Open Client")
        self.button_openClient.setMaximumWidth(100)
        self.connect(self.button_openClient, SIGNAL('clicked()'), self.openClient)
        
        # DAC Frequencies.
        self.textedit_DACfreqs = QTextEdit()
	self.textedit_DACfreqs.setMinimumWidth(150) #added this, box was appearing too small
        self.textedit_DACfreqs.setMaximumWidth(170) #changed from 170 to 200
        self.textedit_DACfreqs.setMaximumHeight(100)
        label_DACfreqs = QLabel('DAC Freqs:')
    
        # File with frequencies/attens
        self.textbox_freqFile = QLineEdit('/home/labuser/MKIDS/MKIDS_SDR/DataReadout/ChannelizerControls/LUT/1tones.txt') #changed file 
        self.textbox_freqFile.setMaximumWidth(200) 

        # Import freqs from file.
        self.button_importFreqs = QPushButton("(2)Load freqs")
        self.button_importFreqs.setMaximumWidth(200)
        self.connect(self.button_importFreqs, SIGNAL('clicked()'), self.importFreqs)   

        # File with FIR coefficients
        self.textbox_coeffsFile = QLineEdit('/home/labuser/Desktop/SDR-master/DataReadout/ChannelizerControls/LUT/BlackmanFilter_250kHz.txt')
        self.textbox_coeffsFile.setMaximumWidth(200)

        # Import FIR coefficients from file.
        self.button_importFIRcoeffs = QPushButton("(3)Import FIR coeffs.")
        self.button_importFIRcoeffs.setMaximumWidth(200)
        self.connect(self.button_importFIRcoeffs, SIGNAL('clicked()'), self.importFIRcoeffs) 

        # Channel increment by 1.
        self.button_channelInc = QPushButton("Channel++")
        self.button_channelInc.setMaximumWidth(100)
        self.connect(self.button_channelInc, SIGNAL('clicked()'), self.channelInc)

        # Load FIR coefficients.
        self.button_loadFIRcoeffs = QPushButton("(4)Load FIR")
        self.button_loadFIRcoeffs.setMaximumWidth(170)
        self.connect(self.button_loadFIRcoeffs, SIGNAL('clicked()'), self.loadFIRcoeffs)

        # Load thresholds.
        self.button_loadThresholds = QPushButton("(5)Load thresholds")
        self.button_loadThresholds.setMaximumWidth(170)
        self.connect(self.button_loadThresholds, SIGNAL('clicked()'), self.loadThresholds)

	# File with save path for pulses
	
	#getdate
	default_save_path = '/home/labuser/Data/' + datetime.utcnow().strftime('%Y') + '/' + datetime.utcnow().strftime('%Y_%m_%d') + '/'

        self.textbox_pulsesavepath = QLineEdit(default_save_path) #changed file 
        self.textbox_pulsesavepath.setMaximumWidth(200) 
	label_pulsesavepath = QLabel('Phase Data Save Path')

        # remove custom threshold button
        self.button_rmCustomThreshold = QPushButton("Remove custom threshold")
        self.button_rmCustomThreshold.setMaximumWidth(200) #changed from 170
        self.connect(self.button_rmCustomThreshold, SIGNAL('clicked()'), self.rmCustomThreshold)
        
        # Channel to measure
        self.textbox_channel = QLineEdit('0')
        self.textbox_channel.setMaximumWidth(50)

        # threshold N*sigma
        self.textbox_Nsigma = QLineEdit('2.5')
        self.textbox_Nsigma.setMaximumWidth(50)
        label_Nsigma = QLabel('Sigma       ')

	# phase threshold - new 
        self.textbox_phasethreshold = QLineEdit('10')
        self.textbox_phasethreshold.setMaximumWidth(50)
        label_phasethreshold = QLabel('[Deg.] Phase Threshold for Pulse Data')
        
        # Time snapshot of a single channel
        self.button_snapshot = QPushButton("Snapshot (BRAM)")
        self.button_snapshot.setMaximumWidth(170)
        self.connect(self.button_snapshot, SIGNAL('clicked()'), self.snapshot)            

        # Long time snapshot of a single channel
        self.button_longsnapshot = QPushButton("Long Snapshot (QDR)")
        self.button_longsnapshot.setMaximumWidth(170)
        self.connect(self.button_longsnapshot, SIGNAL('clicked()'), self.longsnapshot)            
        
	# Continuous time snapshot of a single channel
        self.button_contsnapshot = QPushButton("Record Pulse Data (SW)")
        self.button_contsnapshot.setMaximumWidth(170)
        self.connect(self.button_contsnapshot, SIGNAL('clicked()'), self.contsnapshot)            
        
	# Stop button to stop continuous time snapshot
	self.button_contsnapstop = QPushButton("Stop Pulse Data")
        self.button_contsnapstop.setMaximumWidth(170)
        self.connect(self.button_contsnapstop, SIGNAL('clicked()'), self.contsnapstop)            
        
        # Read pulses
        self.button_readPulses = QPushButton("Read Pulses Heights (HW)")
        self.button_readPulses.setMaximumWidth(205)
        self.connect(self.button_readPulses, SIGNAL('clicked()'), self.readPulses)
        
        # Seconds for "read pulses."
        self.textbox_seconds = QLineEdit('1')
        self.textbox_seconds.setMaximumWidth(50)
	label_seconds = QLabel('* 1 sec')
        
        # lengths of 2 ms for defining thresholds.
        self.textbox_timeLengths = QLineEdit('10')
        self.textbox_timeLengths.setMaximumWidth(50)
        label_timeLengths = QLabel('* 2 msec       ')


        # lengths of 2 ms steps to combine in a snapshot.
        self.textbox_snapSteps = QLineEdit('10')
        self.textbox_snapSteps.setMaximumWidth(50)
        label_snapSteps = QLabel('* 2 msec')

	# normalisation for noise measurements. This is the signal voltage (in micro Volts [uV]) that is input to each of the ADCs.
        self.textbox_normalisation = QLineEdit('50')
        self.textbox_normalisation.setMaximumWidth(50)
        label_normalisation = QLabel('Normalisation [uV] (ADC signal)')

        # lengths of 2 ms steps to combine in a snapshot.
        self.textbox_longsnapSteps = QLineEdit('1')
        self.textbox_longsnapSteps.setMaximumWidth(50)
        label_longsnapSteps = QLabel('* sec')


        # lengths of 1 s steps to combine in a series of snapshots.
        self.textbox_contsnapSteps = QLineEdit('1')
        self.textbox_contsnapSteps.setMaximumWidth(50)
        label_contsnapSteps = QLabel('* sec')

	# number of loops in a continuous snapshot.
        self.textbox_contsnapLoops = QLineEdit('1')
        self.textbox_contsnapLoops.setMaximumWidth(50)
        label_contsnapLoops = QLabel('Iterations')


        #median
        self.label_median = QLabel('median: 0.0000')
        self.label_median.setMaximumWidth(170)

        #threshold
        self.label_threshold = QLabel('threshold: 0.0000')
        self.label_threshold.setMaximumWidth(170)

        #attenuation
        self.label_attenuation = QLabel('attenuation: 0')
        self.label_attenuation.setMaximumWidth(170)

        #frequency
        self.label_frequency = QLabel('freq (GHz): 0.0000')
        self.label_frequency.setMaximumWidth(170)
        
        # Add widgets to window.
        gbox0 = QVBoxLayout()
        hbox00 = QHBoxLayout()
        hbox00.addWidget(self.textbox_roachIP)
        hbox00.addWidget(self.button_openClient)
        gbox0.addLayout(hbox00)
        hbox01 = QHBoxLayout()
        hbox01.addWidget(self.textbox_freqFile)
        hbox01.addWidget(self.button_importFreqs)
        gbox0.addLayout(hbox01)
        hbox02 = QHBoxLayout()
        hbox02.addWidget(self.textbox_coeffsFile)
        hbox02.addWidget(self.button_importFIRcoeffs)
        hbox02.addWidget(self.button_loadFIRcoeffs)
        gbox0.addLayout(hbox02)
        hbox03 = QHBoxLayout()
        hbox03.addWidget(self.textbox_timeLengths)
        hbox03.addWidget(label_timeLengths)
        hbox03.addWidget(self.textbox_Nsigma)
        hbox03.addWidget(label_Nsigma)
        hbox03.addWidget(self.button_loadThresholds)
        gbox0.addLayout(hbox03)
        
        gbox1 = QVBoxLayout()
        gbox1.addWidget(label_DACfreqs)
        gbox1.addWidget(self.textedit_DACfreqs)

        gbox2 = QVBoxLayout()
        hbox20 = QHBoxLayout()
        hbox20.addWidget(self.textbox_channel)
        hbox20.addWidget(self.button_channelInc)
        gbox2.addLayout(hbox20)
	hbox221 = QHBoxLayout()
        hbox221.addWidget(self.textbox_normalisation)
	hbox221.addWidget(label_normalisation)
        gbox2.addLayout(hbox221)
        hbox21 = QHBoxLayout()
        hbox21.addWidget(self.button_snapshot)
        hbox21.addWidget(self.textbox_snapSteps)
        hbox21.addWidget(label_snapSteps)
        gbox2.addLayout(hbox21)
        hbox22 = QHBoxLayout()
        hbox22.addWidget(self.button_longsnapshot)
        hbox22.addWidget(self.textbox_longsnapSteps)
        hbox22.addWidget(label_longsnapSteps)
        gbox2.addLayout(hbox22)
        gbox2.addWidget(self.button_rmCustomThreshold)
        hbox23 = QHBoxLayout()
        hbox23.addWidget(self.button_readPulses)
	hbox23.addWidget(self.textbox_seconds)
	hbox23.addWidget(label_seconds)
        gbox2.addLayout(hbox23)

        gbox3 = QVBoxLayout()
        gbox3.addWidget(self.label_median)
        gbox3.addWidget(self.label_threshold)
        gbox3.addWidget(self.label_attenuation)
        gbox3.addWidget(self.label_frequency)

	hbox25 = QHBoxLayout()
        hbox25.addWidget(self.textbox_phasethreshold) #sets phase threshold
        hbox25.addWidget(label_phasethreshold)
        
	gbox3.addLayout(hbox25)

	
	hbox24 = QHBoxLayout()
        hbox24.addWidget(self.button_contsnapshot)
        hbox24.addWidget(self.textbox_contsnapSteps)
        hbox24.addWidget(label_contsnapSteps)
        hbox24.addWidget(self.textbox_contsnapLoops) #to control number of loops in continuous shot
        hbox24.addWidget(label_contsnapLoops)
        
	hbox26 = QHBoxLayout()
	hbox26.addWidget(self.textbox_pulsesavepath) #adding text box to input save path
	hbox26.addWidget(label_pulsesavepath)
        gbox0.addLayout(hbox26)
        	

	gbox3.addLayout(hbox24)
        
	hbox24 = QHBoxLayout()
        hbox24.addWidget(self.button_contsnapstop)
        gbox3.addLayout(hbox24)
        

        hbox = QHBoxLayout()
        hbox.addLayout(gbox0)
        hbox.addLayout(gbox1)     
        hbox.addLayout(gbox2)
        hbox.addLayout(gbox3)
	
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
  
    def create_status_bar(self):
        self.status_text = QLabel("Awaiting orders.")
        self.statusBar().addWidget(self.status_text, 1)
        
    def create_menu(self):        
        self.file_menu = self.menuBar().addMenu("&File")
        
        load_file_action = self.create_action("&Save plot",shortcut="Ctrl+S", slot=self.save_plot, tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close, shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, (load_file_action, None, quit_action))
        
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", shortcut='F1', slot=self.on_about, tip='About the demo')
        
        self.add_actions(self.help_menu, (about_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"
        path = unicode(QFileDialog.getSaveFileName(self, 'Save file', '',file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    
    def on_about(self):
        msg = """ Message to user goes here.
        """
        QMessageBox.about(self, "MKID-ROACH software demo", msg.strip())
   



def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__=='__main__':
    if len(sys.argv)!= 2:
        print 'Usage: ',sys.argv[0],' roachNum'
        exit(1)
    roachNum = int(sys.argv[1])
    datadir = '/opt/software/colin1/LUT/freqTest.txt'
    main()

