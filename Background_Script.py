#!/bin/python3

"""The purpose of this script is to be a constantly running background manager
It will be running 24/7 to control execution - Or find something in windows to schedule execution - methods seem flimsy however
"""
file_path = r'C:/LDST/YYMMDD/' #TODO:
remote_path = r'/net/vega/data/users/observatory/LDST/YYMMDD/' #TODO:


filters = 

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

from Scheduler import *
from data_transfer import *


logpath = os.path.join(maindatapath, 'log') #TODO: CHange
file_path = 'C:\LDST'
remote_path = '/net/vega/data/users/observatory/LDST/YYMMDD/'

# Setting up logger
if not os.access(file_path, os.F_OK): 
    os.mkdir(file_path)
if not os.access(logpath, os.F_OK): 
    os.mkdir(logpath)

logger = logging.getLogger('main')
filename = 'Exec_log_{}'.format(dt.date.today().strftime('%d_%m_%Y'))
full_filename = os.path.join(logpath, filename)
file_handler = logging.FileHandler(full_filename, mode='w')
formatter = logging.Formatter('%(asctime)s %(name) - %(lineno) -10s %(levelname)-8s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
time.sleep(2.0)
logger.debug('Logger is working')
passes = 0
#Set starting time for first execution
if __name__ == '__main__':
    while True:
        try:
            #TODO: Make backups and retrieve config+database from kapteyn
            
            #Init of scheduling takes care of the whole process from script start to sun rise
            Scheduling(os.path.join(file_path)) 

            #Send observing results to kapteyn
            send_results(file_path,remote_path)
            
            


        except (KeyboardInterrupt, Exception) as e:
            if e == KeyboardInterrupt:
                print('Program terminated, remember to restart this script once you are done!')
                logger.info('The program was interupted by a user, remember to restart it!')
                sys.exit(0)
            else:
                print('There was an error in execution:\n', e)
                logger.warning('There was an error in execution: \n', e)
                passes += 1
                if passes => 3:
                    pass
                else:
                    logger.warning('The program terminated 3 times, check most recent modifications!')
                    sys.exit(0)
                #MAke some kind of message with bot or so

            #TODO: Add another exception for early termination due to other things and send email or so
        
