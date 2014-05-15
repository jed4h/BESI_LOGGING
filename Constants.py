# Default settings for this relay station (needs to be modified for each relay station/deployment)
BaseStation_IP = "172.25.203.183"
relayStation_ID = 9999

#Constants used in BBB BESI code
SHIMMER_BASE = "00:06:66:"   # base bt address of Shimmer        
SHIMMER_ID = "A0:5F:09"         # varies among shimmers - when streaming the ShimmerID is sent by the basestation
PORT = 1                        # common to all shimmers
LIGHT_ADDR = 0x39               # i2c address of light sensor
LIGHT_REG_LOW = 0xAC            # address of low bits of light sensor channel 0
LIGHT_REG_HIGH = 0xAE           # address of low bits of light sensor channel 1
UPDATE_DELAY = 10               # number of loop iterations between reading light and temperature sensors
LOOP_DELAY = 0.1                # loop time in seconds
IS_STREAMING = True             # stream to base station 
IS_LOGGING = True               # log on Beaglebone
FILE_LENGTH = 300
#BASE_PATH = "/media/card/"
BASE_PATH = "Data/"

# when streaming, which sensors to use is sent from the basestation
USE_ACCEL = True                # read data from Shimmer3
USE_LIGHT = True                # read data from light sensor
USE_ADC = True                  # read data from the ADC - temperature and microphone
