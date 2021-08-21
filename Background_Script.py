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
file_path = ''

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
            #TODO: Add finished observations to sql and config, synchronize with kapteyn
            # in the mornings send finished observations
            # in the evenings retrieve new config file 
            

            weather_pred = get_predicted_conditions(short = True) #Only retrieves sunset time
            logger.info('Sunset time retrieved as {}'.format(weather_pred['Sunset']..strftime('%H:%M:%S')))

            #Start script half to one hour before sunset
            if weather_pred['Sunset']-dt.timedelta(hours=1)<dt.datetime.now():
                logger.info('Waiting until 1 hour before sunset')
                time.sleep(dt.datetime.now()-(weather_pred['Sunset']-dt.timedelta(hours=1)).total_seconds()) #wait until 1 hour before sunset to set up
            #Copy config from kapteyn
            logger.info('Retrieving config and sql database')
            get_config()

            logger.info('Starting Scheduling')
            weather_pred = get_predicted_conditions(short = False)

            #Starts AutoHotkey Script opening all applications
            keyboard = Controller()
            keyboard.press('`') 
            logger.info('Triggered AHK script')

            objects = daily_Schedule(os.path.join(file_path,'Database.db'), 'Schedule')
            logger.info('Loaded database')

            #Create the schedule for the night
            objects, schedule = night_schedule(objects)
            logger.info('Created preliminary schedule')

            #Make plot of weather with obs times and save to plot folder
            if os.path.isdir(os.path.join(file_path,'plots')):
                make_plot(objects, schedule,weather_pred, pred_out = False, dir=os.path.join(file_path,'plots'))
            else:
                os.mkdir(os.path.join(file_path,'plots'))
                make_plot(objects, schedule,weather_pred, pred_out = False, dir=os.path.join(file_path,'plots'))
            logger.info('Saved Plot of observing schedule, with predicted conditions')
            
            #Creates file - #FIXME: Add relevant parameters to params
            create_ACP_scheudle(objects, schedule)
            logger.info('Created schedule for ACP')
            keyboard.press('-') #Start ahk script that loads config and starts observation
            logger.info('Triggered AHK script to load ACP schedule')

            if weather_pred['Sunrise']<dt.datetime.now():
                logger.info('Waiting until sunrise')
                (time.sleep(dt.datetime.now()-weather_pred['Sunrise'])).total_seconds()
            
            #Update config file and sql database
            update_config()
            #Send observing results to kapteyn
            send_results(file_path,remote_path)
            #TODO:Make sure to make back ups
            


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
        
