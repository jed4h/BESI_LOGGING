#code to interface with the TSL2561 ambient light sensor over i2c
# continuously samples lux semsor and writes result to given can write
from gpio_utils import *
from Constants import *
import NTPTime
import time
import csv
import struct
import sys
import socket

def lightSense(startDateTime, hostIP, BASE_PORT,  streaming=True, logging=True):
    server_address = (hostIP, BASE_PORT)
    startTimeDT = NTPTime.stripDateTime(startDateTime)
    lightFileName = BASE_PATH+"Relay_Station{0}/Light/Light{1}.txt".format(BASE_PORT, startTimeDT)

    
    light_i2c = i2c_light_init(LIGHT_ADDR)

        
    with open(lightFileName, "w") as lightFile:
        lightFile.write(startDateTime+"\n")
	lightFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
	lightFile.write("Timestamp,Lux\n")
		
    startTime = datetime.datetime.now()

    iterations = -1

    while True:
		if iterations >= FILE_LENGTH:
			startDateTime = NTPTime.sendUpdate(server_address, iterations," light samples", 5)
			iterations = -1
				
			if startDateTime != None:
				startTimeDT = NTPTime.stripDateTime(startDateTime)
				#startTimeDT = datetime.datetime.now()
			
				lightFileName = BASE_PATH+"Relay_Station{0}/Light/Light{1}.txt".format(BASE_PORT, startTimeDT)
				with open(lightFileName, "w") as lightFile:
			    		lightFile.write(startDateTime+"\n")
			    		lightFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
			    		lightFile.write("Timestamp,Lux\n")
				
				startTime = datetime.datetime.now()
		
		elif (iterations % UPDATE_LENGTH) == (UPDATE_LENGTH - 2):
			NTPTime.sendUpdate(server_address, UPDATE_LENGTH, " light samples", 5)


		iterations += 1

		# calculate time since start
		currTime = datetime.datetime.now()
		currTimeDelta = (currTime - startTime).days * 86400 + (currTime - startTime).seconds + (currTime - startTime).microseconds / 1000000.0
		# read light sensor
		# error reading i2c bus. Try to reinitialize sensor
		lightLevel = lux_calc(light_i2c.readU16(LIGHT_REG_LOW), light_i2c.readU16(LIGHT_REG_HIGH))
		if lightLevel == -1:
			light_i2c = i2c_light_init(LIGHT_ADDR)
		
		#if logging:      
			#lightWriter.writerow(("{0:.2f}".format(currTimeDelta), "{0:.2f}".format(lightLevel)))
			
		with open(lightFileName, "a") as lightFile:
			lightFile.write("{0:.2f},{1:.2f},\n".format(currTimeDelta, lightLevel))

		time.sleep(LOOP_DELAY * UPDATE_DELAY)

def sendUpdateLight(server_address, iterations):
	updateSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	updateSock.settimeout(10)
	try:
		updateSock.connect(server_address)
		updateSock.sendall("{} light samples".format(iterations))
		return updateSock.recv(1024)
	except:
		print "error updating base station"
	return
