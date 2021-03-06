#-----------------------------------
# arcons_basic.py
#
# Written by Seth Meeker 07/08/10
#
# arcons.py runs archons control gui for camera status, telescope status, and SDR control
# updated from archons_test.py template
# Updated 2/28/11 to use matplotlib figure canvas backend for spectrum plotting
# Updated 2/28/11 to draw compass
# Updated 5/31/11 to overhaul imaging during an observation with real integration time, not just infinite integration
# Updated 6/2/11 to activate data file creation with beginning of observation
# Updated 6/2/11 to allow multiple pixels in a spectrum
# Updated 7/1/11 to include TCS functionality through an IP socket client
# Updated 7/24/11 to fully implement TCS Status queries at the telescope
# Updated 7/26/11 to implement a simpler imaging method purely from photon counts
#
# In arcons_basic.py:
# Pixel selection from image has been disabled.  No spectra or SNR are displayed since spectral information is no longer available.
# Image thread is turned off and imaging from binary files of counts will be done within the control gui routine
# Upgraded from version 1 to plot timestream of selected pixels' intensities
#
# Version 4 reupdated 06/14/12. Ability to turn on dummy TCS info added.
# Version 5 updated 06/14/12.  Now spawns PacketMaster.c process to handle data taking
# ----------------------------------
# Chris S. notes July 2014
# Image does not display.  Is this because Arcons_frame.png is not created?
# The line that does plt.savefig to create the image is commentd out.
#
# Upgrade to use MKID_ environment variables.
# Write  lib/mkid-environment.h before compiling PacketMaster
# uncomment line that does the plot.savefig to create Arcons_frame.png
import sys
import time
import datetime
import struct
import socket
from telnetlib import Telnet
import os
import subprocess
from os.path import isfile
#import installed libraries
from matplotlib import pyplot as plt
from numpy import *
from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from matplotlib.backends.backend_qt4 import FigureCanvasQT as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import ephem
#import my functions
from lib.rad2altaz import rad2altaz
from lib.make_image_v2 import make_image as make_image_import
from lib.HeaderGen import HeaderGen
import lib.pulses_v1 as pulses
from lib.getSeeing import getPalomarSeeing
#from lib.SignalFilterWheel import SignalFilterWheel
from lib.arcons_basic_gui import Ui_arcons
from tables import *

c = 3.0E17 #[nm/s]
h = 4.13567E-15 #[ev*s]

# Parse environment variables that define pixel geometry and check sanity
numXPixel = int(44)
numYPixel = int(46)
nRoaches = array(1,dtype=int)
sumNRoaches = nRoaches.sum()
beamRows = int(46)
beamCols = int(44)
nPixA = beamRows*beamCols*sumNRoaches
nPixB = numXPixel*numYPixel
assert nPixA==nPixB, "MKID_ geometry does not make sense %d %d"%(nPixA,nPixB)
print "Begin with number of pixels = ",nPixA

EMERGENCY_LASER = False #used only at Palomar if wti ips-400 switch is needed to turn on laser box

observatory = "Broida" # "Broida", "Palomar", or "Lick"
filt1 = Filters(complevel=1, complib='zlib', fletcher32=False)

filters = ['V-band','R-band','Open','405','546','Closed']

#path to labjack routines
ljpath = '/opt/software/SDR-master/DataReadout/ReadoutControls/lib/LabJackPython-8-26-2011/src/'

