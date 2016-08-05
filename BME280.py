# code to read data from the BME teperature/humidity/pressure sensor
# assumes the sensor is connected to I2C bus 2 (pins 17 and 18)
# formulas and register addresses are fromthe BME 280 datasheet

from gpio_utils import *
from Constants import *
import NTPTime
import time
import csv
import struct
import sys
import socket
import ctypes
import subprocess


# calibration values set at manufacture time
class BME280Calib:
	def __init__(self, i2c):
		self.c_T1 = i2c.readU16(T1)
		self.c_T2 = ctypes.c_int16(i2c.readS16(T2)).value
		self.c_T3 = ctypes.c_int16(i2c.readS16(T3)).value

		self.c_P1 = i2c.readU16(P1)
		self.c_P2 = ctypes.c_int16(i2c.readS16(P2)).value
		self.c_P3 = ctypes.c_int16(i2c.readS16(P3)).value
		self.c_P4 = ctypes.c_int16(i2c.readS16(P4)).value
		self.c_P5 = ctypes.c_int16(i2c.readS16(P5)).value
		self.c_P6 = ctypes.c_int16(i2c.readS16(P6)).value
		self.c_P7 = ctypes.c_int16(i2c.readS16(P6)).value
		self.c_P8 = ctypes.c_int16(i2c.readS16(P8)).value
		self.c_P9 = ctypes.c_int16(i2c.readS16(P9)).value

		self.c_H1 = i2c.readU8(H1)
		self.c_H2 = ctypes.c_int16(i2c.readS16(H2)).value
		self.c_H3 = i2c.readU8(H3)
		self.c_H4 = ctypes.c_int16((i2c.readU8(H4) << 4) | (i2c.readU8(H4 + 1) & 0x0F)).value
		self.c_H5 = ctypes.c_int16((i2c.readU8(H5+1) << 4) | (i2c.readU8(H5) >> 4)).value
		self.c_H6 = i2c.readS8(H6)

# activates sensors and sets oversample rate to 1x (not sure what that means)
def BME280Init(i2cAddr, i2cBus):
	i2c = Adafruit_I2C(i2cAddr,i2cBus)
	i2c.write8(ctrl_hum, 0x1)
	i2c.write8(ctrl_meas, start_cmd)
	return i2c

# returs temperature in C and t_fine (used for other sensors)
def readTemp(i2c, calib):
	# measure temperature
	adc_T = (i2c.readU8(T_data) << 12) | (i2c.readU8(T_data + 1) << 4) | (i2c.readU8(T_data + 2) >> 4)
	var1 = ((((adc_T>>3) - (calib.c_T1<<1)))*(calib.c_T2)) >> 11
	var2 = (((((adc_T>>4)-(calib.c_T1))*((adc_T>>4)-(calib.c_T1))) >> 12)*(calib.c_T3)) >> 14
	t_fine = var1 + var2
	return ((t_fine*5 + 128) >> 8)/100.0, t_fine
	
# returns ressure in Pa
def readPressure(i2c, calib, t_fine):
	# measure pressure
	adc_P = (i2c.readU8(P_data) << 12) | (i2c.readU8(P_data + 1) << 4) | (i2c.readU8(P_data + 2) >> 4)
	var1 = t_fine - 128000
	var2 = var1*var1*calib.c_P6
	var2 = var2 + ((var1*calib.c_P5)<<17)
	var2 = var2 + ((calib.c_P4) << 35)
	var1 = ((var1*var1*calib.c_P3)>>8) + ((var1*calib.c_P2)<<12)
	var1 = ((((1)<<47)+var1))*(calib.c_P1)>>33
	P = 1048576 - adc_P
	P = (((P<<31) - var2)*3125)/var1
	var1 = ((calib.c_P9)*(P>>13)*(P>>13))>>25
	var2 = ((calib.c_P8)*P)>>19
	P = ((P + var1 + var2) >> 8) + ((calib.c_P7)<<4)
	return (P/256.)

# returns humitity in % relative humidity	
def readHumidity(i2c, calib, t_fine):
	# measure humidity
	adc_H = (i2c.readU8(H_data) << 8) | (i2c.readU8(H_data + 1))
	var1 = t_fine - 76800
	var1 = (((((adc_H << 14) - ((calib.c_H4) << 20) - ((calib.c_H5)*var1))+(16384)) >> 15) * 
		(((((((var1 * (calib.c_H6)) >> 10) * (((var1 * (calib.c_H3)) >> 11) + (32768))) >> 10)
		+ (2097152)) * (calib.c_H2) + 8192) >> 14))
	var1 = (var1 - (((((var1 >> 15) * (var1 >> 15)) >> 7) *
					 (calib.c_H1)) >> 4))

	return (var1>>12)/1024.0

# reads weather data and stores in a local file
def weatherSense(startDateTime, hostIP, BASE_PORT, streaming=True, logging=True):
    i2c = BME280Init(0x77, 2)
    calib = BME280Calib(i2c)
	
	
    server_address = (hostIP, BASE_PORT)
    startTimeDT = NTPTime.stripDateTime(startDateTime)
    weatherFileName = BASE_PATH+"Relay_Station{0}/Weather/Weather{1}.txt".format(BASE_PORT, startTimeDT)
        
    with open(weatherFileName, "w") as weatherFile:
        	weatherFile.write(startDateTime+"\n")
		weatherFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
		weatherFile.write("Timestamp,Temperature,Pressure,Humidity\n")
		
    startTime = datetime.datetime.now()
    iterations = -1

    while True:
		if iterations >= FILE_LENGTH:
			startDateTime = NTPTime.sendUpdate(server_address, iterations," weather samples", 5)
			iterations = -1
				
			if startDateTime != None:
				startTimeDT = NTPTime.stripDateTime(startDateTime)
				#startTimeDT = datetime.datetime.now()
			
				weatherFileName = BASE_PATH+"Relay_Station{0}/Weather/weather{1}.txt".format(BASE_PORT, startTimeDT)
				with open(weatherFileName, "w") as weatherFile:
			    		weatherFile.write(startDateTime+"\n")
					weatherFile.write("Deployment ID: Unknown, Relay Station ID: {}\n".format(BASE_PORT))
					weatherFile.write("Timestamp,Temperature,Pressure,Humidity\n")
				
				startTime = datetime.datetime.now()
		
		elif (iterations % UPDATE_LENGTH) == (UPDATE_LENGTH - 2):
			NTPTime.sendUpdate(server_address, UPDATE_LENGTH, " weather samples", 5)


		iterations += 1

		# calculate time since start
		currTime = datetime.datetime.now()
		currTimeDelta = (currTime - startTime).days * 86400 + (currTime - startTime).seconds + (currTime - startTime).microseconds / 1000000.0
		# read light sensor
		# error reading i2c bus. Try to reinitialize sensor
		(temp,t_fine) = readTemp(i2c, calib)
		pressure = readPressure(i2c, calib, t_fine)
		humidity = readHumidity(i2c, calib, t_fine)
					
		with open(weatherFileName, "a") as weatherFile:
			weatherFile.write("{0:.2f},{1:.2f},{2:.2f},{3:.2f},\n".format(currTimeDelta, temp, pressure, humidity))

		time.sleep(LOOP_DELAY * UPDATE_DELAY)	


#print datetime.datetime.now()
#weatherSense(str(datetime.datetime.now()), "0.0.0.0", 9999)		
