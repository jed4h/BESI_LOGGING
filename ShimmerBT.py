# functions used to interface with the Shimmer3 over Bluetooth
# a full list of Bluetooth commands recognized by Shimmer can be obtained from the 
# Shimmer3 firmware code
# The commands used here are:
# start streaming = 0x07
# stop streaming = 0x20
# toggle red LED = 0x06
# request calib info = 0x13

import lightblue
import binascii
import struct
import datetime
import time
import socket as Socket
import subprocess

# accelerometer packet format in bytes is:
# 0  |  timestamp_low  |  timestamp_high  |  x_accel_low  |  x_accel_high ...


# use hcitool to scan for Bluetooth devices
# lightblue.finddevices does not show Shimmers
def BTScan():
    proc = subprocess.Popen(["hcitool","scan"], stdout=subprocess.PIPE)
    return proc.communicate()[0].split()


#connects to a shimmer with the given address
def shimmer_connect(addr, port):
    # scanning takes several seconds, so just try to connect without scanning
    deviceFound = 0
    #print "attempting to connect"
    # HDE Bluetooth dongle does not find shimmer, but can connect
    #devices = lightblue.finddevices()
  
   #for device in devices:
    #        if device[0] == addr:
     #           deviceFound = 1
    #discDevices = BTScan()
    
    for device in addr:
	#if device in discDevices:
	    address = device
	    deviceFound = 1
	    socket = lightblue.socket()
	    try:
	        socket.connect((address, port))
		print "successfully Connected to {}".format(address)
	        toggleLED(socket)
	        time.sleep(1)
	        toggleLED(socket)
	        socket.settimeout(0)    # make receive nonblocking
	        #print "successfully connected"
	        return 1, socket, address
	    except Socket.error as e:
	        print "failed to connect to",address,e
        
    #print "failed to find device"
    return 0, None, None
        
        
        
def startStreaming(socket):
    # recv sometimes gives EAGAIN error
    # if sending command fails, return an error code and try again
    try:
	socket.send("\x07")
    except Socket.error as e:
	print "Error Sending Start Streaming Comand",e
    	return -1
    else:
    	# short wait to prevent filling receiver buffer on Shimmer
    	time.sleep(0.5)
	# the expected response is 0xFF, but it usually is not after reconnecting
    	try:
    		if struct.unpack('B',socket.recv(1))[0] == 255:
        		print "Started Streaming..."
    		else:
			print "Started Streaming"
    	except Socket.error as e:
		print "Error reading ACK",e
		return -1
    	else:
		return 0
    
# not used. Streaming stops when the Bluetooth connection is broken
def stopStreaming(socket):
    socket.send("\x20")
    
# toggles the state of the red LED on The Shimmer
def toggleLED(socket):
    socket.send("\x06")
    
# reads 1 second of accelerometer data from the Bluetooth
#returns lists of timestamps and accel. data
def sampleAccel(socket):
    #print datetime.datetime.now()
    maxSize = 40960      #4000 / 256Hz sampling rate * 9 bytes/sample = 1.74 seconds of data
    start = 0
    timestamp = []
    x_accel = []
    y_accel = []
    z_accel = []
    
    # send ACK back to the Shimmer
    try:
	socket.send("\x21")
    except:
	print "error sending 0x21 to Shimmer"

    data = socket.recv(maxSize)
    sizeRecv = len(data)
    #print sizeRecv
    accel_tuple = struct.unpack('B'*sizeRecv, data)
    #print data
    #print accel_tuple
    
    # send 0x21 to the Shimmer to let it know that we are still connected
    #try:
	#socket.send("\x21")
    #except:
	#pass
 
    # data packets from the Shimmer are 9 bytes and start with 0 followed by 0 or 128
    # this might need to be changed for different sampling rates
    while True:
	# find the start of a packet
    	for i  in range(start,len(accel_tuple)):
       	    start = start + 1
	    try:
         	if (accel_tuple[i] == 0) and ((accel_tuple[i+1] == 0) or (accel_tuple[i+1] == 128)):
            	    break
	    except:
		break
	# less than a full packet of data
	if ((start + 8) > sizeRecv):
		break
        #print start

	for i in range(8):
	    # first 2 bytes are timestamp        
            if (i % 9) == 1:
                timestamp.append((accel_tuple[i + start]<< 8) + accel_tuple[i-1 + start]) 
	    # bytes 3 and 4 are x-axis
            if (i % 9) == 3:
               x_accel.append((accel_tuple[i + start]<< 8) + accel_tuple[i-1 + start])

            if (i % 9) == 5:
                y_accel.append((accel_tuple[i + start]<< 8) + accel_tuple[i-1 + start])

            if (i % 9) == 7:
                z_accel.append((accel_tuple[i + start]<< 8) + accel_tuple[i-1 + start])

        start = start + 8

    return timestamp, x_accel, y_accel, z_accel

# write one second of data to a csv file
def writeAccel(accelWriter, timestamp, x_accel, y_accel, z_accel):
    for value in range(len(z_accel)):
        accelWriter.writerow((timestamp[value], x_accel[value], y_accel[value], z_accel[value]))
        

# get the LNA calibration data from the shimmer
# calib message format is ACK | 0x12 | X Offset | Y Offset | Z Offset | X Sens | Y Sens | Z Sens | Alignment Matrix
# this program assumes allisgment is 1 0 0
#               	             0 1 0
#                       	     0 0 1
def readCalibInfo(socket):
    # the calibration message is 23 bytes
    messageLen = 23
    base = 0    #in some test cases an extra 0xff byte is read at the beginning
  
    time.sleep(0.5)
    socket.send("\x13")
    time.sleep(0.5) 
    data = socket.recv(messageLen)
    calib_tuple = struct.unpack('B'*messageLen, data)
    #switch endieness
    Xoff = (calib_tuple[2 + base] << 8) + calib_tuple[3 + base]
    Yoff = (calib_tuple[4 + base] << 8) + calib_tuple[5 + base]
    Zoff = (calib_tuple[6 + base] << 8) + calib_tuple[7 + base]
    
    Xsens = (calib_tuple[8 + base] << 8) + calib_tuple[9 + base]
    Ysens = (calib_tuple[10 + base] << 8) + calib_tuple[11 + base]
    Zsens = (calib_tuple[12 + base] << 8) + calib_tuple[13 + base]
    
    calib_info = LNACalib(Xoff, Yoff, Zoff, Xsens, Ysens, Zsens)
    return calib_info
    
class LNACalib:
    def __init__(self, Xoff = 0, Yoff = 0, Zoff = 0, Xsens = 0, Ysens = 0, Zsens = 0):
        self.Xoff = Xoff
        self.Yoff = Yoff
        self.Zoff = Zoff
        self.Xsens = Xsens
        self.Ysens = Ysens
        self.Zsens = Zsens
        
    def printCalib(self):
        print "X Offset: {0}".format(self.Xoff)
        print "Y Offset: {0}".format(self.Yoff)
        print "Z Offset: {0}".format(self.Zoff)
        print "X Sensitivity: {0}".format(self.Xsens)
        print "Y Sensitivity: {0}".format(self.Ysens)
        print "Z Sensitivity: {0}".format(self.Zsens)

"""       
SHIMMER_BASE = "00:06:66:66:"   # base bt address of Shimmer        
SHIMMER_ID = "94:A0"            # varies among shimmers        
s=lightblue.socket()
shimmer_connect(s, SHIMMER_BASE + SHIMMER_ID, 1)
calib = readCalibInfo(s)
calib.printCalib()
s.close()"""
