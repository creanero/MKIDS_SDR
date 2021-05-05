import corr, time, sys

ip = root@192.168.4.10
bof = chan_snap_v3_2012_Oct_30_1216.bof

print "opening client and programming "+ip+"..."
roach = corr.katcp_wrapper.FpgaClient(ip, 7147)
time.sleep(1)

print "and programming "
roach.progdev(bof)
time.sleep(1.5)
print "done"


