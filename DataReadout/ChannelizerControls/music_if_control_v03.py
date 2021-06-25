#v01 First release, vor MUSIC_IF rev2 board (with adf4355 LO)
#v02 Added support for rev1 board (with ADF4350 LO)
#v03 Extended freq range of LO

#set which_rev to 1 for the rev1 board, anything else for the rev2 board
which_rev = 2
import time
import serial
import sys      #For checking python version
#run this under Python 2.x
assert sys.version_info < (3,0)

sleep_time = .1
debug_print = 0

def ser_slow(text):
    ser.write(text)
    time.sleep(sleep_time)
    
def Set_PLL4350(chan, freq, power, enable):
    print "Setting PLL Freq"
    if freq>4400: freq = 4400
    if freq<275: freq = 275
    div = int(2200/freq)
	#the div value can be 0 (divide by 1), 1 (by 2) or 2 (by 4) or 3 (by 8)
    if div >= 4: div = 3;
    elif div >= 2: div = 2;
    elif (div >= 1): div = 1;
    else: div = 0;
    freq = freq * (2**div)
    integer_part = int(freq/10.0)
    fractional_part = int(100*(freq - (integer_part * 10)))
    print integer_part, fractional_part, div
    #Send out a series of register values to the ADF4355 chip
    #Each register write consists of 36 bits; the MSnibble selects
    # which chip (1 for LO, 2 for CLK) is being written; the remaining
    # 32 bits are the data, the LS nibble being the register within the chip
  
    #reg 5
    ser_slow(chan + "00400005\r")
    #reg 4
    data = 0x8ff1c4 | (div<<20) | (enable << 5) | (power << 3)
    hex_data = hex(data)[2:]
    hex_data_padded = (8-len(hex_data))*'0' + hex_data
    if debug_print:
        print "reg4 val= " + chan + hex_data_padded
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data_padded + "\r")
    if debug_print:print ser.readline()          
    
    #reg 3
    ser_slow(chan + "000004B3\r")
    #reg 2, with MUX=3
    ser_slow(chan + "0c005EC2\r")   
    #reg 1
    ser_slow(chan + "08009f41\r")   
   
    #reg 0
    data = (integer_part<<15) | (fractional_part<<3)
    hex_data = hex(data)[2:]
    hex_data_padded = (8-len(hex_data))*'0' + hex_data
    if debug_print:
        print "reg0 val= " + chan + hex_data_padded
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data_padded + "\r")
    if debug_print: print ser.readline()          
 
    #reg 2 again, with MUX = 4
    ser_slow(chan + "10005EC2\r")   
 
