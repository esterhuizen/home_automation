import os
import subprocess
import glob
import time
import datetime
import pymongo
from pymongo import MongoClient
import urllib2
import sys
import json
import pprint
 
os.system('/sbin/modprobe w1-gpio')
os.system('/sbin/modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
 
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
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
        return temp_c
        

def get_response(url):
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError:
        return None
    return json.loads(response.read())


# Do metservice lookups

url = 'http://metservice.com/publicData/oneMinObs_auckland'
res = get_response(url)
layers = res['clothingLayers']
outTemp = res['temperature']
feelsLike = res['windChill']
windSpeed = res['windSpeed']

# Grab our connection information from the MONGOHQ_URL environment variable
# (mongodb://linus.mongohq.com:10045 -u username -pmy_password)
MONGO_URL = os.environ.get('MONGOHQ_URL')
#connection = Connection(MONGO_URL)
#client = MongoClient(MONGO_URL)
client = MongoClient('mongodb://script:Mymongo12@troup.mongohq.com:10035/home_automation')

# Specify the database
db = client.home_automation
# Print a list of collections
# print db.collection_names()

# Specify the collection
collection = db.loungeTemp

piTemps = subprocess.check_output('/usr/local/bin/get_temp.sh')
[ cpuT, gpuT ] = piTemps.strip().split(',')

reading = {"lounge_temp": read_temp(),
            "cpu_temp": float(cpuT),
            "gpu_temp": float(gpuT),
            "layers": float(layers),
            "outTemp": float(outTemp),
            "feelsLike": float(feelsLike),
            "windSpeed": float(windSpeed),
           "date": datetime.datetime.now()
                                 }

# Insert the monster document into the monsters collection
temp_id = collection.insert(reading)

collection = db.piTemp

piReading = {"cpu_temp": cpuT,
            "gpu_temp": gpuT,
           "date": datetime.datetime.now()
                                 }

temp_id = collection.insert(piReading)

