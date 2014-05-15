from gpio_utils import *
from Constants import *
import NTPTime
import socket
import time
import csv
import subprocess
import sys


# gets sensor values from the temperature sensor and the microphone, writes the data to a file and sends the data over a socket
def soundSense(startDateTime, hostIP, BASE_PORT, streaming = True, logging = True):

    server_address = (hostIP, BASE_PORT)
    # use custom function because datetime.strptime fails in multithreaded applications
    startTimeDT = NTPTime.stripDateTime(startDateTime)
    audioFileName = BASE_PATH+"Relay_Station{0}/Audio/Audio{1}.txt".format(BASE_PORT, startTimeDT)
    doorFileName = BASE_PATH+"Relay_Station{0}/Door/Door{1}.txt".format(BASE_PORT, startTimeDT)
    tempFileName = BASE_PATH+"Relay_Station{0}/Temperature/Temperature{1}.txt".format(BASE_PORT, startTimeDT)
    
    
        
    # get the start time according to the BeagleBone. This time is only useful for detirmining time deltas
    
    with open(audioFileName, "w") as audioFile:
        audioFile.write(startDateTime+"\n")
	audioFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
	audioFile.write("Timestamp,Ambient Noise Level\n")
		
    with open(doorFileName, "w") as doorFile:
        doorFile.write(startDateTime+"\n")
	doorFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
	doorFile.write("Timestamp,Door Sensor Channel 1, Door Sensor Channel 2\n")
		
    with open(tempFileName, "w") as tempFile:
        tempFile.write(startDateTime+"\n")
	tempFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
	tempFile.write("Timestamp,Degree F\n")
		
    startTime = datetime.datetime.now()
	
    iterations = -1
    
    while True:
	
		if iterations >= FILE_LENGTH:
			startDateTime = NTPTime.sendUpdate(server_address, iterations, " ADC")
			iterations = -1
			
			if startDateTime != None:
				#startTimeDT = datetime.datetime.strptime(startDateTime.rstrip(), "%Y-%m-%d %H:%M:%S.%f")
				startTimeDT = NTPTime.stripDateTime(startDateTime)
				audioFile.close()
				doorFile.close()
				tempFile.close()
			
				audioFileName = BASE_PATH+"Relay_Station{0}/Audio/Audio{1}.txt".format(BASE_PORT, startTimeDT)
				doorFileName = BASE_PATH+"Relay_Station{0}/Door/Door{1}.txt".format(BASE_PORT, startTimeDT)
				tempFileName = BASE_PATH+"Relay_Station{0}/Temperature/Temperature{1}.txt".format(BASE_PORT, startTimeDT)
			
				with open(audioFileName, "w") as audioFile:
					audioFile.write(startDateTime+"\n")
					audioFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
					audioFile.write("Timestamp,Ambient Noise Level\n")
		
				with open(doorFileName, "w") as doorFile:
					doorFile.write(startDateTime+"\n")
					doorFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
					doorFile.write("Timestamp,Door Sensor Channel 1, Door Sensor Channel 2\n")
				
				with open(tempFileName, "w") as tempFile:
					tempFile.write(startDateTime+"\n")
					tempFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
					tempFile.write("Timestamp,Degree F\n")
				
				startTime = datetime.datetime.now()

		elif (iterations % UPDATE_LENGTH) == (UPDATE_LENGTH - 2):
			NTPTime.sendUpdate(server_address, UPDATE_LENGTH, " ADC")	

		iterations += 1
		
		# calculate the time since the start of the data collection
		currTime = datetime.datetime.now()
		currTimeDelta = (currTime - startTime).days * 86400 + (currTime - startTime).seconds + (currTime - startTime).microseconds / 1000000.0
			
		# run the c code to get one second of data from the ADC
		proc = subprocess.Popen(["./ADC1"], stdout=subprocess.PIPE,)
		# anything printed in ADC.c is captured in output
		output = proc.communicate()[0]
		split_output = output.split(',')
			
		# data is in <timestamp>,<value> format
		# 100 samples/second from the mic and 1 sample/sec from the temperature sensor
		i = 0 
		while (i < (len(split_output) / 2 - 1)):
		# every 11th sample is from the door sensor
			if (((i + 1) % 12) == 11):
				#doorFile.write(struct.pack("fff", float(split_output[2 * i]) + currTimeDelta, float(split_output[2 * i + 1]),float(split_output[2 * i + 3])) + "~~")
				with open(doorFileName, "a") as doorFile:
				    doorFile.write("{0:.2f},{1:.2f},{2:.2f}\n".format( float(split_output[2 * i]) + currTimeDelta, float(split_output[2 * i + 1]),float(split_output[2 * i + 3])))
				i = i + 1

			else:		
				#audioFile.write(struct.pack("ff", float(split_output[2 * i]) + currTimeDelta, float(split_output[2 * i + 1])) + "~~")
				with open(audioFileName, "a") as audioFile:
				    audioFile.write("{0:.2f},{1:.2f}\n".format(float(split_output[2 * i]) + currTimeDelta, float(split_output[2 * i + 1])))

			i = i + 1
			
		# send 1 semple from the temperature sensor
		try:
			(tempC, tempF) = calc_temp(float(split_output[-1]) * 1000)
		except:
			sys.exit()

		#tempSock.sendall("{0:0.4f},{1:03.2f},{2:03.2f},\n".format(float(split_output[-2]) + currTimeDelta, tempC, tempF))
		with open(tempFileName, "a") as tempFile:
		    tempFile.write("{0:0.4f},{1:03.2f},\n".format(float(split_output[-2]) + currTimeDelta, tempF))

def sendUpdateADC(server_address, iterations):
	updateSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	updateSock.settimeout(10)
	try:
	    updateSock.connect(server_address)
	    updateSock.sendall("{} ADC samples".format(iterations))
	    return updateSock.recv(1024)
	except:
	    print "error updating base station"

