#!/bin/bash
#setEnvironment.sh
#Sets environment variables used in data readout gui's
#Run before templarCustom.py,ArconsDashboard.py,etc. or have ~/.bashrc or ~/.bash_profile run it

##Variables used by ArconsDashboard

# The directory where obs files will be saved
export MKID_DATA_DIR=$HOME/data/$(date +%Y%m%d)
# The path to the beammap h5 file, identifying frequencies with pixel locations for each readout unit (roach board)
export BEAMMAP_PATH=$SCRIPT_ROOT/data/common/sorted_beamimage46x44.h5
# A file to store the current state of the filter wheel
export FILTER_WHEEL_PATH=$SCRIPT_ROOT/DataReadout/ReadoutControls/bin/filter.txt
# A file to store the current state of the calibration mirror arm
export MIRROR_ANGLE_PATH=$SCRIPT_ROOT/DataReadout/ReadoutControls/bin/mirror.txt
#The filename of the current compiled firmware.  Should be stored in SDR/DataReadout/ChannelizerControls/boffiles/
export BOFFILE=pulse_trigger_2022_Jan_24_1322.bof
#The git commit of the model file for the boffile above
export FIRMWARE_COMMIT=75f17828098b0d3c57acf07f9b3188b39794f666

##Variables used by templar 

#The delay in the firmware between reading the dds values from dram and using them (Determined by which firmware is listed above).
export DDS_LAG=154
#boolean switch to indicate whether the current firmware makes use of a threshold in computing baseline phase
export B_BASE_THRESH=0
# The directory where the current frequency/attenuation files are stored (EX: ps_freq0.txt). Also where roachConfig.txt is.
#export FREQ_PATH=~/opt/software/colin1/LUT
export FREQ_PATH=$SCRIPT_ROOT/DataReadout/ChannelizerControls/LUT
##Variables used by channelizerCustom

# filename(s) of FIR coefficients to be loaded into firmware.  
#Use %d in place of roach number to have a different file for each roach
export CUSTOM_FIR=matched_30us.txt
#Default phase level for photon triggering
export THRESHOLD_LEVEL=2.1

##Variables added to help port to new hardware configurations
export MKID_NROW=46
export MKID_NCOL=44
export MKID_TELESCOPE=Broida
