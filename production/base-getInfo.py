# NOTE: All <<ItemsToBeReplaced>>

import os
import glob
import sys
import re
import time
import subprocess
import MySQLdb as mdb 
import datetime
# Adding in library for the Adafruit BMP085 Chipset
import Adafruit_BMP.BMP085 as BMP085

# Adding libraries for Weather Undersground Processing
from urllib import urlencode
import urllib2
 
# Database Setup
databaseUsername="root" #YOUR MYSQL USERNAME, USUALLY ROOT
databasePassword="<<MySQLPswd>>" #YOUR MYSQL PASSWORD 
databaseName="WordPressDB" #do not change unless you named the Wordpress database with some other name

# Start Weather Underground Setup
WU_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
wu_station_id = "<<WUStationID>>"  #Your Weather Station ID
wu_station_key = "<<WUStationKey>>"   #Your Weather Station Key
# End Weather Underground Setup

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Default contructor for the I2C Bus for the BMP085 Sensor
sensor = BMP085.BMP085()
# If you want to override the default bus number, comment out the above line and use this one instead:
#sensor = BMP085.BMP085(busnum=2)

def sendToWU(temperature,pressure):  #To send data to Weather Underground
                                              
        print('Uploading Weather to WU')
        # Build weather data object
        weather_data = {
            "action": "updateraw",
            "ID": wu_station_id,
            "PASSWORD": wu_station_key,
            "dateutc": "now",
            "tempf": str(temperature),
            "baromin": str(pressure),
        }
        try:
            upload_url = (WU_URL + "?" + urlencode(weather_data))
            response = urllib2.urlopen(upload_url)
            html = response.read()
            print('Server Response: ', html)
            response.close()  #close the file
        except:
            print('Exception: ', sys.exec_info()[0], SLASH_N)



def saveToDatabase(temperature,humidity,pressure):

	con=mdb.connect("localhost", databaseUsername, databasePassword, databaseName)
        currentDate=datetime.datetime.now().date()

        now=datetime.datetime.now()
        midnight=datetime.datetime.combine(now.date(),datetime.time())
        minutes=((now-midnight).seconds)/60 #minutes after midnight, use datead$


        with con:
                cur=con.cursor()

                cur.execute("INSERT INTO temperatures (temperature, humidity, pressure, dateMeasured, hourMeasured) VALUES (%s,%s,%s,%s,%s)",(temperature,humidity,pressure,currentDate, minutes))

		print "****** DATA SAVED ******"
		return "true"



def read_temp_raw():
	catdata = subprocess.Popen(['cat',device_file], 
	stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out,err = catdata.communicate()
	out_decode = out.decode('utf-8')
	lines = out_decode.split('\n')
	return lines

 
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
#        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c#, temp_f
	


#check if table is created or if we need to create one
try:
	queryFile=file("createTable.sql","r")

	con=mdb.connect("localhost", databaseUsername,databasePassword,databaseName)
        currentDate=datetime.datetime.now().date()

        with con:
		line=queryFile.readline()
		query=""
		while(line!=""):
			query+=line
			line=queryFile.readline()

		cur=con.cursor()
		cur.execute(query)	

        	#now rename the file, because we do not need to recreate the table everytime this script is run
		queryFile.close()
        	os.rename("createTable.sql","createTable.sql.bkp")


except IOError:
	pass #table has already been created


#gather data
Temp = read_temp()
TempF = Temp * 1.8 + 32
Hum = 'NULL'
BMPPres = sensor.read_pressure()
ATMPressure = BMPPres * 0.000009869 #convert Pascal Units to ATM
BMPTempC = sensor.read_temperature()
BMPTempF = BMPTempC * 1.8 + 32
BMPAlt = sensor.read_altitude()
BMPSeaPres = sensor.read_sealevel_pressure()

# outbound data

#saveToDatabase(read_temp(),'Null',sensor.read_pressure())
saveToDatabase(Temp,Hum,ATMPressure)
sendToWU(TempF,ATMPressure)


#whole lotta visual checks
print('Temp = {0:0.2f} *C'.format(Temp))
print('BMP Temp = {0:0.2f} *C'.format(BMPTempC))
print('BMP Temp = {0:0.1f} *F'.format(BMPTempF))
print('BMP Pressure = {0:0.02f} Pa'.format(BMPPres))
print('ATM Pressure = {0:0.02f} ATM'.format(ATMPressure))
print('BMP Altitutde = {0:0.2f} m'.format(BMPAlt))
print('BMP Sealevel Pressure = {0:0.02f} Pa'.format(BMPSeaPres))


