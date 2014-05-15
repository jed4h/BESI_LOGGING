# Program to collect data from a Shimmer3 over Bluetooth
# Can log data to a file locally and/or stream to a host PC
# The shimmer ID is sent from the basestation
# the basestation IP is a user input 
 


#!/usr/bin/env python
from gpio_utils import *
from ShimmerBT import *
from Constants import *
import NTPTime
import subprocess
import socket
import time
import csv
import struct
import sys


def shimmerSense(startDateTime, hostIP, BASE_PORT, ShimmerID, ShimmerID2, streaming = True, logging = True):
    streamingError = 0  # set to 1 if we lose connection while streaming

    server_address = (hostIP, BASE_PORT)
    startTimeDT = NTPTime.stripDateTime(startDateTime)
    accelFileName =  BASE_PATH+"Relay_Station{0}/Accelerometer/Accelerometer{1}.txt".format(BASE_PORT, startTimeDT)

    # records connect/disconnect events and times - not used
    ferror = open("error", "a")

    ShimmerIDs = []
    ShimmerIDs.append(SHIMMER_BASE + ShimmerID)
    ShimmerIDs.append(SHIMMER_BASE + ShimmerID2)

	

    ferror.write(startDateTime + "\n")
    with open(accelFileName, "w") as accelFile:
	accelFile.write(startDateTime+"\n")
	accelFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
	accelFile.write("Timestamp,X-Axis,Y-Axis,Z-Axis\n")
    
    startTime = datetime.datetime.now()

    # attempt to connect until successful
    while True:
	
	conn, s, connID = shimmer_connect(ShimmerIDs, PORT)
	if conn == 1:
		break
	else:
	    time.sleep(5)


    # give sensors some time to start up
    time.sleep(1)
    print "Connection Established to {}".format(connID)
    startDateTime = NTPTime.sendUpdate(server_address, 0, " Connected to {}".format(connID))

    # initialize variables used to convert Shimmer timestamps into seconds
    lastTime = 0
    startTick = -1
    numRollover = 0
    lastRelTime = -10000
    lastValidRelTime = -10000
    

    #startTime = datetime.datetime.now() 
    #ferror.write("Connection Established to {}. Time: {}\n".format(connID, datetime.datetime.now()-startTime))
           
    print "Sending Start Streaming Command"
    # try sending start streaming command 10 times
    streamingError = 1
    for attempt in range(10):
    	if (startStreaming(s) != -1):
	    streamingError = 0
	    break

    iterations = -1
    # find time since the start
    currTime = datetime.datetime.now()
    currTimeDelta = (currTime - startTime).days * 86400 + (currTime - startTime).seconds + (currTime - startTime).microseconds / 1000000.0
   
    while True:
	
	if iterations >= FILE_LENGTH:
			startDateTime = NTPTime.sendUpdate(server_address, iterations, " Accelerometer")
			iterations = -1
			# only start a new file when we get a timestamp from the base station
			if startDateTime != None:
				startTimeDT = NTPTime.stripDateTime(startDateTime)
				#startTimeDT = datetime.datetime.now()
				#accelFile.close()
				accelFileName = BASE_PATH+"Relay_Station{0}/Accelerometer/Accelerometer{1}.txt".format(BASE_PORT, startTimeDT)
			
				with open(accelFileName, "w") as accelFile:
					accelFile.write(startDateTime+"\n")
					accelFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
					accelFile.write("Timestamp,X-Axis,Y-Axis,Z-Axis\n")

				# reset variables for determining timestamps whenever we star a new file
				startTime = datetime.datetime.now()
				lastRelTime = -10000
				lastValidRelTime = -10000
				lastTime = 0
				startTick = -1				
				numRollover = 0

	elif (iterations % UPDATE_LENGTH) == (UPDATE_LENGTH - 2):
		if streamingError == 0:
			NTPTime.sendUpdate(server_address, UPDATE_LENGTH, " Accelerometer")
 
	iterations += 1

	# get time since the start on the first iteration
	if startTick == -1:
		currTime = datetime.datetime.now()
		currTimeDelta = (currTime - startTime).days * 86400 + (currTime - startTime).seconds + (currTime - startTime).microseconds / 1000000.0
		

	# if an exception is raised receiving data or connection is lost (streamingError == 1) try to reconnect
        try:
            if streamingError == 0:
                (timestamp, x_accel, y_accel, z_accel) = sampleAccel(s)
            else:
                raise socket.error
            # if the connection is lost: close the socket, create an new one and try to reconnect
        except socket.error:
	    if streamingError == 0:
		    # log every disconnect event in a file
		    ferror.write("Connection Lost from {}. Time: {}\n".format(connID, datetime.datetime.now()-startTime))
       		    startDateTime = NTPTime.sendUpdate(server_address, 0, " Disconnected from {}".format(connID))

            streamingError = 1
            try:
		s.close()
	    except:
		pass

            #attempt to reconnect
            conn, s, connID = shimmer_connect(ShimmerIDs, PORT)

	    if (conn == 1):
		print "Connection Est. to {}".format(connID)
                time.sleep(1)
		# log reconnect events to a file
    		ferror.write("Connection Re-established to {}. Time: {}\n".format(connID, datetime.datetime.now()-startTime))
		startDateTime = NTPTime.sendUpdate(server_address, 0, " Connected to {}".format(connID))

		
		lastTime = 0
		startTick = -1
		numRollover = 0
		lastRelTime = -10000
		lastValidRelTime = -10000
		
       
                print "Sending Start Streaming Command"
		for attempt in range(10):
		    if (startStreaming(s) != -1):
                	streamingError = 0
			break
            else:
                #print "Error Connecting to Shimmer"
		time.sleep(5)
		
	    currTime = datetime.datetime.now()
	    currTimeDelta = (currTime - startTime).days * 86400 + (currTime - startTime).seconds + (currTime - startTime).microseconds / 1000000.0
		
        else:
            #write accel values to a csv file
            
	    # get rssi for connectino to Shimmer
	    rssi_reading = subprocess.check_output(["hcitool","rssi","{}".format(connID)])
	    rssi_int = int(rssi_reading.split(":")[1].rstrip())	    

	    # print a message every 10 iterations
	    if iterations%10 == 0:
		print "sampling Accelerometer {} {}".format(connID, iterations)

            with open(accelFileName, "a") as accelFile:
                for i in range(len(z_accel)):
			relTime = timestamp[i]
			# valid data is between 0 and 4095 (inclusive)
			dataValid = ((int(x_accel[i]) < 4096) and (int(y_accel[i]) < 4096) and (int(z_accel[i]) < 4096))
			# a valid timestamp is a multiple of 256 ticks since the last timestamp
                	timestampValid = (int(relTime) - lastRelTime)%256 == 0
                	isValid = (dataValid and timestampValid) or (dataValid and startTick == -1) 
                	# assume every data point is valid - why?
			isValid = True
                	if isValid:
                    		if startTick == -1:
     	         	          	startTick = relTime
                        
                    	tickDiff = relTime - startTick
			# counter on the Shimmer rolls over to 0 every 2 seconds
                    	if relTime < lastValidRelTime:
                        	numRollover = numRollover + 1
                        	#print relTime, lastRelTime, lastTime

                        
                    	lastTime = 2*numRollover + 1.0/32768*tickDiff + 1.0/256
                    	if isValid:
                        	accelFile.write("{0:.5f},{1},{2},{3},{4}\n".format(float(lastTime) + currTimeDelta, x_accel[i], y_accel[i], z_accel[i], rssi_int))
                        	lastValidRelTime = relTime
                    	lastRelTime = relTime 
		  
        time.sleep(1)
		
def sendUpdateAccel(server_address, iterations, message = "accel samples"):
	updateSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	updateSock.settimeout(10)
	try:
		updateSock.connect(server_address)
		updateSock.sendall("{} ".format(iterations) + message)
		return updateSock.recv(1024)
	except:
		print "error updating base station"
	return	
