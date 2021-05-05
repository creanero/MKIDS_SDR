sudo /etc/init.d/dnsmasq start
sudo /etc/init.d/nfs-kernel-server start

#Start tcp borph server on MKIDS1
# Pretty sure next two lines don't work. But maybe they do
#ssh root@MKIDS1 "killall -q -r tcpborphserver"
#ssh root@MKIDS1 "tcpborphserver"

#telnet MKIDS1 7147 &

SCRIPT_ROOT=$(dirname "$(readlink -f "$0")")

source $SCRIPT_ROOT/fermi-bashrc
source $SCRIPT_ROOT/DataReadout/setEnvironment.sh
#source $SCRIPT_ROOT/DataReadout/ReadoutControls/startPulseServers.sh
source $SCRIPT_ROOT/DataReadout/ChannelizerControls/startSeqFirmware.sh
