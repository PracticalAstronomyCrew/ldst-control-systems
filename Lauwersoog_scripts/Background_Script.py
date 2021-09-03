#!python
#!C:\Users\blaau\AppData\Local\Programs\Python\Python39

"""The purpose of this script is to be a constantly running background manager
It will be running 24/7 to control execution - Or find something in windows to schedule execution - methods seem flimsy however
"""

"""
Flat plan - dawn dusk
Bias, Dark - prior to Flat and after second flat


Auto Focus - prior to observing once per night

Check pointing direction


"""





import os
import sys
import time
import logging
import datetime as dt
from pynput.keyboard import Controller
import subprocess
from Scheduler import *
from data_transfer import *


file_path = os.path.abspath('C:\LDST')
remote_path = '/net/vega/data/users/observatory/LDST/'

if not os.path.isdir(os.path.join(file_path, 'logs')):
    os.mkdir(os.path.join(file_path, 'logs'))
logpath = os.path.join(file_path, 'logs') 
# Setting up logger
if not os.access(file_path, os.F_OK): 
    os.mkdir(file_path)
if not os.access(logpath, os.F_OK): 
    os.mkdir(logpath)

logger = logging.getLogger('main')
filename = '{}'.format(dt.date.today().strftime('%Y%m%d'))
full_filename = os.path.join(logpath, filename)
file_handler = logging.FileHandler(full_filename, mode='w')
formatter = logging.Formatter('%(asctime)s %(name) %(lineno)-10s %(levelname) %(message)')#'%(asctime)s %(name) - %(lineno)-10s %(levelname)-8s %(message)s')
file_handler.setFormatter(formatter)
#logger.addHandler(file_handler) TODO
logger.setLevel(logging.DEBUG)
time.sleep(2.0)
logger.debug('Logger is working')
passes = 0

#TODO: Filter names
#TODO: Logsheet naming: YYMMDD_LOGS.pdf first find where they are tho
#FIXME: It appears images are written with very odd permissions
if __name__ == '__main__':
    while True:
        try:
            #Connect to vpn
            os.chdir('C:\\Program Files\\NordVPN')

            subprocess.run(['./nordvpn','-c']) #TODO: Check if this ever finished execution

            #Move current config and database to backup folder
            #backup_config(file_path)
            #retrieve new config and database
            get_config_database(file_path, remote_path) #FIXME: In case no config is found use backup
            #Init of scheduling takes care of the whole process from script start to sun rise
            Scheduling(file_path,remote_path) 

        except (KeyboardInterrupt, Exception) as e:
            if e == KeyboardInterrupt:
                print('Program terminated early during scheduling, make sure to check if the configs have been modified yet!')
                logger.info('The program was interupted by a user, check that the configs are up to date!')
                sys.exit(0)
            else:
                print('There was an error in execution:\n', e)
                logger.warning('There was an error in execution: \n', e)
                passes += 1
                if passes >= 3:
                    pass
                else:
                    logger.warning('The program terminated 3 times, check most recent modifications!')
                    sys.exit(0)
                #MAke some kind of message with bot or so

        try:
            #Send observing results to kapteyn
            send_results(file_path,remote_path)
        
        except (KeyboardInterrupt, Exception) as e:
            if e == KeyboardInterrupt:
                print('Observational Results were not submitted to kapteyn, assure the config has been synced, and forward the observations results!')
                logger.info('The program was interupted by a user assure that the results are send to kapteyn')
                sys.exit(0)
            else:
                print('There was an error in execution:\n', e)
                logger.warning('There was an error in execution: \n', e)
                passes += 1
                if passes >= 3:
                    pass
                else:
                    logger.warning('The program terminated 3 times, check most recent modifications!')
                    sys.exit(0)
                #MAke some kind of message with bot or so
        



"""

File Handling Illustration

On kapteyn there is also .../LDST/approval for PID's which still need to be approved

The backup folder will not be the same on kapteyn and lauwersoog, kapteyn will keep backups of configs prior to adding PID's whereas Lauwersoog backups will contain the config files as returned by the previous nights observing 


.../LDST/
    ├── logs 
    │       └── YYYYMMDD         # Script Log from that date
    ├── logsheets  
    │       └── YYYYMMDD         # logsheet from that date TODO: check where they are actually written to
    ├── backups  
    │       ├── configs        
    │       │       └── ...
    │       ├── Databases
    │       │       └── ...
    │       ├── Schedules
    │       │       └── ...
    │       └── Interpolation_Data.csv
    │       
    ├── config
    │       ├── config           # Config containing PID's and obsIDs as short reference
    │       ├── config.ini       # Config containing the API key for openweather
    │       └── Database.db      # Database containing a record of all obsIDs and PIDs with all scheduling info
    ├── sky_bright
    │       └── Interp_dat.csv   # CSV file containing interpolation data for sky brightness, will be regularly refreshed
    ├── YYYYMMDD                 # Directory for date YYYY MM DD
    │       ├── PID              # Directory for PID (the number) containing all obsID's
    │       │    ├── obsID       # obsID (the number) directory with corresponding (possibly uncompleted observations)
    │       │    │       └── image.fits    #Image files belonging to obsID (including dark and bias)
    │       │    ├── obsID
    │       │    └── ...
    │       └── ...
    └── ...
"""