def Set_PLL4355(chan, freq, power, enable):
    print "Setting PLL Freq"
    if freq>6800: freq=6800
    if freq<850: freq=850
    div = int(3400/freq)
	#the div value can be 0 (divide by 1), 1 (by 2) or 2 (by 4) or 3 (by 8)
    if div >= 4: div = 3;
    elif div >= 2: div = 2;
    elif (div >= 1): div = 1;
    else: div = 0;
    freq = freq * (2**div)
    integer_part = int(freq/5.0)
    fractional_part = int(((freq - 5.0 * integer_part)/5.0)*2**24)
    print "PLL values", freq, integer_part, fractional_part, div
    #Send out a series of register values to the ADF4355 chip
    #Each register write consists of 36 bits; the MSnibble selects
    # which chip (1 for LO, 2 for CLK) is being written; the remaining
    # 32 bits are the data, the LS nibble being the register within the chip
    
    #send reg12 value
    ser_slow(chan + "0001041C\r")
    #reg 11
    ser_slow(chan + "0061300B\r")
    #reg 10
    ser_slow(chan + "060C017FA\r")
    #reg 9
    ser_slow(chan + "03027CC9\r")
    #reg 8
    ser_slow(chan + "102D0428\r")
    #reg 7
    ser_slow(chan + "12000007\r")
    
    #reg 6- Need to form data word
    data= 0x35002406 | (div<<21) | (enable<<6) | (power<<4)
    hex_data = hex(data)
    if debug_print:
        print "reg6 val = " + chan + hex_data[2:]
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data[2:] + "\r")
    if debug_print:print ser.readline()          
    
    #reg 5
    ser_slow(chan + "00800025\r")
    #reg 4
    ser_slow(chan + "32008B84\r")
    #reg 3
    ser_slow(chan + "00000003\r")
    #reg 2
    ser_slow(chan + "00000052\r")
    
    #reg 1
    data = (fractional_part<<4) | 1
    #convert to hex and strip off leading 0x
    hex_data = hex(data)[2:]
    #need to pad this to 8 characters
    hex_data_padded = (8-len(hex_data))*'0' + hex_data
    #and strip off the 0x, and add the leading chan character
    if debug_print:
        print "reg1 val= " + chan + hex_data_padded
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data_padded + "\r")
    if debug_print: print ser.readline()          
    
    #reg 0
    data = 0x00200000 | (integer_part<<4)
    hex_data = hex(data)[2:]
    hex_data_padded = (8-len(hex_data))*'0' + hex_data
    if debug_print:
        print "reg0 val= " + chan + hex_data_padded
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data_padded + "\r")
    if debug_print:print ser.readline()          
 
def Set_Attens(A0, A1, A2):
    print "Setting Attens"
    if A0>31.5: A0=31.5
    if A0<0: A0=0
    if A1>31.5: A1=31.5
    if A1<0: A1=0
    if A2>31.5: A2=31.5
    if A2<0: A2=0
    A0=31.5-A0
    A1=31.5-A1
    A2=31.5-A2
    A0 = int(A0*2)
    A1 = int(A1*2)
    A2 = int(A2*2)
    chan = '3'
    data = A0<<26 | A1<<20 | A2<<14
    hex_data = hex(data)[2:]
    hex_data_padded = (8-len(hex_data))*'0' + hex_data
    if debug_print:
        print "atten reg value = " + chan + hex_data_padded
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data_padded + "\r")
    if debug_print:print ser.readline()          
   
    
def Set_Switches():
    print "Setting Switches"
    chan = '0'
    data = (not Ext_CLK)<<4 | BB_Loop<<3 | (not LO_doubler)<<2 | (not RF_Loop)<<1 | Ext_LO 
    data = data<<27
    hex_data = hex(data)[2:]
    hex_data_padded = (8-len(hex_data))*'0' + hex_data
    if debug_print:
        print "switch value= " + chan + hex_data_padded
        time.sleep(sleep_time)
        ser.reset_input_buffer()
    ser_slow(chan + hex_data_padded + "\r")
    if debug_print:print ser.readline()          

##########################################################    
##########################################################    
##########################################################    
#Variables to keep track of hardware state
LO_freq = 3000.0
CLK_freq = 600.0
Atten0 = 0
Atten1 = 0
Atten2 = 0
BB_Loop = False
RF_Loop = False
Ext_LO = False
Ext_CLK = False
#Added this for the rev1 board LO freq doubler
LO_doubler = False

#constants for the PLL divider and rfpower
LO_power = 3    #3 is max
CLK_power = 2   

print "MUSIC IF Control"
try:
    ser = serial.Serial('COM4', 9600)
except:
    print "Check Serial Port Connection"
    quit()
print("Serial port used: " + ser.name)         # check which port was really used
n=0
while n<10:
    a = ser.readline()
    print a
    if a.startswith("ard_hi"): 
        ser_slow("h")
        break
    time.sleep(sleep_time)
    n=n+1
    
#Dump anything in the receive buffer   
ser.reset_input_buffer()

#initialize everything
if which_rev == 1:
    Set_PLL4350('1', LO_freq, LO_power, 1)
