import sys, os, random, math, array, fractions

#from PyQt4.QtCore import *  #using import * was casuing errors with hex() function   
#from PyQt4.QtGui import *
import PyQt4.QtCore as QtC   #instead, had to import PyQt4 like this 
import PyQt4.QtGui as QtG    ##later had to add QtC. or QtG. before certain functions e.g. line 52

from PyQt4 import QtGui
import socket
import matplotlib, corr, time, struct, numpy 
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from tables import *
from lib import iqsweep


#Things to update:
#DONE...make filename_NEW.txt only hold information for channel that is changed
#DONE...delete resonator (change FIR?)
#click to change freq
#custom set center



if __name__ == '__main__':
    if len(sys.argv) != 2:
	#print len(sys.argv) 
	#print sys.argv[0] 
	print 'Usage: ',sys.argv[0],' roachNo'
        exit(1)
    roachNo = int(sys.argv[1])
    #datadir = os.environ['MKID_FREQ_PATH']#'/opt/software/colin1/'
   # print datadir
    #configFile = numpy.loadtxt(os.path.join(datadir,'roachConfig.txt'))
   # configFile = numpy.reshape(configFile,(-1,2))
    #try:
        #scaleFactorFile = numpy.loadtxt(os.path.join(datadir,'scaleFactors.txt'))
        #defaultScale = float(scaleFactorFile[:,1][roachNo])
    #except:
        #defaultScale = 10.
    #defaultLOFreqs = configFile[:,0]
    #defaultAttens = configFile[:,1]
    #defaultLOFreq = defaultLOFreqs[roachNo]
   #defaultAtten = int(defaultAttens[roachNo])

	
    MAX_ATTEN = 99

