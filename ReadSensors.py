#!/usr/bin/env python
from gpio_utils import *
from ShimmerBT import *
from Constants import *
from TSL2561 import *
from Shimmer3 import *
from Mic import *
from BME280 import *
import socket
import time
import csv
import threading
import sys
import os

# get BS IP and RS port # from config file
fconfig = open("config")
for line in fconfig:
	if line[0] == "#":
            pass
        else:
            splitLine = line.split("=")
            try:
                if splitLine[0] == "BaseStation_IP":
                    BaseStation_IP2 = str(splitLine[1]).rstrip()
            except:
                print "Error reading IP Address"
            
            try:
                if splitLine[0] == "relayStation_ID":
                    relayStation_ID2 = int(splitLine[1])
            except:
                print "Error reading Port" 

default_settings = ''

# create local data folder - not needed if using SD card
if not os.path.exists("Data"):
	os.mkdir("Data")
# create data storage files
baseFolder = BASE_PATH+"Relay_Station{}/".format(relayStation_ID2)
if not os.path.exists(baseFolder):
	os.mkdir(baseFolder)
if not os.path.exists(baseFolder + "Accelerometer"):
	os.mkdir(baseFolder + "Accelerometer")
if not os.path.exists(baseFolder + "Temperature"):
	os.mkdir(baseFolder + "Temperature")
if not os.path.exists(baseFolder + "Light"):
	os.mkdir(baseFolder + "Light")
if not os.path.exists(baseFolder + "Audio"):
	os.mkdir(baseFolder + "Audio")
if not os.path.exists(baseFolder + "Door"):
	os.mkdir(baseFolder + "Door")
if not os.path.exists(baseFolder + "Weather"):
	os.mkdir(baseFolder + "Weather")

print ("Default Settings:")
print ("Base Station IP Address: {0}".format(BaseStation_IP2))
print ("Relay Station ID: {0}".format(relayStation_ID2))

while default_settings != ("Y") and default_settings != ("y") and default_settings != ("N") and default_settings != ("n"):
	default_settings = str(raw_input("Use Default Settings? (Y/N):"))


if (default_settings == "N" or default_settings == "n"):
	hostIP = str(raw_input("Enter the base station IP address: "))
	BASE_PORT = int(raw_input("Enter the relay station ID (port): "))
else:
	hostIP = BaseStation_IP2
	BASE_PORT = relayStation_ID2 

while True:
	# get the shimmerID and what sensors to use from the base station 
	# IS_STREAMING is always True
	if IS_STREAMING:
		synchSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address_synch = (hostIP, BASE_PORT)
		synchSock.settimeout(10)
		#print "connecting to %s port %s" % server_address_synch
		try:
			synchSock.connect(server_address_synch)
		except:
			print "connection to base station timed out"
			time.sleep(5)
			continue
		print "Connected to {} port {}".format(hostIP, BASE_PORT)	
		synchSock.settimeout(None)
		synchSock.sendall("starting up")		
		# receive info
		# get 3 byte length first
		msgLen = ''
		while (len(msgLen) != 3):
			try:
				msgLen = msgLen + synchSock.recv(3)
			except:
				pass

		msgLen = int(msgLen)
		data = ''    
		# call recv until we get all the data
		while (len(data) != msgLen):
			try:
				data = data + synchSock.recv(msgLen)
			except:
				pass
		# Base Station sends Shimmer BT IDs and start time
		splitData = data.split(",")
		SHIMMER_ID = splitData[0]
		SHIMMER_ID2 = splitData[1]
		startDateTime = splitData[2]
		USE_ACCEL = True
		USE_LIGHT = True
		USE_ADC = True

		#print startDateTime

		synchSock.close()

	ferror = open("error", "a")
	

	#stream to base station 
	if IS_STREAMING:

		if USE_ACCEL:
		    # create thread to handle interfacing with the Shimmer
		    accelThread = threading.Thread(target=shimmerSense, args=(startDateTime, hostIP, BASE_PORT,  SHIMMER_ID, SHIMMER_ID2, IS_STREAMING, IS_LOGGING))
		    # Thread will stop when parent is stopped
		    accelThread.setDaemon(True)
		   		

		if USE_LIGHT:
			lightThread = threading.Thread(target=lightSense, args=(startDateTime, hostIP, BASE_PORT, IS_STREAMING, IS_LOGGING))
			lightThread.setDaemon(True)
			
			
		if USE_ADC:
			# all sensors that use the ADC need to be managed by a single thread
			ADCThread = threading.Thread(target=soundSense, args = (startDateTime, hostIP, BASE_PORT, IS_STREAMING, IS_LOGGING))
			ADCThread.setDaemon(True)
		if USE_WEATHER:
			weatherThread = threading.Thread(target=weatherSense, args=(startDateTime,hostIP,BASE_PORT))
			weatherThread.setDaemon(True)


	# trap keyboard interrupt
	try:
		if USE_ACCEL:
			accelThread.start()
		if USE_LIGHT:
			lightThread.start()
		if USE_ADC:
			ADCThread.start()
		if USE_WEATHER:
			weatherThread.start()
		
		# wait until every thread exits (should never happen)
		if USE_ACCEL:
			accelThread.join()
		if USE_LIGHT:
			lightThread.join()
		if USE_ADC:
			ADCThread.join()
		if USE_WEATHER:
			weatherThread.join()
	
    
	except:
		print ""
		print "Exit"
