#!/bin/bash
# identifies the directory the current script is running in
SCRIPT_ROOT="$(dirname -- "$(readlink -f -- "$0")")"

#ROACHES=(0 1 2 3 4 5 6 7)
ROACHES=$MKID_ROACHES
CLK="512"
#BOF="chan_if_acc_x_2011_Aug_02_0713.bof" #Palomar 2011 firmware,has deadtime lockout bug, 3-pt trigger bug
#BOF="chan_dtrig_v2_2012_Aug_28_1956.bof" #Has short low pass filter baseline, plus Palomar 2011 bugs
#BOF="btrig_fix_v1_2012_Sep_06_1516.bof" *fixed deadtime lockout, longer low pass filter baseline
#BOF="chan_snap_v3_2012_Oct_30_1216.bof" #has snapQDR block for long snapshots, DDS lag: 154
#BOF="chan_snap_v3_2013_Oct_03_1412.bof" #has snapQDR block for long snapshots, DDS lag: 192
#BOF="chan_dead_v2_2013_Oct_07_1841.bof" #short dead time + count rate limiter, DDS lag: 194
#BOF="chan_smart_v0_2013_Nov_12_1137.bof" #has moving average baseline. DDS lag: 194
#BOF="chan_smart_v1_2013_Nov_13_1403.bof" #has moving average baseline block and strict trigger conditions. DDS lag: 194
#BOF="chan_smart_v2_2013_Nov_16_2141.bof" #has moving average baseline block and strict trigger conditions. Fixed bugs. DDS lag: 194
#BOF="chan_sm1_2013_Nov_26_2220.bof" #baseline threshold has on/off switch. added many snaps in capture. deadline bug fixed. DDS lag: 194

BOF=$BOFFILE     #uncomment this

# Sets the base of the IP address for the roach boards
# Is there a way to make this dynamic? - OC
IP_BASE_192="192.168.4.1"
IP_BASE_10="10.0.0.1"

# Sets the data readout directory
DATA_READOUT_DIR=${SCRIPT_ROOT}/DataReadout

# Sets the Channeliser Control directory
CHANNELIZER_CONTROLS_DIR=${DATA_READOUT_DIR}/ChannelizerControls



if [ "$1" == "--help" ]; then
	echo "Usage: $0 CLOCK_MHZ [BOF_FILE]"
	exit 0
fi
if [ $# -ge 1 ]; then
	BOF=$1
fi

if [ $# -eq 2 ]; then
	CLK=$2
fi

check_status()
{
    status=$?
    if [ $status -ne 0 ]; then
        echo ""
        echo "ERROR $1"
        exit $status
    fi  
    return 0
}

for i in ${ROACHES[*]}
do
    CURRENT_IP_192=${IP_BASE_192}${i}
    CURRENT_IP_10=${IP_BASE_10}${i}

    echo "Roach $i"
    echo -n "Killing running firmware ... "
	ssh root@${CURRENT_IP_192} "killall -q -r \.bof"
    sleep 2s
    echo " done"
    echo -n "Copying latest $BOF to roach ... "
	scp ${CHANNELIZER_CONTROLS_DIR}/boffiles/$BOF root@${CURRENT_IP_192}:/boffiles/
	check_status $i
    echo " done"
    echo -n "Setting clock rates to $CLK MHz ... "
	python ${CHANNELIZER_CONTROLS_DIR}/lib/clock_pll_setup_$CLK.py ${CURRENT_IP_192} > /dev/null
	check_status $i
    sleep 2s
    echo " done"
    echo -n "Programing firmware on roach ... "
	python ${CHANNELIZER_CONTROLS_DIR}/lib/program_fpga.py ${CURRENT_IP_192} $BOF > /dev/null
	check_status $i
    echo " done"
done

#if [ "$BOFFILE" == "chan_snap_v3_2012_Oct_30_1216.bof" ]; then
    #echo -n "Setting alpha registers ... "
    #python ${CHANNELIZER_CONTROLS_DIR}/lib/set_alpha.py
#fi
#if [ "$BOFFILE" == "chan_svf_2014_Aug_06_1839.bof" ]; then
    #echo -n "Setting svf baseline parameters ... "
    #python ${CHANNELIZER_CONTROLS_DIR}/lib/set_svf.py
#fi
check_status -1
echo "DONE"