class AppForm(QtG.QMainWindow):
    def __init__(self, parent=None):
        QtG.QMainWindow.__init__(self, parent)           #added QtG. before QMainWindow
        self.setWindowTitle('DIAS_MKID_Readout_1_0')
	label = QtGui.QLabel('DIAS', self)
	label.setFont(QtG.QFont('Arial', 20))
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        self.dacStatus = 'off'
        self.dramStatus = 'off'
        self.tapStatus = 'off'
        self.socketStatus = 'off'
        self.ch_all = []
        self.attens = numpy.array([1. for i in range(256)])
        #self.freqRes = 1953.125
        #self.freqRes = 7812.5
        self.sampleRate = 512e6
        N_lut_entries = 2**16
        self.freqRes = self.sampleRate/N_lut_entries
        #self.iq_centers = numpy.array([0.+0j]*256)
        self.customResonators=numpy.array([[0.0,-1]]*256)	#customResonator[ch]=[freq,atten]
        self.last_I_on_res = None
        self.last_Q_on_res = None
        self.last_I = None
        self.last_Q = None
        self.last_iq_centers = None
        self.last_IQ_vels = None
        self.last_f_span = None
        self.I = None
        self.Q = None
        self.I_on_res = None
        self.Q_on_res = None
        self.iq_centers = None
        self.IQ_vels = None
        self.f_span = None
        self.last_scale_factor = None

        
    def openClient(self):
        self.status_text.setText('connecting...')
        #self.QApplication.processEvents()
        print 'connecting...'
        self.roach = corr.katcp_wrapper.FpgaClient(self.textbox_roachIP.text(),7147)
	self.roach.progdev('chan_512_2012_Jul_30_1754.bof') 

	#Original boffile: 'chan_512_2012_Jul_30_1754.bof'  
	#Last working: chan_snap_v3_2012_Oct_30_1216.bof
        #trying chan_snap_v4_20_12_2018_May_29_1235.bof and chan_snap_v4_20_12_2018_Jun_07_1106.bof
	#chan_snap_eb_02_08_2018_Aug_02_1545.bof also works.
	#changed back to chan_snap_v3_2012_Oct_30_1216.bof

 

        time.sleep(2)
        self.status_text.setText('connection established')
        print 'connection established to',self.textbox_roachIP.text()
        self.button_openClient.setDisabled(True)


    def create_main_frame(self):
        self.main_frame = QtG.QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        self.dpi = 100
        self.fig = Figure((9.0, 10.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes0 = self.fig.add_subplot(221)
        self.axes1 = self.fig.add_subplot(222)
	self.axes2 = self.fig.add_subplot(223)
        self.axes3 = self.fig.add_subplot(224)
        
        cid=self.canvas.mpl_connect('button_press_event', self.changeCenter)
        
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Roach board's IP address
        roachIP = roachNo
#        if roachNo == 6:
#            roachIP = 7
#        elif roachNo == 7:
#            roachIP = 6
        self.textbox_roachIP = QtG.QLineEdit('192.168.4.10')
        self.textbox_roachIP.setMaximumWidth(200)
        label_roachIP = QtG.QLabel('Roach IP Address:')

        # Start connection to roach.
        self.button_openClient = QtG.QPushButton("(1)Open Client")
        self.button_openClient.setMaximumWidth(100)
        self.connect(self.button_openClient, QtC.SIGNAL('clicked()'), self.openClient)
        
        
        # Add widgets to window.
        gbox0 = QtG.QVBoxLayout()
        hbox00 = QtG.QHBoxLayout()
        hbox00.addWidget(self.textbox_roachIP)
        hbox00.addWidget(self.button_openClient)
        gbox0.addLayout(hbox00)
        hbox01 = QtG.QHBoxLayout()
        hbox01.addWidget(self.textbox_freqFile)
        hbox01.addWidget(self.button_loadFreqsAttens)
        gbox0.addLayout(hbox01)
        hbox02 = QtG.QHBoxLayout()
        hbox02.addWidget(label_saveDir)
        hbox02.addWidget(self.textbox_saveDir)
        gbox0.addLayout(hbox02)
        hbox03 = QtG.QHBoxLayout()
        hbox03.addWidget(label_loFreq)
        hbox03.addWidget(self.textbox_loFreq)
        gbox0.addLayout(hbox03)
        hbox04 = QtG.QHBoxLayout()
        hbox04.addWidget(label_freqOffset)
        hbox04.addWidget(self.textbox_freqOffset)
        gbox0.addLayout(hbox04)

        gbox1 = QtG.QVBoxLayout()
        gbox1.addWidget(label_DACfreqs)
        gbox1.addWidget(self.textedit_DACfreqs)
        hbox10 = QtG.QHBoxLayout()
        hbox10.addWidget(label_offset)
        hbox10.addWidget(self.textbox_offset)
        hbox11 = QtG.QHBoxLayout()
        #hbox11.addWidget(label_dds_shift)
        #hbox11.addWidget(self.textbox_dds_shift)
        gbox1.addLayout(hbox10)
        gbox1.addLayout(hbox11)
        gbox1.addWidget(self.cbox_keepScaleFactor)
        hbox111 = QtG.QHBoxLayout()
        hbox111.addWidget(self.cbox_useScaleFactor)
        hbox111.addWidget(self.textbox_customScale)
        gbox1.addLayout(hbox111)
        gbox1.addWidget(self.button_define_LUTs)
        #gbox1.addWidget(self.button_startDAC)
        hbox12 = QtG.QHBoxLayout()
        hbox12.addWidget(self.button_startDAC)
        hbox12.addWidget(self.square_DACindicate)
        gbox1.addLayout(hbox12)

        gbox2 = QtG.QVBoxLayout()
        hbox20 = QtG.QHBoxLayout()
        hbox20.addWidget(label_atten_in)
        hbox20.addWidget(self.textbox_atten_in)
        hbox20.addWidget(label_powerSweepStart)
        hbox20.addWidget(self.textbox_powerSweepStart)
        hbox20.addWidget(label_powerSweepStop)
        hbox20.addWidget(self.textbox_powerSweepStop)
        gbox2.addLayout(hbox20)
        hbox21 = QtG.QHBoxLayout()
        hbox21.addWidget(label_loSpan)
        hbox21.addWidget(self.textbox_loSpan)
        hbox21.addWidget(self.button_sweepLO)
        hbox21.addWidget(self.button_showPrevious)
        gbox2.addLayout(hbox21)
        hbox22 = QtG.QHBoxLayout()
        hbox22.addWidget(label_channel)
        hbox22.addWidget(self.textbox_channel)
        hbox22.addWidget(self.button_channelIncDown)
        hbox22.addWidget(self.button_channelIncUp)
        gbox2.addLayout(hbox22)
        hbox23 = QtG.QHBoxLayout()
        hbox23.addWidget(label_attenuation)
        hbox23.addWidget(self.spinbox_attenuation)
        hbox23.addWidget(label_freq)
        hbox23.addWidget(self.textbox_freq)
        hbox23.addWidget(self.button_updateResonator)
        hbox23.addWidget(self.button_autoFreq)
        hbox23.addWidget(self.button_deleteResonator)
        gbox2.addLayout(hbox23)
        hbox24 = QtG.QHBoxLayout()
        hbox24.addWidget(label_freqAutoLimit)
        hbox24.addWidget(self.textbox_freqAutoLimit)
        hbox24.addWidget(self.button_autoFreqs)
        gbox2.addLayout(hbox24)
        hbox25 = QtG.QHBoxLayout()
        hbox25.addWidget(self.button_rotateLoops)
        hbox25.addWidget(self.button_translateLoops)
        gbox2.addLayout(hbox25)
 
        hbox = QtG.QHBoxLayout()
        hbox.addLayout(gbox0)
        hbox.addLayout(gbox1)     
        hbox.addLayout(gbox2)
        
        vbox = QtG.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)


 



def main():
    app = QtG.QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()