else: Set_PLL4355('1', LO_freq, LO_power, 1)
Set_PLL4350('2',  CLK_freq, CLK_power, 1)
Set_Attens(Atten0, Atten1, Atten2)
Set_Switches()

#while True:
#    Set_PLL4355('1', LO_div, LO_freq, LO_power, 1)
#    time.sleep(3)
    
while True:
    print "LO Freq = ", LO_freq
    print "Clk Freq = ", CLK_freq
    print "Atten0 = ", Atten0
    print "Atten1 = ", Atten1
    print "Atten2 = ", Atten2
    print "RF_Loop = ", RF_Loop
    print "BB_Loop = ", BB_Loop
    print "Ext_LO = ", Ext_LO
    print "Ext_CLK = ", Ext_CLK
    if which_rev == 1:
        print "LO_doubler = ", LO_doubler
    

    print "Select one of the following"
    if which_rev == 1:
        print "1. Set LO Freq (MHz, 550 to 4400)"
    else: print "1. Set LO Freq (MHz, 850 to 6800)"
    print "2. Set CLK Freq (MHz, 550 to 1100)"
    print "3. Set Attenuator RFin (dB, 0 to 31.5)"
    print "4. Set Attenuator RFout1 (dB, 0 to 31.5)"
    print "5. Set Attenuator RFout2 (dB, 0 to 31.5)"
    print "6. Toggle BB Loopback"
    print "7. Toggle RF Loopback"
    print "8. Toggle External LO"
    print "9. Toggle External Clock"
    if which_rev == 1:
        print "10. Toggle LO freq doubler"
    
    print "q. Quit \n\r"

    inp = raw_input("Your Choice:  ")
    if inp == 'q':
        ser.close()
        quit()
    if inp =='1': 
        inp = raw_input("Enter new LO Freq (MHz), '0' to disable  ")
        if inp == '0':
            if which_rev == 1:
                Set_PLL4350('1', LO_freq, LO_power, 0)
            else: Set_PLL4355('1', LO_freq, LO_power, 0)
            LO_freq = 0.0
        else:
            LO_freq = float(inp)
            if which_rev == 1:
                Set_PLL4350('1', LO_freq, LO_power, 1)
            else: Set_PLL4355('1', LO_freq, LO_power, 1)
        continue
    if inp =='2': 
        inp = raw_input("Enter new CLK Freq (MHz), '0' to disable  ")
        if inp == '0':
            Set_PLL4350('2', CLK_freq, CLK_power, 0)
            CLK_freq = 0.0
        else:
            CLK_freq = float(inp)
            Set_PLL4350('2',  CLK_freq, CLK_power, 1)
        continue        
    if inp =='3': 
        inp = raw_input("Enter new Atten0 Setting (0-31.5)  ")
        Atten0 = float(inp)
        Set_Attens(Atten0, Atten1, Atten2)
        continue
    if inp =='4': 
        inp = raw_input("Enter new Atten1 Setting (0-31.5)  ")
        Atten1 = float(inp)
        Set_Attens(Atten0, Atten1, Atten2)
        continue
    if inp =='5': 
        inp = raw_input("Enter new Atten2 Setting (0-31.5)  ")
        Atten2 = float(inp)
        Set_Attens(Atten0, Atten1, Atten2)
        continue
    if inp =='6': 
        BB_Loop = not BB_Loop
        Set_Switches()
        continue
    if inp =='7': 
        RF_Loop = not RF_Loop
        Set_Switches()
        continue
    if inp =='8': 
        Ext_LO = not Ext_LO
        Set_Switches()
        continue
    if inp =='9': 
        Ext_CLK = not Ext_CLK
        Set_Switches()
        continue
    if inp == '10':
        LO_doubler = not LO_doubler
        Set_Switches()

    # data = "123456789\r"
    # ser.write(data)     # write a string
    # time.sleep(1)
    # line = ser.readline()          
    # print line       

     
ser.close()
quit()