class StartQt4(QMainWindow):
    def __init__(self,parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_arcons()
        self.ui.setupUi(self)
        self.debug=0

        
        #delete old quicklook frames from previous observation to avoid confusion
        if isfile("TV_frame.bmp"):
            os.remove("TV_frame.bmp")
        elif isfile("TV_frame.png"):
            os.remove("TV_frame.png")

        #set some important permanent parameters (array size, energy range, directories)
        self.nxpix = self.get_xpix()
        self.nypix = self.get_ypix()
        self.int_time = 1 #seconds

        #self.rearrange_frames()
        self.ui.brightpix.setMaximum(self.nxpix*self.nypix)
        #self.resize(390+20+15+10*self.nxpix,475+20+10*self.nypix)

        self.check_params()

        self.Emin = 0.92 #eV corresponds to 1350 nm
        self.Emax = 3.18 #eV corresponds to 390 nm (changed from original 4.2 ev)

        self.ui.spectra_plot.canvas.ax.clear()
        self.ui.spectra_plot.canvas.ytitle = "Counts"
        self.ui.spectra_plot.canvas.xtitle = "Time"
        self.ui.spectra_plot.canvas.format_labels()
        self.ui.spectra_plot.canvas.show()

        #read in bad pixels from file so they can be "X"d out in the quicklook
        #self.bad_pix = random.randint(0,1024,40)
        self.bad_pix_x = []
        self.bad_pix_y = []
        self.spectrum_pixel_x = []
        self.spectrum_pixel_y = []
        self.pix_select_mode = "rect"
        self.sky_subtraction = False
        self.taking_sky = False
        self.calibrating = False
        #default beammap file, can be updated in gui with browse button
        self.beammapfile = '/opt/software/SDR-master/Setup/test/ps_r0_20140815-121539.h5#"beamimage.h5'
        print "beammapfile=",self.beammapfile
        self.filterfile = os.environ['MKID_FILTER_WHEEL_PATH']
        self.checkfilter()
        self.mirrorfile = os.environ['MKID_MIRROR_ANGLE_PATH']
        self.checkmirror()

        #set default directory, binning routine directory, and data directory
        self.defaultdir = QDir.currentPath()
        #self.bindir = str(self.defaultdir)+"/bin" # path where dataBin.py is saved and creates binned files
        self.bindir = os.environ['MKID_DATA_DIR']+"/bin"
        self.datadir = os.environ['MKID_DATA_DIR']#QDir.currentPath() #starts as default path until gui specifies new data path
        #put default directory in data directory search line upon startup
        self.ui.data_directory_lineEdit.setText(self.datadir)
        self.roachdir = "./" #where the roaches (or Ben's client) will look for directions on where to put data

        #upon startup we are not observing, but this becomes true when Start Obs is clicked
        self.observing = False

        #create image thread for image generation routine to happen while gui updates
        #self.image_thread = image_Worker(self, nxpix=self.nxpix, nypix=self.nypix, Emin=self.Emin, Emax=self.Emax)

        #create timer thread that controls observation timer
        self.timer_thread = timer_Worker(self)

        #load beam map from default beammap directory
        self.loadbeammap()

        #load flat factors
        self.loadFlatFactors()

        #use mouse to select pixel from tv_image, also triggers a new spectrum to be displayed
        self.ui.tv_image.mousePressEvent = self.start_pixel_select
        self.ui.tv_image.mouseReleaseEvent = self.end_pixel_select

        #Label filters
        self.ui.filter1.setText("1) "+str(filters[0]))
        self.ui.filter2.setText("2) "+str(filters[1]))
        self.ui.filter3.setText("3) "+str(filters[2]))
        self.ui.filter4.setText("4) "+str(filters[3]))
        self.ui.filter5.setText("5) "+str(filters[4]))
        self.ui.filter6.setText("6) "+str(filters[5]))

        #signal from image thread to make spectrum
        #QObject.connect(self.image_thread,SIGNAL("new_spectrum"),self.display_spectra)
        #button signals
        QObject.connect(self.ui.options_radioButton, SIGNAL("toggled(bool)"), self.expand_window)
        QObject.connect(self.ui.mode_buttonGroup, SIGNAL("buttonClicked(int)"), self.set_spectrum_mode)
        #QObject.connect(self.ui.plot_buttonGroup, SIGNAL("buttonClicked(int)"), self.set_plot_mode)
        #QObject.connect(self.ui.simple_imaging_radioButton, SIGNAL("toggled(bool)"),self.set_simple_imaging)
        QObject.connect(self.ui.subtract_sky_radioButton, SIGNAL("toggled(bool)"), self.set_sky_sub)
        #QObject.connect(self.ui.image_color_radioButton, SIGNAL("toggled(bool)"), self.set_image_color)
        QObject.connect(self.ui.search_pushButton, SIGNAL("clicked()"), self.file_dialog)

        QObject.connect(self.ui.choose_beamimage, SIGNAL("clicked()"), self.choose_beamimage)
        QObject.connect(self.ui.choose_bindir, SIGNAL("clicked()"), self.choose_bindir)

        QObject.connect(self.ui.laser_toggle, SIGNAL("clicked(bool)"), self.toggle_laser)

        QObject.connect(self.ui.start_observation_pushButton, SIGNAL("clicked()"), self.start_observation)
        #update binning routine's integration time if it is changed during an observation
        QObject.connect(self.ui.int_time_spinBox, SIGNAL("valueChanged(int)"), self.send_params)
        #Connect obs timer and stop button to their functionality of ending observation
        QObject.connect(self.timer_thread,SIGNAL("timeout()"), self.finish_observation)
        QObject.connect(self.ui.stop_observation_pushButton,SIGNAL("clicked()"), self.stop_observation)
        #Connect sky exposure button to taking sky count image for later sky subtraction
        QObject.connect(self.ui.takesky, SIGNAL("clicked()"), self.take_sky)
        #Connect filter wheel movement
        QObject.connect(self.ui.filter_buttonGroup, SIGNAL("buttonClicked(int)"), self.movefilter)
        #Connect button to update description in header
        QObject.connect(self.ui.update_description, SIGNAL("clicked()"), self.update_description)
        #Connect calibration arm functions
        QObject.connect(self.ui.do_cal_button, SIGNAL("clicked()"), self.do_cal)
        QObject.connect(self.ui.go_home_button, SIGNAL("clicked()"), self.go_home)
        QObject.connect(self.ui.goto_button, SIGNAL("clicked()"), self.goto_angle)

        #create timers to update images and statuses constantly
        self.status_timer = QTimer()
        QObject.connect(self.status_timer,SIGNAL("timeout()"),self.update_status)
        self.status_timer.start(1000)
        self.update_timer = QTimer()
        QObject.connect(self.update_timer,SIGNAL("timeout()"),self.update_remaining_time)
        self.update_timer.start(200)

        #create timer to poll path for changes to org file
        self.stattime = 0 #bin file creation time that is checked by check_files
        self.polling_timer = QTimer()
        QObject.connect(self.polling_timer,SIGNAL("timeout()"), self.check_files)
        #self.polling_timer.start(200) #moved to start_observation

        #signal image thread to restart if bin file is locked when it tries to access it
        #QObject.connect(self.image_thread,SIGNAL("retry_image()"), self.start_image_thread)

    #def start_image_thread(self):
        #self.image_thread.start_images(self.bindir)

    def toggle_laser(self):
        if EMERGENCY_LASER == True:
            if self.ui.laser_toggle.isChecked():
                try:
                    #client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #client.connect(("198.202.125.153", 23)) #connecting to ethernet power switch
                    #client.send("/on 1")
                    #response = client.recv(1024)
                    #print repr(response)
                    client = Telnet("198.202.125.153", 23)
                    client.read_until("IPS>",1)
                    client.write("/on 1\r")
                    print "sent command to telnet"
                    #print client.read_all()
                    client.read_until("IPS>",1)
                    client.write("/x\r")
                    client.close()
                    self.ui.laser_label.setText("ON")
                except:
                    print "Could not reach laser switch and turn laser ON"
                    return
            else:
                try:
                    #client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #client.connect(("198.202.125.153", 23)) #connecting to ethernet power switch
                    #client.send("/off 1")
                    #response = client.recv(1024)
                    #print repr(response)
                    client = Telnet("198.202.125.153", 23)
                    client.read_until("IPS>",1)
                    client.write("/off 1\r")
                    print "sent command to telnet"
                    #print client.read_all()
                    client.read_until("IPS>",1)
                    client.write("/x\r")
                    client.close()
                    self.ui.laser_label.setText("OFF")
                except:
                    print "Could not reach laser switch and turn laser OFF"
                    return
        else:
            if self.ui.laser_toggle.isChecked():
                laseronproc = subprocess.Popen("sudo nice -n -5 python %slaserBoxControl.py %s %s"%(ljpath,'on', 'all'),shell=True)
                laseronproc.wait()
                self.ui.laser_label.setText("ON")
            else:
                laseroffproc = subprocess.Popen("sudo nice -n -5 python %slaserBoxControl.py %s %s"%(ljpath,'off','all'),shell=True)
                laseroffproc.wait()
                self.ui.laser_label.setText("OFF")

    def go_home(self):
        self.ui.goto_angle.setValue(40)
        self.goto_angle()
        print "Moved calibration arm to HOME"

    def goto_angle(self):
        angle = self.ui.goto_angle.value()
        while self.mirrorposition != angle:
            if self.mirrorposition < angle:
                self.mirrorposition+=1
                gotoproc = subprocess.Popen("sudo nice -n -5 python %smirrorGoToAngle.py %i"%(ljpath, self.mirrorposition),shell=True)
                gotoproc.wait()
            else:
                self.mirrorposition-=1
                gotoproc = subprocess.Popen("sudo nice -n -5 python %smirrorGoToAngle.py %i"%(ljpath, self.mirrorposition+1),shell=True)
                gotoproc.wait()
        f=open(str(self.mirrorfile),'w') #put file where dataBin is running
        f.write(str(self.mirrorposition))
        f.close()
        print "Moved calibration arm to angle %i"%(angle)

    def do_cal(self):
        caltime = self.ui.cal_time.value()
        calangle = self.ui.cal_angle.value()
        self.ui.goto_angle.setValue(calangle)
        print "Running calibration observation for %i seconds"%(caltime)
        self.calibrating = True
        self.goto_angle()
        self.ui.laser_label.setText("ON")
        self.ui.laser_toggle.setChecked(True)
        self.toggle_laser()
        self.start_observation()
        #calproc.wait()
        #print "FINISHED CALIBRATION"

    def checkmirror(self):
        if not isfile(self.mirrorfile):
            msgbox = QMessageBox()
            msgbox.setText("No mirror position saved to file.\nHOMING MIRROR TO 40 DEGREES")
            msgbox.exec_()
            homeproc = subprocess.Popen("sudo nice -n -5 python %smirrorGoToAngle.py %i"%(ljpath, 40),shell=True)
            homeproc.wait()
            self.mirrorposition = 40
            self.ui.goto_angle.setValue(self.mirrorposition)
            f=open(str(self.mirrorfile),'w') #put file where dataBin is running
            f.write(str(self.mirrorposition))
            f.close()
        else:
            f = open(str(self.mirrorfile),'r')
            self.mirrorposition = f.read()
            self.mirrorposition = int(self.mirrorposition)
            f.close()
            print "Mirror at angle " + str(self.mirrorposition)+" on startup."

    def checkfilter(self):
        if not isfile(self.filterfile):
            msgbox = QMessageBox()
            msgbox.setText("No filter position saved to file.\nMOVE FILTER WHEEL TO POSITION 6 (DARK) BEFORE CONTINUING")
            msgbox.exec_()
            self.filterposition = 6
            self.ui.filter6.setChecked(True)
            f=open(str(self.filterfile),'w') #put file where dataBin is running
            f.write(str(self.filterposition)+' '+str(filters[self.filterposition-1]))
            f.close()
        else:
            f = open(str(self.filterfile),'r')
            text = f.read()
            self.filterposition,self.startfilter = text.split(' ')
            self.filterposition = int(self.filterposition)
            f.close()
            print "Filter at position " + str(self.filterposition) + " ("+str(self.startfilter)+") on startup."
            if self.filterposition == 1:
                self.ui.filter1.setChecked(True)
            elif self.filterposition == 2:
                self.ui.filter2.setChecked(True)
            elif self.filterposition == 3:
                self.ui.filter3.setChecked(True)
            elif self.filterposition == 4:
                self.ui.filter4.setChecked(True)
            elif self.filterposition == 5:
                self.ui.filter5.setChecked(True)
            elif self.filterposition == 6:
                self.ui.filter6.setChecked(True)

    def movefilter(self):
        if self.ui.filter1.isChecked():
            moveto = 1
        elif self.ui.filter2.isChecked():
            moveto = 2
        elif self.ui.filter3.isChecked():
            moveto = 3
        elif self.ui.filter4.isChecked():
            moveto = 4
        elif self.ui.filter5.isChecked():
            moveto = 5
        elif self.ui.filter6.isChecked():
            moveto = 6
        #moveto = int(self.ui.filterpos_spinbox.value()) #input from gui
        if moveto < 1 or moveto >6:
            print "Please select filter position between 1 and 6"
        else:
            while self.filterposition != moveto:
                self.filterposition +=1
                if self.filterposition == 7:
                    self.filterposition = 1
                filtproc = subprocess.Popen("sudo nice -n -5 python %sSignalFilterWheel.py"%(ljpath),shell=True)
                filtproc.wait()
                time.sleep(1) #wait 1 second for filter to complete move.  Should not send more than 1 signal every 2 seconds.
                #sent bnc signal to filter
                print "Filter moved to position "+ str(self.filterposition) +" ("+str(filters[self.filterposition-1])+")"
            #write new position to file
            f=open(str(self.filterfile),'w') #put file where dataBin is running
            f.write(str(self.filterposition)+' '+str(filters[self.filterposition-1]))
            f.close()
            print "Completed filter move"

    def loadbeammap(self):
        bmfile = openFile(self.beammapfile, 'r')
        #read beammap in to memory to create beam image
        self.bmap = bmfile.root.beammap.beamimage.read()
        self.bmap = rot90(self.bmap)
        self.bmap = flipud(self.bmap)
        bmfile.close()

    def loadFlatFactors(self):
        try:
            #self.flatFactors = load('/home/sean/data/common/intensityFactors.npy')
            self.flatFactors = flipud(self.flatFactors)
        except:
            print "Unable to load flat factors, flat fielding will not work"
            self.ui.flat_field_radioButton.setEnabled(False)

    #turn gui functionality on/off when observations are stopped/running
    def enable_observation(self):
        self.ui.start_observation_pushButton.setEnabled(True)

    def disable_directory_change(self):
        self.ui.search_pushButton.setEnabled(False)
        self.ui.data_directory_lineEdit.setEnabled(False)
    def enable_directory_change(self):
        self.ui.search_pushButton.setEnabled(True)
        self.ui.data_directory_lineEdit.setEnabled(True)

    #open dialog to select data path
    def file_dialog(self):
        self.newdatadir = QFileDialog.getExistingDirectory(self, str("Choose Save Directory"), "",QFileDialog.ShowDirsOnly)
        self.newdatadir = str(self.newdatadir)
        if len(self.newdatadir) > 0:
            self.datadir = self.newdatadir
            #write file that passes new directory to data thread
            #f=open(str(self.bindir)+"/path.bin",'w') #put file where dataBin is running
            #f.write(str(self.datadir)) #write data path to file
            #f.close()
            #f=open(str(self.defaultdir)+"/path.sim",'w') #put file where dataSim is running
            #f.write(str(self.datadir)) #write data path to file
            #f.close()
        self.ui.data_directory_lineEdit.setText(self.datadir) #put new path name in line edit

    def start_observation(self):
        '''we will want this function to activate the saving of data.  will need to name,
        open, and begin writing to file.  also activate observation timer if a
        time is given.'''
        if self.calibrating == True:
            self.exptime = self.ui.cal_time.value()
        else:
            self.exptime = self.ui.obs_time_spinBox.value()
        if self.exptime == 0:
            print "Please enter a desired observation time in seconds"
        else:
            self.image_time = 0
            self.counts = zeros((self.exptime,self.nxpix*self.nypix),int32)
            #print self.counts
            self.rotated_counts = zeros((self.exptime,self.nypix,self.nxpix),int32)
            self.observing = True
            #turn off things we don't want messed with during an exposure
            self.disable_directory_change()
            self.ui.update_description.setEnabled(False)
            self.ui.start_observation_pushButton.setEnabled(False)
            self.ui.obs_time_spinBox.setEnabled(False)
            #call headerGen and give it telescope status/file info
            if self.calibrating == True:
                basename = "cal_"
            else:
                basename = "obs_"
            targname = str(self.ui.target_lineEdit.text())
            self.int_time = self.ui.int_time_spinBox.value()
            self.start_time = int(floor(time.time()))
            self.get_telescope_position(lt = self.start_time) #returns alt, az, ra, dec, ha, lst, utc, airmass
            self.get_telescope_status() #only returns focus
            self.get_parallactic()
            self.seeing = getPalomarSeeing()
            #convert ra and dec from ra:ra:ra, dec:dec:dec to floats
            self.dec = float(ephem.degrees(self.dec))
            self.ra = float(ephem.hours(self.ra))
            filthead = str(filters[self.filterposition-1])
            self.obsname = basename+time.strftime("%Y%m%d-%H%M%S", time.gmtime(self.start_time))
            self.obsfile = str(self.obsname) + '.h5'
            logfile = 'logs/'+str(self.obsname)+'.log'
            #logfile = 'logs/pm.log'
            self.ui.file_name_lineEdit.setText(str(self.obsfile))
            if os.path.exists(self.bindir) == False:
                os.mkdir(self.bindir)
            HeaderGen(self.obsfile, self.beammapfile, self.start_time,  self.exptime, self.ra, self.dec, self.alt, self.az, self.airmass, self.lst, filthead,dir=str(self.datadir), telescope = observatory, target=targname, focus=self.focus, parallactic = self.parallactic)

            # Write the file lib/mkid-environment.h used by lib/PacketMaster.c
            meFile = open("lib/mkid-environment.h","wb")
            meFile.write("#define NROACHES %d\n"%nRoaches)
            meFile.write("#define NPIXELS_PER_ROACH %d\n"%(beamRows*beamCols))
            meFile.write("#define BEAM_ROWS %d\n"%beamRows)
            meFile.write("#define BEAM_COLS %d\n"%beamCols)
            meFile.close()

            # make the bin directory if it does not exist
            try:
                os.mkdir("bin")
            except OSError:
                pass

            proc = subprocess.Popen("h5cc -shlib -pthread -o bin/PacketMaster lib/PacketMaster.c",shell=True)
            #proc = subprocess.Popen("h5cc -shlib -pthread -o bin/PacketMaster lib/PacketMasterR1.c",shell=True)
            proc.wait()
            filePath = os.path.join(self.datadir,self.obsfile)
            pmCommand = "sudo nice -n -10 bin/PacketMaster %s %s >> %s"%(filePath,self.beammapfile,logfile)


            # make the logs directory if it does not exist
            try:
                os.mkdir("logs")
            except OSError:
                pass
            print "Start PacketMaster like this: ",pmCommand
            self.pulseMasterProc = subprocess.Popen(pmCommand,shell=True)
            print "PacketMaster process started with logfile %s" % logfile
            print "Header written to data file, beginning observation..."
            #time.sleep(5) #wait 1 second for Ben's code to create beamimage before activating rebinning
            #self.send_params()
            self.polling_timer.start(200)
            #start observation timer
            self.timer_thread.start_timer(self.exptime)

    def stop_observation(self):
        '''what happens when you click the "stop observation" button.
        will need to clear and reset timer, close and save any data files
        and re-enable directory change and observations'''
        self.ui.continuous.setChecked(False) #turn off continuous observing so packet master can reset
        print "Calling stopPacketMaster.sh"
        subprocess.Popen("./stopPacketMaster.sh",shell=True)
        #subprocess.Popen("./stopPacketMasterR1.sh",shell=True)
        self.finish_observation()

    def finish_observation(self):
        #f=open(str(self.bindir)+"/stop.bin", 'wb')
        #f.close()
        #f=open(str(self.roachdir)+"/stop.sim", 'wb')
        #f.close()
        self.observing = False
        #turn on the things that were disabled during exposure
        self.enable_directory_change()
        self.ui.update_description.setEnabled(True)
        self.ui.start_observation_pushButton.setEnabled(True)
        self.ui.obs_time_spinBox.setEnabled(True)
        #turn off observation timer and reset
        if self.timer_thread.isRunning():
            self.timer_thread.stop()
        #self.image_thread.reset()
        if self.calibrating == True:
            print "FINISHED CALIBRATION"
            self.go_home()
            self.ui.laser_label.setText("OFF")
            self.ui.laser_toggle.setChecked(False)
            self.toggle_laser()
            self.calibrating = False
        if self.ui.continuous.isChecked():
             self.pulseMasterProc.wait() #wait for packet master to finish and start a new observation automatically
             self.start_observation()

    def update_description(self):
        #updates the description section in the header info with whatever is in the description box on the dashboard. Activated by clicking "update description" button after data taking is complete.
        h5file = openFile(str(self.datadir)+'/'+str(self.obsfile), mode='a')
        hdrtable = h5file.root.header.header.read()
        newdesc = str(self.ui.textEdit.toPlainText())
        hdrtable['description'] = newdesc
        h5file.removeNode('/header',recursive=True)
        h5file.flush()
        hdrgrp = h5file.createGroup('/','header','Group containing observation description')
        h5table = h5file.createTable(hdrgrp, 'header', pulses.ObsHeader, "Header",filters=filt1)
        #hdrtable = h5table.row
        #hdrtable = h5file.createTable('/header', header, "Header",filters=filt1)
        h5table.append(hdrtable)
        h5file.flush()
        h5file.close()
        print "Updated description in header of " + str(self.obsfile)

    def choose_beamimage(self):
        newbeamimage = QFileDialog.getOpenFileName(parent=None, caption=QString(str("Choose Beamimage File")),directory = ".",filter=QString(str("H5 (*.h5)")))
        if len(newbeamimage) > 0:
            self.beammapfile = str(newbeamimage)
            self.loadbeammap()

    def choose_bindir(self):
        newbindir = QFileDialog.getExistingDirectory(self, str("Choose Bin Directory"), "",QFileDialog.ShowDirsOnly)
        if len(newbindir) > 0:
            self.bindir = str(newbindir)

    def send_params(self):
        if self.observing == True:
            #send parameter file to dataBin including integration time, and obs file name
            f=open(str(self.bindir)+"/file.bin", 'w')
            f.write(str(self.obsfile))
            f.close()
            f=open(str(self.bindir)+"/params.bin", 'wb')
            datapacket = struct.pack('iiiff', self.int_time, self.nxpix, self.nypix, self.Emin, self.Emax)
            #datapacket = struct.pack('iiiff', self.int_time, self.nypix, self.nxpix, self.Emin, self.Emax)
            f.write(datapacket)
            f.close()
            #send parameter files to eventually to data catching client with start time, exposure time, and obsfile name
            f=open(str(self.roachdir)+"/file.sim", 'w')
            f.write(str(self.obsfile))
            f.close()
            f=open(str(self.roachdir)+"/params.sim", 'wb')
            datapacket = struct.pack('ii',self.start_time,self.exptime)
            f.write(datapacket)
            f.close()

    def set_sky_sub(self):
        #Use radio button to set if we want sky subtraction to be on or off
        if self.ui.subtract_sky_radioButton.isChecked():
            self.sky_subtraction = True
        else:
            self.sky_subtraction = False

    #def set_simple_imaging(self):
    #   if self.ui.simple_imaging_radioButton.isChecked():
    #       self.image_thread.simple_imaging = True
    #   else:
    #       self.image_thread.simple_imaging = False

    #def set_image_color(self):
    #   if self.ui.image_color_radioButton.isChecked():
    #       self.image_thread.color_on = True
    #   else:
    #       self.image_thread.color_on = False

    #def load_skyfile(self):
        #pass

    #def load_darkfile(self):
        #pass

    def take_sky(self):
        self.taking_sky = True
        self.skytime = self.ui.int_time_spinBox.value()
        self.skycount = zeros((1,self.nypix,self.nxpix))
        self.skyrate = zeros((1,self.nypix,self.nxpix))
        self.start_observation()

    def make_image(self):
        #rawdata = load(self.binfile)
        rawdata = loadtxt(self.binfile)

        #debug data
        #rawdata=load('/home/sean/Matt/DataReadout/cdata.npy')
        #rawdata=load('/Users/ourhero/Documents/Mazinlab/cdata.npy')

        rawshape = shape(rawdata)
        #print 'Rotating data:'
        #print rawdata.shape
        rotated = flipud(rawdata)
        #print rotated.shape
        #rotated = rot90(rawdata)
        #print rotated.shape
        #rotated = rot90(rotated)
        #print rotated.shape
        #rotated = rot90(rotated)
        #print rotated.shape
        #rotated = reshape(rotated,(1,self.nypix,self.nxpix))
        #print rotated.shape

        if self.taking_sky == True:
            self.skycount += rotated

        tf = self.image_time
        self.int_time = self.ui.int_time_spinBox.value()
        ti = tf-self.int_time


        try:
            newcounts = reshape(rawdata,(1,self.nxpix*self.nypix))
            #self.counts= append(self.counts,newcounts,axis=0)
            #self.rotated_counts = append(self.rotated_counts, rotated, axis=0)

            self.counts[self.image_time] = newcounts
            self.rotated_counts[self.image_time] = rotated

            #print 'shape of counts', shape(self.counts)
            if ti<0:
                ti = 0
            if tf==0 or tf==ti:
                image_counts = newcounts
            else:
                image_counts = sum(self.counts[ti:tf],axis=0)
                image_counts = reshape(image_counts,(1,self.nxpix*self.nypix))

            if self.sky_subtraction == True:
                image_counts = image_counts-reshape(self.skyrate*(tf-ti),(1,self.nxpix*self.nypix))

            photon_count = reshape(image_counts,rawshape)
            #print photon_count.shape
            photon_count = flipud(photon_count)
            #photon_count = rot90(photon_count)
            #photon_count = rot90(photon_count)
            #photon_count = rot90(photon_count)

            if self.ui.flat_field_radioButton.isChecked():
                photon_count *= self.flatFactors

            if self.ui.contrast_mode.isChecked():
                self.vmin = self.ui.vmin.value()
                self.vmax = self.ui.vmax.value()
            else:
                indices = sort(image_counts)
                brightest = self.ui.brightpix.value()
                self.vmin = 0
                self.vmax = indices[0,-1*(brightest)]

            #fig = plt.figure(figsize=(.44,.46), dpi=100, frameon=False)
            fig = plt.figure(figsize=(0.01*numXPixel,0.01*numYPixel), dpi=100, frameon=False)
            im = plt.figimage(photon_count, cmap='gray',vmin = self.vmin, vmax = self.vmax)

            if tf==ti:
                self.redpix = where(photon_count > 2000)
            else:
                self.redpix = where(photon_count > 2000*(tf-ti))
            #im = plt.figimage(rawdata, cmap='gray')
            plt.savefig("Arcons_frame.png", pad_inches=0)
            #try:
            #    print '# redpix= ',len(self.redpix[0])
            #except:
            #    print '# redpix= 0'
            self.image_time+=1
            self.update_image()
            if self.taking_sky == True:
                if self.image_time == self.skytime:
                    self.taking_sky = False
                    self.skyrate = self.skycount/self.skytime
        except ValueError:
            print 'Warning:  shape(rawdata)= ', shape(rawdata), "self nxpix,nypix=",self.nxpix,self.nypix

    def makepixmap(self, imagefile, scalex=1, scaley=1):
        '''Given an image file this function converts them to pixmaps to be displayed by QT gui'''
        qtimage = QImage(imagefile)
        width, height = qtimage.size().width(), qtimage.size().height()
        qtimage = qtimage.scaled(width*scalex,height*scaley)
        pix = QPixmap.fromImage(qtimage)
        return pix

    def display_image(self):
        #search directory for image
        #if self.image_thread.simple_imaging == False:
            #imagefile = "./TV_frame.bmp"
        #else:
            #imagefile = "./TV_frame.png"
        imagefile = "./Arcons_frame.png"
        #convert to pixmap
        if isfile(imagefile):
            pix = self.makepixmap(imagefile, scalex=10, scaley=10)
            #display pixmap
            self.scene = QGraphicsScene()
            self.scene.addPixmap(pix)
            if len(self.redpix)> 0:
                for i in xrange(len(self.redpix[0])):
                    x = self.redpix[1][i]
                    y = self.redpix[0][i]
                    darkDarkRed = QColor(60,0,0)
                    self.scene.addRect(10*(x),10*(y),9,9, darkDarkRed, darkDarkRed)
                    #self.scene.addRect(10*(x),10*(y),9,9, Qt.darkRed, Qt.darkRed) #make 'hot' pixels red
            for i in xrange(len(self.bad_pix_x)):
                x = self.bad_pix_x[i]
                y = self.bad_pix_y[i]
                self.scene.addLine(10*x,10*y,10*x+9,10*y+9,Qt.red)
                self.scene.addLine(10*x,10*y+9,10*x+9,10*y,Qt.red)
            if len(self.spectrum_pixel_x) != 0:
                for i in xrange(len(self.spectrum_pixel_x)):
                    x = self.spectrum_pixel_x[i]
                    y = self.spectrum_pixel_y[i]
                    #self.scene.addRect(10*(x),10*(y),9,9, Qt.blue) #10's since image plot is 320x320 pixels
                    self.scene.addRect(10*(x),10*(y),9,9, Qt.blue)
            self.ui.tv_image.setScene(self.scene)
            self.ui.tv_image.show()
            #os.remove(str(imagefile))
        else:
            print "blank scene since ",imagefile," does not exist"
            self.blankscene = QGraphicsScene()
            self.blankscene.clear()
            self.ui.tv_image.setScene(self.blankscene)
            self.ui.tv_image.show()

    def expand_window(self):
        #if spectrum options button is clicked resize window to show/hide options
        if self.ui.options_radioButton.isChecked():
            #rx = 590+20+10*self.nxpix
            #ry = 450+20+10*self.nypix
            rx = 590+20+10*numXPixel
            ry = 450+20+10*numYPixel

        else:
            #rx = 380+20+15+10*self.nxpix
            #ry = 450+20+10*self.nypix
            rx = 380+20+15+10*numXPixel
            ry = 450+20+10*numYPixel
        print "resize to rx,ry = ",rx,ry
        self.resize(rx,ry)

    #def set_plot_mode(self):
        #change between spectra plots and signal to noise ratio plots
    #   if self.ui.plot_snr_radioButton.isChecked():
    #       self.image_thread.set_plot_mode("snr")
    #       self.ui.spectra_plot.canvas.ytitle = "Signal to Noise"
    #   else:
    #       self.image_thread.set_plot_mode("spectra")
    #       self.ui.spectra_plot.canvas.ytitle = "Counts"
    #   pass

    def set_spectrum_mode(self):
        if self.ui.drag_select_radioButton.isChecked():
            self.pix_select_mode="drag"
            self.spectrum_pixel_x = []
            self.spectrum_pixel_y = []
        elif self.ui.rect_select_radioButton.isChecked():
            self.pix_select_mode="rect"
            self.spectrum_pixel_x = []
            self.spectrum_pixel_y = []
        elif self.ui.circ_select_radioButton.isChecked():
            self.pix_select_mode="circ"
            self.spectrum_pixel_x = []
            self.spectrum_pixel_y = []

    def start_pixel_select(self,event):
        #Mouse press returns x,y position of first pixel to be used in spectra
        self.startrawx,self.startrawy = event.pos().x(), event.pos().y()
        self.startpx = self.startrawx/10
        self.startpy = self.startrawy/10
        self.startpix = self.nxpix*self.startpy+self.startpx
        #print '(' , self.startpx,',',self.startpy,')'

    def end_pixel_select(self,event):
        #Mouse release returns x,y position of last pixel to be used in spectra
        self.endrawx,self.endrawy = event.pos().x(), event.pos().y()
        self.endpx = self.endrawx/10
        self.endpy = self.endrawy/10
        self.endpix = self.nxpix*self.endpy+self.endpx
        #print 'x: ',
        #print self.endrawx,
        #print 'y: ',
        #print self.endraw
        self.pixel_list()

    def pixel_list(self):
        #if click and drag selection is on, add new pixels to the list of all pixels being plotted
        if self.pix_select_mode == "drag":
            if self.startpix != self.endpix:
                #get all pix in box
                allx = xrange(min(self.startpx,self.endpx),max(self.startpx, self.endpx)+1)
                ally = xrange(min(self.startpy,self.endpy),max(self.startpy, self.endpy)+1)
                pixx = []
                pixy = []
                for x in allx:
                    for y in ally:
                        pixx.append(x)
                        pixy.append(y)
            else:
                pixx = [self.startpx]
                pixy = [self.startpy]
        elif self.pix_select_mode == "rect":
            #get all pix in box
            length = self.ui.rect_x_spinBox.value()
            height = self.ui.rect_y_spinBox.value()
            #print 'length: ',
            #print length
            #print 'height: ',
            #print height
            allx = xrange(self.startpx-int(ceil(length/2.0)-1),self.startpx+int(floor(length/2.0))+1)
            ally = xrange(self.startpy-int(ceil(height/2.0)-1),self.startpy+int(floor(height/2.0))+1)
            self.spectrum_pixel_x = []
            self.spectrum_pixel_y = []
            pixx = []
            pixy = []
            for x in allx:
                for y in ally:
                    pixx.append(x)
                    pixy.append(y)
            #print 'pix x: ',
            #print pixx
            #print 'pix y: ',
            #print pixy
        elif self.pix_select_mode == "circ":
            r = self.ui.circ_r_spinBox.value()
            length = 2*r
            height = length
            allx = xrange(self.startpx-int(ceil(length/2.0)),self.startpx+int(floor(length/2.0))+1)
            ally = xrange(self.startpy-int(ceil(height/2.0)),self.startpy+int(floor(height/2.0))+1)
            self.spectrum_pixel_x = []
            self.spectrum_pixel_y = []
            pixx = []
            pixy = []
            for x in allx:
                for y in ally:
                    if (abs(x-self.startpx))**2+(abs(y-self.startpy))**2 <= (r)**2:
                        pixx.append(x)
                        pixy.append(y)
        for i in xrange(len(pixx)):
            x = pixx[i]
            y = pixy[i]
            #print 'x: ',x,' y: ',y
            #check for repeated pixels (clicked for deselection) and out of bounds pixels, remove from total array
            if x >= 0 and x <= self.nxpix-1 and y>=0 and y <=self.nypix-1:
                self.spectrum_pixel_x.append(x)
                self.spectrum_pixel_y.append(y)
                #print 'Look here for an error?'

            if (x in self.spectrum_pixel_x) and (y in self.spectrum_pixel_y):

                px = array(self.spectrum_pixel_x)
                py = array(self.spectrum_pixel_y)
                indicesx = where( px == x)[0]
                indicesy = where( py == y)[0]
                #print 'px: ',x
                #print 'py: ',y
                #print 'indx: ',indicesx
                #print 'indy: ',indicesy
                repeats = []
                for val in indicesx:
                    spot = where(indicesy == val)[0]
                    if len(spot>0):
                        for i in xrange(len(spot)):
                            repeats.append(indicesy[spot[i]])
                        #print 'repeats: ',repeats,len(repeats)
                if len(repeats) > 1:
                    repeats = sort(repeats)
                    for i in xrange(len(repeats)):
                        del(self.spectrum_pixel_x[repeats[-(i+1)]])
                        del(self.spectrum_pixel_y[repeats[-(i+1)]])

        if self.observing == False:
            #self.image_thread.update_spectrum(self.bindir)
            if hasattr(self, 'image_time'):
                self.display_timestream()
                self.display_image()
            else:
                print "'StartQt4' object has no attribute 'image_time'; cannot make plot"


    def display_timestream(self):
        #plots spectra directly from bin file data passed from image thread
        time1 = self.image_time
        time0 = 0 #time1-100
        if time0<0:
            time0 = 0
        time = arange(time0,time1)
        plotcounts = zeros(len(time))
        #plotcounts = empty(0)
        for t in time:
            counts=0
            for i in xrange(len(self.spectrum_pixel_x)):
                counts += int(self.rotated_counts[t,self.spectrum_pixel_y[i],self.spectrum_pixel_x[i]])
            plotcounts[t] += counts
            #plotcounts = append(plotcounts,counts)
        self.ui.spectra_plot.canvas.ax.clear()
        self.spectrum_pixel = self.bmap[median(self.spectrum_pixel_x)][(self.nypix-1)-median(self.spectrum_pixel_y)]
        self.ui.pixelpath.setText(str(self.spectrum_pixel))
        self.ui.row.setText(str((numYPixel-1)-median(self.spectrum_pixel_y)))
        self.ui.col.setText(str(median(self.spectrum_pixel_x)))
        #self.spectrum_pixel = self.nxpix*(median(self.spectrum_pixel_y))+median(self.spectrum_pixel_x)
        #self.ui.pixel_no_lcd.display(self.spectrum_pixel)
        #self.ui.integrated_snr_lcd.display(SNR)
        #self.ui.spectra_plot.canvas.ax.plot(bins,counts,'o')
        #print len(time)
        #print len(plotcounts)
        #print shape(time)
        #print shape(plotcounts)
        self.ui.spectra_plot.canvas.ax.plot(time,plotcounts)
        self.ui.spectra_plot.canvas.format_labels()
        self.ui.spectra_plot.canvas.draw()
        self.ui.spectra_plot.canvas.ax.plot(time,plotcounts)
        #if len(self.spectrum_pixel_x) != 0:
        #   self.scene = QGraphicsScene()
        #   for i in xrange(len(self.spectrum_pixel_x)):
        #       x = self.spectrum_pixel_x[i]
        #       y = self.spectrum_pixel_y[i]
        #       print x,',',y
        #       self.scene.addRect(10*(x),10*(y),9,9, Qt.blue) #10's since image plot is 320x320 pixels
        #   self.ui.tv_image.setScene(self.scene)
        #   self.ui.tv_image.show()

    def make_compass(self, azimuth):
        pi = arccos(-1.)
        azimuth *= (pi/180) #azimuth is sent in radians already from pyephem calculation
        self.compass = QGraphicsScene()
        w = self.ui.compass_graphicsView.width()-5.0
        h = self.ui.compass_graphicsView.height()-5.0
        r = w/2.0
        #draw compass and markings
        self.compass.addEllipse(0,0,w,h,pen=Qt.black)
        #draw arrow
        x1 = 0 #line always starts from center
        y1 = 0
        #calculate end of arrow from azimuth
        x2 = r*sin(azimuth)
        y2 = r*cos(azimuth)
        #flip x's for bearing compass
        x1 = -1*x1
        x2 = -1*x2
        #invert y's and shift x and y since graphics view (0,0) is top left corner
        y1 = -1*y1
        y2 = -1*y2
        x1,y1,x2,y2 = x1+w/2.0,y1+h/2.0,x2+h/2.0,y2+h/2.0
        self.compass.addLine(x1,y1,x2,y2,pen=Qt.green)
        self.ui.compass_graphicsView.setScene(self.compass)
        self.ui.compass_graphicsView.show()

    def get_parallactic(self):
        if observatory == "Palomar":
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(("198.202.125.194", 5004)) #connecting directly at Palomar
                #client.connect(("10.200.2.11", 49200)) #connecting directly at Palomar
                client.send('?PARALLACTIC\r')
                response = client.recv(1024)
                client.close()
            except:
                print "Connection to TCS failed on get_parallactic"
                return

            parallactic = response.split('\n')
            title, par_value = parallactic[0].split('= ')
            self.parallactic = float(par_value)
        else:
            self.parallactic = nan


    def get_telescope_status(self):
        if observatory == "Palomar":
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(("198.202.125.194", 5004))
                #client.connect(("10.200.2.11", 49200)) #connecting directly at Palomar
                client.send('REQSTAT\r')
                response = client.recv(1024)
                client.close()
            except:
                print "Connection to TCS failed on get_telescope_status"
                return

            print response
            utc, line2, line3, line4, cass_angle = response.split('\n')
            id, focus, tubelength = line2.split(', ')
            focus_title, focus_val = focus.split('= ')
            self.focus = focus_val
        else:
            self.focus = nan

    def get_telescope_position(self, lt=0):

        if observatory == "Palomar":
            #Palomar's location
            self.lat = 33.0 + 21.0/60.0 + 21.6/3600.0
            self.lon = 116.0 + 51.0/60.0 + 46.8/3600.0

            #send status request to TCS system
            #client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #client.connect(("198.202.125.194", 49200)) #connecting remotely to Palomar

            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(("198.202.125.194", 5004))
                #client.connect(("10.200.2.11", 49200)) #connecting directly at Palomar
                client.send('REQPOS\r')
                response = client.recv(1024)
                client.close()
            except:
                print "Connection to TCS failed on get_telescope_position"
                return

            #split response into status fields
            line1,line2,airmass = response.split('\n')

            utc, lst = line1.split(', ')
            ra, dec, ha = line2.split(', ')

            utc_title, junk, utc_day, utc_time = utc.split(' ')
            #utc_hour, utc_min, utc_sec = utc_time.split(':')
            self.utc = utc_time

            lst_title, junk, lst_time = lst.split(' ')
            #lst_hour, lst_min, lst_sec = lst_time.split(':')
            self.lst = lst_time

            ra_title, junk, ra_val = ra.split(' ')
            #ra_hour, ra_min, ra_sec = ra_val.split(':')
            self.ra = (ra_val)

            dec_title, junk, dec_val = dec.split(' ')
            #dec_hour, dec_min, dec_sec = dec_val.split(':')
            self.dec = (dec_val)

            ha_title, junk, ha_val = ha.split(' ')
            #ha_hour, ha_min, ha_sec = ha_val.split(':')
            self.ha = ha_val

            airmass_title, airmass_val = airmass.split('=  ')
            airmass_val=airmass_val[:-1]
            self.airmass = float(airmass_val)

            #calculate alt and az of current target
            targname = str(self.ui.target_lineEdit.text())
            target = ephem.readdb(str(targname)+',f|L,'+str(ra_val)+','+str(dec_val)+',2000')

            if lt==0:
                lt = time.time()
            dt = datetime.datetime.utcfromtimestamp(lt)

            palomar = ephem.Observer()
            palomar.long, palomar.lat = '-116.0:51.0:46.80', '33.0:21.0:21.6'
            palomar.date = ephem.Date(dt)
            palomar.elevation = 1706.0
            target.compute(palomar)
            self.alt, self.az = target.alt*(180./math.pi), target.az*(180/math.pi)

            #print float(ephem.degrees(self.alt))
            #print float(ephem.degrees(self.az))

            self.seeing = getPalomarSeeing()

        elif observatory == "Lick":
            #Lick's location
            self.lat = 37.0 + 20.0/60.0 + 24.6/3600.0
            self.lon = -1.*(121.0 +  38.0/60.0 + 43.80/3600.0)
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(("shard",2345))
                client.send('telinfo airmass dec ha sid ut_date ut_time ra\r')
                response = client.recv(256)
                client.close()
            except:
                print "Connection to TCS failed on get_telescope_position"
                return

            #split response into status fields
            a = response.split(' ')
            b = []
            for i in xrange(len(a)):
                if a[i] != '':
                    b.append(a[i])
            airmass = b[0]
            dec = b[1]
            ha = b[2]
            sid = b[3]
            utc_date = b[4]
            utc_time = b[5]
            ra = b[6]

            self.utc = utc_time
            self.lst = sid
            self.ra = ra
            self.dec = dec
            self.ha = ha
            self.airmass = float(airmass)

            #calculate alt and az of current target
            targname = str(self.ui.target_lineEdit.text())
            target = ephem.readdb(str(targname)+',f|L,'+str(ra)+','+str(dec)+',2000')

            if lt==0:
                lt = time.time()
            dt = datetime.datetime.utcfromtimestamp(lt)

            lick = ephem.Observer()
            lick.long, lick.lat = '-121:38:43.80', '37:20:24.6'
            lick.date = ephem.Date(dt)
            lick.elevation = 1283.0
            target.compute(lick)
            self.alt, self.az = target.alt*(180./math.pi), target.az*(180/math.pi)

        else:
            #UCSB Broida Hall's location from Google Earth
            self.lat = 34.414243
            self.lon = -119.843009

            ###Code for dummy status setting
            self.ra = float(self.ui.RA_lineEdit.text())
            self.dec = float(self.ui.Dec_lineEdit.text())
            #get utc and local times
            self.t = time.gmtime()
            self.utc = time.strftime("%H:%M:%S",self.t)
            self.lt = time.localtime()
            #Calculate alt, az, and airmass(X)
            self.alt, self.az, self.lst, self.ha = rad2altaz(self.ra, self.dec, self.lon, self.lat, self.t)
            self.airmass = 1./cos((pi/180)*(90-self.alt))
            #self.parallactic = 0.0


    def set_telescope_status(self):
        self.get_telescope_position()
        #display coordinates
        self.ui.ra_label.setText(str(self.ra))
        self.ui.dec_label.setText(str(self.dec))
        self.ui.alt_label.setText(str(self.alt))
        self.ui.az_label.setText(str(self.az))
        self.ui.airmass_label.setText(str(self.airmass))
        self.ui.lst_label.setText(str(self.lst))
        self.ui.utc_label.setText(str(self.utc))
        self.lt = time.localtime()
        self.ui.local_time_label.setText(str(self.lt.tm_hour)+":"+str(self.lt.tm_min)+":"+str(self.lt.tm_sec))
        #send coordinates to compass to it can point toward positive ra and dec
        #self.make_compass(float(self.az))

    def update_remaining_time(self):
        try: self.timer_thread and self.timer_thread.isRunning()
        except AttributeError:
            self.ui.remaining_time_lcdNumber.display(self.ui.obs_time_spinBox.value())
        else:
            self.ui.remaining_time_lcdNumber.display(self.timer_thread.remaining_time)

    def update_status(self):
        self.set_telescope_status()

    def update_image(self):
        if self.image_time == self.exptime:
            pass
        else:
            self.display_image()
            if len(self.spectrum_pixel_x) != 0:
                if hasattr(self, 'image_time'):
                    self.display_timestream()
                #else:
            	    #print "'StartQt4' object has no attribute 'image_time'"
            #if self.image_thread.spectrum_pixel != None:
        	    #self.display_spectra()
            #self.update_remaining_time()

    def check_files(self):
        #if self.observing == True:
        self.binfile = str(self.bindir)+'/'+str(self.obsname)+'_'+str(self.image_time)+'.txt'
        #self.binfile = "/home/sean/ben/bin/obs_20110726-114310"+'_'+str(self.image_time)+'.npy'
        if self.debug == 1:
            self.make_image()
            self.debug =0

        if isfile(self.binfile):
            if not isfile(str(self.bindir) + '/lock.'+str(self.image_time)):
                self.make_image()


        #if isfile(str(self.bindir) + '/data.bin'):
            #statinfo = os.stat(str(self.bindir) + '/data.bin')
            #if self.stattime != statinfo.st_mtime:
                #self.start_image_thread()
                #self.stattime = statinfo.st_mtime

    def check_params(self):
        self.ui.tv_image.setGeometry(QRect(10, 10, 10*(self.nxpix)+4, 10*(self.nypix)+4))
        #self.ui.tv_image.setGeometry(QRect(10, 0, 450, 600))
        # temporary function to allow changing of array size and energy range without dialog and test that these params are passed properly to dataBin and dataSim
        # check if params have changed value using gui controls
        # self.data_thread.update_params(self.nxpix, self.nypix, self.Emin, self.Emax)
        # update values, pass new values to image thread, and write file with these new values to send to dataBin

    def closeEvent(self, event=None):
        #self.image_thread.__del__()
        if isfile(str(self.bindir)+"/lock.bin"):
            os.remove(str(self.bindir)+"/lock.bin")
        #if isfile(str(self.bindir)+"/data.bin"):
            #os.remove(str(self.bindir)+"/data.bin")
        #if isfile("TV_frame.bmp"):
            #os.remove("TV_frame.bmp")
        if isfile("Arcons_frame.png"):
            os.remove("Arcons_frame.png")

    def rearrange_frames(self):
        self.ui.frame_4.setGeometry(QtCore.QRect(390, 180, 25+10*self.nxpix, 25+10*self.nypix)) #pixel array frame
        #self.ui.frame_4.setGeometry(QtCore.QRect(390, 180, 200+10*self.nxpix, 150+10*self.nypix)) #pixel array frame
        self.ui.frame_5.setGeometry(QtCore.QRect(0, 190+20+10*self.nypix, 731, 241)) #pixel spectrograph frame
        self.ui.groupBox.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 10, 181, 191)) #pixel selection mode option
        self.ui.label_18.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 680, 46, 13)) #Dec
        self.ui.label_17.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 640, 46, 13)) #RA
        self.ui.RA_lineEdit.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 655, 113, 20))
        self.ui.Dec_lineEdit.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 695, 113, 20))
        self.ui.simple_imaging_radioButton.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 720, 211, 21))
        self.ui.label_26.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 610, 101, 17)) #testing junk
        self.ui.choose_beamimage.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 210, 171, 41))
        self.ui.choose_bindir.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 250, 171, 41))
        self.ui.brightpix.setGeometry(QtCore.QRect(430+20+10*self.nxpix, 300, 57, 25)) #number box for brightpix
        #self.ui.brightpix.setMaximum(self.nxpix*self.nypix)
        self.ui.label_22.setGeometry(QtCore.QRect(491+20+10*self.nxpix, 300, 91, 21))
        self.ui.takesky.setGeometry(QtCore.QRect(420+20+10*self.nxpix, 380, 171, 51))

    def get_xpix(self):
        return numXPixel
    def get_ypix(self):
        return numYPixel


