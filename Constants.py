
#Constants used in BBB BESI code
SHIMMER_BASE = "00:06:66:"	# first 3 bytes of every Shimmer's Bt address
PORT = 1                        # common to all shimmers
LIGHT_ADDR = 0x39               # i2c address of light sensor
LIGHT_REG_LOW = 0xAC            # address of low bits of light sensor channel 0
LIGHT_REG_HIGH = 0xAE           # address of low bits of light sensor channel 1
UPDATE_DELAY = 10               # number of loop iterations between reading light and temperature sensors
LOOP_DELAY = 0.1                # loop time in seconds
IS_STREAMING = True             # stream to base station 
IS_LOGGING = True               # log on Beaglebone
FILE_LENGTH = 60
UPDATE_LENGTH = 20
#BASE_PATH = "/media/card/"
BASE_PATH = "Data/"
USE_WEATHER = True

# BME 280 parameters
ctrl_hum = 0xF2
ctrl_meas = 0xF4

press_msb = 0xF7
press_lsb = 0xF8
press_xlsb = 0xF9

temp_msb = 0xFA
temp_lsb = 0xFB
temp_xlsb = 0xFC

hum_msb = 0xFD
hum_lsb = 0xFE

# 16 bit registers
T1 = 0x88
T2 = 0x8A
T3 = 0x8C

P1 = 0x8E
P2 = 0x90
P3 = 0x92
P4 = 0x94
P5 = 0x96
P6 = 0x98
P7 = 0x9A
P8 = 0x9C
P9 = 0x9E

H1 = 0xA1 # 8 bits
H2 = 0xE1 # 16
H3 = 0xE3 # 8
H4 = 0xE4
H5 = 0xE5
H6 = 0xE7 # 8?

P_data = 0xF7
T_data = 0xFA
H_data = 0xFD

start_cmd = 0b00100111
