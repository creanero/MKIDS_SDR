import sys, os, random, math, array, fractions
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
import socket
import matplotlib, corr, time, struct, numpy
from matplotlib.backends.backend_qt4 import FigureCanvasQT as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from tables import *
from lib import iqsweep

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: ',sys.argv[0],' roachNo'
        exit(1)
    roachNo = int(sys.argv[1])

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('DIAS_MKID_Readout_2_0')
	label = QtGui.QLabel('DIAS', self)
	label.setFont(QFont('Arial', 20))
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
        N_lut_entries = 2**9
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
	self.roach.progdev('chan_snap_v3_2012_Oct_30_1216.bof')
        time.sleep(2)
        self.status_text.setText('connection established')
        print 'connection established to',self.textbox_roachIP.text()
        self.button_openClient.setDisabled(True)

    def programRFswitches(self, regStr = '10110'):
        #    5 bit word: LO_int/ext, RF_loop, LO_source(doubler), BB_loop, Ck_int/ext
        #regStr = self.textbox_rfSwReg.text()
        print int(regStr[0]), int(regStr[1]), int(regStr[2]),int(regStr[3]), int(regStr[4])

        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('if_switch', 1)
        
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[0])<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[0])<<2)+(1<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[0])<<2)+(0<<1)+(0<<0))
        
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[1])<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[1])<<2)+(1<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[1])<<2)+(0<<1)+(0<<0))                
        
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[2])<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[2])<<2)+(1<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[2])<<2)+(0<<1)+(0<<0))
        
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[3])<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[3])<<2)+(1<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[3])<<2)+(0<<1)+(0<<0))
        
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[4])<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[4])<<2)+(1<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(int(regStr[4])<<2)+(0<<1)+(0<<0))   

        # Now clock out the data written to the reg.
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(1<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(1<<0))   
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(1<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))                        
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(1<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(1<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(1<<0))
        self.roach.write_int('regs', (1<<4)+(1<<3)+(0<<2)+(0<<1)+(0<<0))
        self.roach.write_int('if_switch', 0)
        
    def programAttenuators(self, atten_in_desired, atten_out_desired):
        #    There are eight settings for each attenuator:
        #    0db, -0.5, -1, -2, -4, -8, -16, and -31.5, which
        #    are listed in order in "attenuations."    
        #atten_in_desired = float(self.textbox_atten_in.text())
        atten_in = 63 - int(atten_in_desired*2)
        
        #atten_out_desired = float(self.textbox_atten_out.text())
        if atten_out_desired <= 31.5:
            atten_out0 = 63
            atten_out1 = 63 - int(atten_out_desired*2)
        else:
            atten_out0 = 63 - int((atten_out_desired-31.5)*2)
            atten_out1 = 0


