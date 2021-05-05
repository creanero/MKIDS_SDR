sudo /etc/init.d/dnsmasq start
sudo /etc/init.d/nfs-kernel-server start

#Start tcp borph server on MKIDS1
# Pretty sure next two lines don't work. But maybe they do
#ssh root@MKIDS1 "killall -q -r tcpborphserver"
#ssh root@MKIDS1 "tcpborphserver"

#telnet MKIDS1 7147 &

source ~/Desktop/SDR-master/fermi-bashrc
source ~/Desktop/SDR-master/DataReadout/setEnvironment.sh
#source ~/Desktop/SDR-master/DataReadout/ReadoutControls/startPulseServers.sh
source ~/Desktop/SDR-master/DataReadout/ChannelizerControls/startSeqFirmware.sh