#Data generation in dataSim.py and organization in dataBin.py, and image generation is in own thread that stays in this gui application.
#image_Worker retrieves and opens organized files, saves to local arrays, storing as cumulative arrays
#if we are in an observation, and makes quicklook images and spectra from these local arrays.
class image_Worker(QThread):
    def __init__(self, parent = None, nxpix=numXPixel, nypix=numYPixel, Emin=0.92, Emax=3.18):
        QThread.__init__(self, parent)
        self.nxpix = int(nxpix)
        self.nypix = int(nypix)
        self.Emin = Emin
        self.Emax = Emax
        self.total_pix = int(self.nxpix*self.nypix)
        self.exiting = False
        self.sky_subtraction = False #default is to have sky subtraction on
        self.color_on = False #default to generating images with color.
        self.spectrum_pixel = [] #pass pixel number by clicking desired pixel and will get spectra
        self.imaging = False #turns true when image thread is running
        self.simple_imaging = False
        self.pix_select_mode = "rect"
        self.plot_mode = "spectra"
        self.setup_thread()
    def setup_thread(self):
        self.SNR = [0,0,0,0,0,0,0,0,0,0]
        self.me = [0]*self.total_pix
        #Setup bin structure that will come from organize_data
        self.bintype = "wavelength" ###################  CHANGE SPECTRUM TYPE HERE   #########################
        if self.bintype == "energy":
            #break each pixel's photons into energy bins
            self.binmin = self.Emin
            self.binmax = self.Emax
        else:
            #default to wavelength bins for a traditional spectrum
            self.binmax = h*c/self.Emin
            self.binmin = h*c/self.Emax
        self.dE = (self.binmax-self.binmin)/10.
        self.E0 = self.binmin + self.dE/2.
        self.E1 = self.E0+self.dE
        self.E2 = self.E1+self.dE
        self.E3 = self.E2+self.dE
        self.E4 = self.E3+self.dE
        self.E5 = self.E4+self.dE
        self.E6 = self.E5+self.dE
        self.E7 = self.E6+self.dE
        self.E8 = self.E7+self.dE
        self.E9 = self.E8+self.dE
        self.pc = ndarray(self.total_pix, int)

    def update_params(self, nxpix, nypix, Emin, Emax):
        self.nxpix, self.nypix, self.Emin, self.Emax = nxpix, nypix, Emin, Emax
        self.setup_thread() #remake arrays for imaging
    def __del__(self):
        self.exiting = True
        self.wait()
    def unpack_file(self, file):
        f = open(file, 'rb')
        inputdata = f.read()
        f.close()
        numbers = struct.unpack(self.total_pix*'10I', inputdata)
        darray = reshape(numbers,(self.total_pix,10))
        return darray
    def subtract_sky(self, meds):
        '''Sky subtraction works by taking the median of counts over all pixels in every energy slice
        and subtracting that number from each pixel's count total.  Since there are generally 8 to 9 times more
        sky pixels than object pixels this median should come from a sky pixel and can be used as
        a good representation of sky counts at that energy'''
        #subtract each bins median values from each pixel in that bin
        self.C0[:] = [x-int(meds[0]) for x in self.C0]
        self.C1[:] = [x-int(meds[1]) for x in self.C1]
        self.C2[:] = [x-int(meds[2]) for x in self.C2]
        self.C3[:] = [x-int(meds[3]) for x in self.C3]
        self.C4[:] = [x-int(meds[4]) for x in self.C4]
        self.C5[:] = [x-int(meds[5]) for x in self.C5]
        self.C6[:] = [x-int(meds[6]) for x in self.C6]
        self.C7[:] = [x-int(meds[7]) for x in self.C7]
        self.C8[:] = [x-int(meds[8]) for x in self.C8]
        self.C9[:] = [x-int(meds[9]) for x in self.C9]
    def calc_mean_energy(self):
        for p in xrange(self.total_pix):
            self.me[p] = ((self.C0[p]*self.E0 + self.C1[p]*self.E1 + self.C2[p]*self.E2 + self.C3[p]*self.E3 \
                        + self.C4[p]*self.E4 + self.C5[p]*self.E5 + self.C6[p]*self.E6 + self.C7[p]*self.E7 \
                        + self.C8[p]*self.E8 + self.C9[p]*self.E9) /self.pc[p])
        if self.bintype == "wavelength":
            self.me[:] = [h*c/e for e in self.me]
    def calculate_SNR(self, totalcounts, medians, npix):
        total_signal = 0
        total_n = 0
        self.integrated_SNR = 0
        self.SNR = [0,0,0,0,0,0,0,0,0,0]
        for i in xrange(len(medians)):
            if self.sky_subtraction == True:
                signal = totalcounts[i]
                noise = npix*medians[i]
            else:
                signal = totalcounts[i]-npix*medians[i]
                noise = npix*medians[i]
            if signal < 0:
                signal = 0
            if noise == 0:
                noise = 1 #pretty much only happens when a bin has no photons in it at all
            total_signal += signal
            total_n += noise
            self.SNR[i] = signal/(sqrt(noise))
        self.integrated_SNR = total_signal/(sqrt(total_n))
    def make_spectrum(self, pixel, counts):
        bins = arange(self.binmin,self.E9,self.dE)
        self.emit(SIGNAL("new_spectrum"), pixel, bins, counts, self.integrated_SNR)
    def update_spectrum(self, bindir): #called when new data is not coming in but a new pixel is asked for
        self.bin_directory = bindir
        if not isfile(str(self.bin_directory) +"/lock.bin"):
            f=open(str(self.bin_directory)+"/lock.bin",'wb') #lock bin file so dataBin cannot access it
            f.close()
            binfile = str(self.bin_directory) + "/data.bin"
            darray = self.unpack_file(binfile)
            os.remove(str(self.bin_directory) + "/lock.bin") # unlock bin file
            self.C0=darray[:,0] #counts in 1st energy bin generated by organize_data
            self.C1=darray[:,1]
            self.C2=darray[:,2]
            self.C3=darray[:,3]
            self.C4=darray[:,4]
            self.C5=darray[:,5]
            self.C6=darray[:,6]
            self.C7=darray[:,7]
            self.C8=darray[:,8]
            self.C9=darray[:,9]
            #get median energy's for every bin for sky subtraction and SNR calculation
            self.medians = [median(self.C0),median(self.C1),median(self.C2),median(self.C3),median(self.C4),\
                        median(self.C5),median(self.C6),median(self.C7),median(self.C8),median(self.C9)]
            if self.sky_subtraction == True:
                self.subtract_sky(self.medians)
            if self.spectrum_pixel != []:
                totalcounts = [0,0,0,0,0,0,0,0,0,0]
                for p in self.spectrum_pixel:
                    counts = [self.C0[p],self.C1[p],self.C2[p],self.C3[p],self.C4[p],self.C5[p],self.C6[p],\
                            self.C7[p],self.C8[p],self.C9[p]]
                    for i in xrange(len(counts)):
                        totalcounts[i] += counts[i]
                #calculate SNR
                self.calculate_SNR(totalcounts, self.medians, len(self.spectrum_pixel))
                if self.plot_mode == "spectra":
                    self.make_spectrum(median(self.spectrum_pixel),totalcounts)
                else:
                    self.make_spectrum(median(self.spectrum_pixel),self.SNR)
                pylab.clf()
        else:
            #retry update spectrum
            print "lock in place on bin file, cannot make new spectrum"
            time.sleep(0.1)
            self.retry_spectrum(self.bin_directory)
    def retry_spectrum(self, bindir):
        self.update_spectrum(bindir)
    def set_spectrum_mode(self, mode):
        self.pix_select_mode = mode
        self.spectrum_pixel = []
        self.make_spectrum(0,[0,0,0,0,0,0,0,0,0,0])
    def set_plot_mode(self,mode):
        self.plot_mode = mode
        self.update_spectrum(self.bin_directory)
    def reset(self):
        self.pc = ndarray(self.total_pix, int)
        self.me = [0]*self.total_pix
    def start_images(self, bindir):
        self.bin_directory = bindir
        self.imaging = True
        self.start()
    def run(self):
        if not self.exiting:
            if not isfile(str(self.bin_directory)+"/lock.bin"):
                f=open(str(self.bin_directory)+"/lock.bin",'wb') #lock bin file so dataBin cannot access it
                f.close()
                datafile = str(self.bin_directory) + "/data.bin"
                #unpack file sent from organizer that has reorganized the raw data
                darray = self.unpack_file(datafile)
                os.remove(str(self.bin_directory)+"/lock.bin")
                #Break data into counts for energy slices 0-9
                self.C0=darray[:,0]
                self.C1=darray[:,1]
                self.C2=darray[:,2]
                self.C3=darray[:,3]
                self.C4=darray[:,4]
                self.C5=darray[:,5]
                self.C6=darray[:,6]
                self.C7=darray[:,7]
                self.C8=darray[:,8]
                self.C9=darray[:,9]

                #get median energy's for every bin for sky subtraction and SNR calculation
                self.medians = [median(self.C0),median(self.C1),median(self.C2),median(self.C3),median(self.C4),\
                            median(self.C5),median(self.C6),median(self.C7),median(self.C8),median(self.C9)]
                #do sky subtraction from these arrays of counts per pixel in each energy slice
                if self.sky_subtraction == True:
                    self.subtract_sky(self.medians)
                for m in xrange(self.total_pix):
                    self.pc[m]=self.C0[m]+self.C1[m]+self.C2[m]+self.C3[m]+self.C4[m]+self.C5[m]+self.C6[m]+\
                        self.C7[m]+self.C8[m]+self.C9[m]
                self.calc_mean_energy()
                if self.simple_imaging == False:
                    self.satpercent = 0.10 #default to 0.10
                    im = make_image_import(self.pc, self.me, self.color_on,self.satpercent)
                    im.save("TV_frame.bmp")
                else:
                    print "Reshaping image from ", shape(self.pc),
                    photon_count = array(self.pc)
                    photon_count = photon_count.reshape(32,32)
                    photon_count = flipud(photon_count)
                    print " to ", shape(photon_count)
                    fig = plt.figure(figsize=(.32,.32), dpi=100, frameon=False)
                    im = plt.figimage(photon_count, cmap='gray')
                    plt.savefig("TV_frame.png", pad_inches=0)
                if self.spectrum_pixel != []:
                    totalcounts = [0,0,0,0,0,0,0,0,0,0]
                    for p in self.spectrum_pixel:
                        counts = [self.C0[p],self.C1[p],self.C2[p],self.C3[p],self.C4[p],self.C5[p],self.C6[p],\
                                self.C7[p],self.C8[p],self.C9[p]]
                        for i in xrange(len(counts)):
                            totalcounts[i] += counts[i]
                    #calculate SNR
                    self.calculate_SNR(totalcounts, self.medians, len(self.spectrum_pixel))
                    if self.plot_mode == "spectra":
                        self.make_spectrum(median(self.spectrum_pixel),totalcounts)
                    else:
                        self.make_spectrum(median(self.spectrum_pixel),self.SNR)
                    pylab.clf()
                self.imaging = False
            else:
                print "lock is in place on bin file, cannot image"
                time.sleep(0.1)
                self.emit(SIGNAL("retry_image()"))

class timer_Worker(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.remaining_time = 0
        self.stopped = False
    def __del__(self):
        self.exiting = True
        self.wait()
    def stop(self):
        self.stopped = True
        self.remaining_time = 0
    def start_timer(self, starttime):
        self.starttime = starttime
        self.start()
    def run(self):
        self.stopped = False
        self.remaining_time = self.starttime
        t1 = time.time()
        t2 = time.time()
        while self.stopped == False and self.remaining_time > 0:
            t2 = time.time()
            self.remaining_time = self.starttime - (t2-t1)
            time.sleep(0.1)
        self.emit(SIGNAL("timeout()"))
        self.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = StartQt4()
    myapp.show()
    app.exec_()
