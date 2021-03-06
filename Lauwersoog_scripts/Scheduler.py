#!python
#!C:\Users\blaau\AppData\Local\Programs\Python\Python39

#Astropy and astroplan related stuff
from astropy import constants
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.coordinates as coord
import astropy.units as u
from astropy.time import Time
from astroplan.scheduling import PriorityScheduler, Schedule, TransitionBlock, Transitioner
from astroplan import ObservingBlock, FixedTarget, Observer
from astroplan import AltitudeConstraint,AtNightConstraint,MoonIlluminationConstraint, AirmassConstraint
from Helper_funcs import RainConstraint, SkyBrightnessConstraint, SeeingConstraint
from astroplan.plots import plot_schedule_airmass
import sys


#python native modules
import sqlite3
import requests
import datetime as dt
import csv
import os
import matplotlib.pyplot as plt
import numpy as np
import logging
import time

import matplotlib.pyplot as plt

from pynput.keyboard import Controller

from Helper_funcs import sqlite_retrieve_table, dprint, create_new_interpolation_dataset
from data_transfer import update_config_after_run

from requests.exceptions import ConnectionError
#Boilerplate logging
logger = logging.getLogger('main.scheduler')
logger.debug("starting scheduler logger")




class Scheduling:
    #Defining general parameters for the telescope, all the parameters outside of class functions will be assigned to the self parameter
    
    #   Telescope specifics
    filters = ['B*', 'G*', 'R*', 'H_alpha', 'None']
    # Filter transition rate
    ftr = {'filter':{   ('Lum, B*'): 10*u.second,
                        ('B*','G*'): 10*u.second,
                        ('G*','R*'): 10*u.second,
                        ('R*','H_alpha'): 10*u.second,
                        ('H_alpha','Filter 16'): 10*u.second,
                        ('Filter 16','B*'): 10*u.second}} #TODO: Change rates
    read_out_time = 20*u.second
    slew_rate = .8*u.deg/u.second
    location = EarthLocation(53.3845258962902, 6.23475766593151)
    observer = Observer(location=location)
    #Global constraints 
    twilight = AtNightConstraint.twilight_civil()
    altitude = AltitudeConstraint(min=10*u.deg, max=90*u.deg,boolean_constraint = True)#TODO: Check min height
    global_constraints = [twilight, altitude]


    def __init__(self, file_path):
        """Starts pipeline scheduling execution"""
        logger.info('Getting Weather data')
        while True:
            try:
                self.get_predicted_conditions(short=True)
                break
            except Exception as e:
                if e == ConnectionError:
                    logger.warning('API key didn`t return data, trying again (we can make 1000 API calls/day and 60 calls/min), however this error should not occure')
                    pass
                else:
                    logger.warning('Unrecognized error while retrieving weather data, trying again: ', e)
                    pass
        
        if os.path.isfile(os.path.join(file_path, 'sky_bright', 'Interpolation_Data.csv')):
            logger.info('Interpolation data present')
        else: 
            logger.warning('No interpolation data present')
            if os.path.isfile(os.path.join(file_path, 'backups', 'Interpolation_Data.csv')):
                logger.info('Found Interpolation Data backup, copying to sky_bright')
                file_cont = open(os.path.join(file_path, 'backups', 'Interpolation_Data.csv')).readlines()
                writer = csv.writer(open(os.path.join(file_path,'sky_bright', 'Interpolation_Data.csv'), 'w'))
                for row in file_cont:
                    writer.writerow(row)
            else:
                logger.warning('No backup found either, check what happened! Creating new set')
                create_new_interpolation_dataset('./sky_bright')
            logger.warning('Interpolation data retrieved')
        
        logger.info('Predicted sunset at {}, script will continue at {}'.format(self.sunset, self.sunset-dt.timedelta(hours=1)))
        
        if self.sunset > dt.datetime.now():
            time_to_sleep = ((self.sunset-dt.timedelta(hours=1))-dt.datetime.now()).total_seconds()
            if time_to_sleep <= 0:
                logger.warning('Script did not wait, check why execution started late!')
            else:
                time.sleep(1) #Sleeps until an hour to sunset #TODO: Replace 1 with time_to_sleep
        else:
            logger.warning('The script reached execution after Sunset! Late start of Observation')
        
        logger.info('Starting applications using AutoHotkeyScript')
        self.file_path = file_path

        keyboard = Controller()
        keyboard.press('`') 
        logger.info('Triggered AHK script')

        logger.info('Retrieving weather data')

        self.weather_cond = self.get_predicted_conditions()

        logger.info('Creating priority ordered list')

        self.priority_ordered_list = self.daily_Schedule(os.path.join(file_path,'config', 'Database.db'), 'Schedule')
        
        self.scheduled_blocks = self.create_priority_schedule() 

        logger.info('Created Schedule')

        logger.info('Creating ACP scheduler text file')
        #The below creates the ACP text file, and assigns directories to each obsID (all of which also get created)
        self.create_ACP_scheudle()

        logger.info('Created ACP schedule')
        keyboard.press('-') #TODO:
        logger.info('Loaded schedule into ACP')
        
        if self.weather_cond['Sunrise']<dt.datetime.now():
            logger.info('Waiting until sunrise')
            time.sleep((dt.datetime.now()-self.weather_cond['Sunrise']).total_seconds())
        else:
            logger.warning('Script finished execution after sunrise!!')
        
        update_config_after_run(self.file_path)
        

    def get_predicted_conditions(self,short=False):
        """ 
        Retrieves Data from OpenWeatherMap.org using API key 
        """
        location = (53.3845258962902, 6.23475766593151)
        api_key='52695aff81b7b6e5708ab0e924b859f2'
        url= "http://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=[current,minutely,alerts]&appid={}".format(*location, api_key)
        weather = requests.get(url).json()
        if not short:
            keys = ['Temperature', 'Pressure', 'Humidity', 'Dew_Point', 'Cloud_cover', 'Visibility', 'Wind_Speed','Wind_direction','Rain_Prob']
            key_return = ['temp','pressure','humidity','dew_point','clouds','visibility','wind_speed','wind_deg','pop']
            weather_cond = {keys[i]:[weather['hourly'][j][key_return[i]] for j in range(len(weather['hourly']))] for i in range(len(keys))}
            weather_cond['Time']=[dt.datetime.utcfromtimestamp(i['dt']) for i in weather['hourly']]
            weather_cond['Moon']=weather['daily'][0]['moon_phase']
            weather_cond['Sunset']=dt.datetime.utcfromtimestamp(weather['daily'][0]['sunset'])
            self.sunset = weather_cond['Sunset']
            weather_cond['Sunrise']=dt.datetime.utcfromtimestamp(weather['daily'][1]['sunrise'])
            self.sunrise = weather_cond['Sunrise']
            return weather_cond
        if short:
            self.sunset = dt.datetime.utcfromtimestamp(weather['daily'][1]['sunrise'])
            return 0


    def daily_Schedule(self,database, table):
        """
        Creates schedule every day prior to observing
        ---------
        database --> str: sqlite database
        table --> str: table name containing objects to be observed    
        """
        connect = sqlite3.connect(database)
        content = sqlite_retrieve_table(connect, table)
        for i in content: 
            i = assign_priority(i) 
        content = sorted(content, key=lambda k: k['priority'], reverse=True)
        return content

    
    def create_priority_schedule(self, save_plot=False):
        """Uses astroplan priority scheduler to assign observation"""
        blocks = []
        #Enumerate obsID's according to sorted priorities as astroplan takes priority 1 to be highest
        for priority, image in enumerate(self.priority_ordered_list):
            #obsID so that the order of obsID's can later be used
            config = {'filter':image['Filter'], 'obsID':image['obsID']} 
            #Determining constraints
            constraints = [RainConstraint(weather=self.weather_cond)]
            if image['airmass'] != None:
                constraints.append(AirmassConstraint(max=image['airmass']))
            if image['moon']!=None:
                constraints.append(MoonIlluminationConstraint(max=image['moon']))
            if image['twilight']!=None:
                if image['twilight']=='astronomical':
                    constraints.append(AtNightConstraint.twilight_astronomical())
                elif image['twilight']=='nautical':
                    constraints.append(AtNightConstraint.twilight_nautical())
                elif image['twilight']=='civil':
                    pass
                else:
                    logger.warning('Twilight {} not recognized for obsID {}'.format(image['twilight'], config['obsID']))
            if image['seeing']!=None and 0==1:#TODO: remove 0==1 to get seeing to work
                constraints.append(SeeingConstraint(max=image['seeing']))
            if image['sky_brightness']!=None:
                constraints.append(SkyBrightnessConstraint(weather=self.weather_cond,min=image['sky_brightness']))

            b = ObservingBlock.from_exposures(target=FixedTarget.from_name(image['object']), priority=priority, time_per_exposure=image['exposure']*u.second,number_exposures=image['number_of_exposures'], readout_time=self.read_out_time,configuration=config,constraints=constraints)
            blocks.append(b)

        transitioner = Transitioner(self.slew_rate,self.ftr)

        self.scheduler = PriorityScheduler(constraints = self.global_constraints, observer=self.observer, transitioner=transitioner)

        self.priority_schedule = Schedule(Time(self.weather_cond['Sunset']),Time(self.weather_cond['Sunrise']))
        if len(blocks)>0:
            self.schedule = self.scheduler(blocks, self.priority_schedule)
            #Append extra observations without conditions to free spots of scheduler
            #self.create_extra_obs() #TODO: Remove hashtag
        else:
            logger.warning('There are no observations to be scheduled in the database!')
            self.create_extra_obs(error=True)

        if save_plot:
            plt.figure(figsize = (14,6))
            plot_schedule_airmass(self.priority_schedule)
            plt.legend(loc = "upper right")
            if not os.path.isdir(os.path.join(self.file_path, 'plots')):
                os.mkdir(os.path.join(self.file_path, 'plots'))
            plt.savefig(os.path.join(self.file_path, 'plots', dt.date.today().strftime('%Y%m%d')+'.png'))
        if hasattr(self, 'schedule'):
            return self.schedule.scheduled_blocks
        else:
            logger.critical('No Observations were Scheduled, please check the execution Log, script will now terminate!')
            sys.exit(0)

    def create_extra_obs(self,error=False):
        if not error:
            free_time = 0
            for i in self.schedule.open_slots:
                time = i.duration.to_value(u.second)
                if time > 600: #If more than 10 minutes free try to schedule something with no min conditions
                    free_time+=time
            if not free_time > 0:
                return 0
        #TODO: Retrieve x slots to fill the time frame, constraints are set in ObservingBlock, check that error is covered
        from .Extra_obs import get_observations
        to_append = get_observations()
        
        blocks = []
        priority = 100 #start at low priority so nothing else gets overriden
        for i in to_append:#TODO: All below
            config = {'filter':i['Filter'], 'tempID':i['tempID']} 
            b = ObservingBlock.from_exposures(target=FixedTarget.from_name(image['object']), priority=priority, time_per_exposure=image['exposure']*u.second,number_exposures=image['number_of_exposures'], readout_time=self.read_out_time,configuration=config)
            blocks.append(b)
            priority+=1
        if len(blocks)>0: #Throws an error if passed an empty list
            if not error:
                self.scheduler(blocks, self.priority_schedule)
            if error:
                self.schedule = self.scheduler(blocks, self.priority_schedule)
        else:
            logger.info('No extra observations added')
        self.extra_blocks = blocks
        


    def create_ACP_scheudle(self):
        """
        Creates ACP text file
        And directories for image files
        ---------
        objects --> dict as returned by night_schedule
        """
        #Create file header 
        nr_of_observations = len(self.scheduled_blocks)
        header = ';\n; --------------------------------------------\n; This plan was generated by the automated python script 4.2.6\n; --------------------------------------------\n;\n; For:           jacobus\n; Targets:       {}\n;\n; NOTE:          Timing features are disabled\n;\n; Autofocus at start of run.\n;\n; ---------------------------------------------\n;\n'.format(nr_of_observations)
        #Dusk Flat
        header += '#duskflats Schedule_flat_{}.txt  ; Acquire flat fields at dusk\n;\n#autofocus\n;\n'.format(dt.date.today().strftime('%Y%m%d'))
        #We will also take care of the residual file handling here
        im_path = os.path.join(self.file_path, dt.date.today().strftime('%Y%m%d'))
        #Calibration directory
        if not os.path.isdir(im_path):
            os.mkdir(im_path)
        if not os.path.isdir(os.path.join(im_path, 'calibration')):
            os.mkdir(os.path.join(im_path, 'calibration'))
        header += self.entry_layout(params=None,imdir=im_path,cal_st=True,cal_end=False)
        if not os.path.isdir(im_path):
            os.mkdir(os.path.join(im_path))
        else:
            logger.warning('Image directory for todays run already existed!')
        # add seperate ID for observations not based on uni
        for i in self.scheduled_blocks:
            if type(i)==TransitionBlock:
                continue
            if 'obsID' in i.configuration.keys(): #The configuration given to the scheduler
                for j in self.priority_ordered_list: #Iterate through list and find correct obsid, should be one of the first few as it is ordered according to priority already
                    if i.configuration['obsID'] == j['obsID']: 
                        params = {}
                        params['catalogue_name'] = i.target.name
                        params['Filter'] = i.configuration['filter']
                        params['count'] = str(i.number_exposures)
                        params['repeat'] = '1' 
                        params['interval'] = i.time_per_exposure.value
                        params['binning'] = j['binning'] 
                        params['PID'] = j['PID']
                        params['ObsID'] = i.configuration['obsID']
                        PID_path = os.path.join(im_path, str(params['PID']))
                        if not os.path.isdir(PID_path):
                            os.mkdir(PID_path)
                        ObsID_path = os.path.join(PID_path, str(params['ObsID']))
                        if not os.path.isdir(ObsID_path):
                            os.mkdir(ObsID_path)
                        else:
                            logger.warning('ObsID {} Image directory for todays run already existed!'.format(params['ObsID']))
                        header+=self.entry_layout(params=params,imdir=ObsID_path)
                        break #Break j loop
            elif 'tempID' in i.configuration:
                for j in self.extra_blocks: #Iterate through list and find correct obsid, should be one of the first few as it is ordered according to priority already
                    if i.configuration['tempID'] == j['tempID']: 
                        params = {}
                        params['catalogue_name'] = i.target.name
                        params['Filter'] = i.configuration['filter']
                        params['count'] = str(i.number_exposures)
                        params['repeat'] = '1' 
                        params['interval'] = i.time_per_exposure.value
                        params['binning'] = '1'
                        params['tempID'] = i.configuration['tempID']
                        extra_obs_path = os.path.join(im_path, 'extra_obs')
                        if not os.path.isdir(extra_obs_path):
                            os.mkdir(extra_obs_path)
                        tempID_path = os.path.join(extra_obs_path, str(params['tempID']))
                        if not os.path.isdir(tempID_path):
                            os.mkdir(tempID_path)
                        else:
                            logger.warning('tempID {} Image directory for todays run already existed!'.format(params['ObsID']))
                        header+=self.entry_layout(params=params,imdir=tempID_path)
                        break #Break j loop
            else:
                logger.warning('Could not append observation {}'.format(i.configuration))
        #Add calibration
        header += self.entry_layout(params=None,imdir=im_path,cal_st=False,cal_end=True)
        #Dawn Flat
        header += '#dawnflats Schedule_flat_{}.txt  ; Acquire flat fields at dawn\n;\n;\n'.format(dt.date.today().strftime('%Y%m%d'))

        #End File
        header += ';\n; END OF PLAN\n;\n;'
        #Write schedule to backup path
        with open(os.path.join(self.file_path,'backups', 'Schedules','Schedule_{}.txt'.format(dt.date.today().strftime('%Y%m%d'))),'w') as file:
            file.write(header)
        with open(os.path.join(self.file_path,'Schedule.txt'),'w') as file:
            file.write(header)
        #FIXME: Change naming of filters as is appropriate
        flat = '; ---------------------------------------------\n; ACP Auto-Flat Plan - Generated by Python Script\n; ---------------------------------------------\n;\n; For:      jacobus\n; At:       07:50:01\n; From:     Schedule_{}.txt\n; Flats:    16\n;\n; Lines are count,filter,binning (comma-separated)\n; Empty filter uses ACP-configured clear filter\n; ---------------------------------------------------\n;\n5,Luminance,1\n5,R*,1\n5,G*,1\n5,B*,1\n;\n; ----------------\n; END OF FLAT PLAN\n; ----------------\n;'.format(dt.date.today().strftime('%Y%m%d'))

        with open(os.path.join(self.file_path,'backups', 'Schedules','Schedule_flat_{}.txt'.format(dt.date.today().strftime('%Y%m%d'))),'w') as file:
            file.write(flat)
        with open(os.path.join(self.file_path,'Schedule_flat.txt'),'w') as file:
            file.write(flat)
    
    def entry_layout(self,params=None,imdir=None,cal_st=False,cal_end=False):
        """Returns string formated for ACP planner plan text file""" 
        entry = ''
        if cal_st: #Calibration at start
            file_path = os.path.join(imdir, 'calibration')
            entry+='; === Target Bias (21@bin1) ===\n;\n#dir {}\n#repeat 1\n#count 21\n#interval 0\n#binning 1\n#bias\n#dir\n;'.format(file_path)
            entry='; === Target Dark (5x300sec@bin1) ===\n;\n#dir {}\n#repeat 1\n#count 1\n#interval 300\n#binning 1\n#dark\n#dir\n;'.format(file_path)
        elif cal_end: #Calibration at end
            file_path = os.path.join(imdir, 'calibration')
            entry='; === Target Dark (5x300sec@bin1) ===\n;\n#dir {}\n#repeat 1\n#count 1\n#interval 300\n#binning 1\n#dark\n#dir\n;'.format(file_path)
            entry+='; === Target Bias (21@bin1) ===\n;\n#dir {}\n#repeat 1\n#count 21\n#interval 0\n#binning 1\n#bias\n#dir\n;'.format(file_path)
        else:
            entry += '; === Target {} ===\n;\n'.format(params['catalogue_name'])
            entry += '; WARNING: Folder path is not portable.\n#dir {}    ; Images forced to go into this folder\n'.format(os.path.abspath(imdir))
            entry +=  '#repeat {}\n'.format(params['repeat'])
            entry += '#count {}\n'.format(params['count'])
            entry += '#filter {}\n'.format(params['Filter'])
            entry += '#interval {}\n'.format(params['interval'])
            entry += '#binning {}\n'.format(params['binning'])
            entry += '{}\n'.format(params['catalogue_name'])
            entry += '#dir    ; Revert to default images folder\n;\n'
        return entry


def assign_priority(obj): #FIXME: Adapt values
    """
    Packaging function for daily_Schedule
    ----------
    dictionary --> dict: containing all scheduling parameters for one schedule
    today --> datetime: object containing todays date
    """
    #Base variable onto which is added
    priority = 0
    #Checking if time sensitive
    if obj['time_sensitive'] == 'Yes':
        priority += 10
    #Checking who created the querry
    observer_dict =  {'Moderator':10, 'OA':1, 'Staff':0.5,'Student (Thesis)':0.4,'Student(Thesis)':0.4,'Student': 0.3,'Outreach/schools':0.2,'Public':0.1}
    for key in observer_dict:
        if obj['Observer_type'].strip(' ').upper() == key.strip(' ').upper():
            priority += 5*observer_dict[key]
        #Checking for rarity of observation
    boundary = [0,1,5,10,100]
    priority_adder = [i*3 for i in [1,1,1,0.1,0.1]]
    priority = range_comp(boundary, priority_adder, obj['Rarity'], priority)

        #Checking for length of observation (in seconds)
    boundary = [0,30,60,120,360,1000]
    priority_adder = [i*2 for i in [1,0.9,0.85,0.8,0.7,0.1]]
    priority = range_comp(boundary, priority_adder, obj['total_length'], priority)

        #Checking for number of dates since submission date
    start = dt.datetime.strptime(obj['Submission_Date'].replace(' ', ''), "%d-%m-%Y")
    days_since_sub = abs((dt.datetime.now()-start).days)
    #Determining priority additive for days left
    boundary = [0,0,1,2,5,10,100]
    priority_adder = [0.2,0.2,0.3,0.4,0.5,1]
    priority = range_comp(boundary, priority_adder, days_since_sub, priority)

        #Checking number of days until finish date
    end = dt.datetime.strptime(obj['Completed_by'], "%d-%m-%Y")
    days_to_fin = abs((end-dt.datetime.now()).days)
    #Determining priority additive for days left
    boundary = [0,0,1,2,5,10,100]
    priority_adder = [100,100,70,30,20,1]
    priority = range_comp(boundary, priority_adder, days_to_fin, priority)

        #Creating dict entry
    obj['priority'] = float(priority)
    return obj




def range_comp(ranges,priority_adder, to_check, priority):
    """Helper function for above
    -------
    ranges --> list: of all boundary conditions, if first is inclusive on bottom and top include twice
    priority_adder --> list: priority for each respective range, and for larger than last index
    to_check --> int: integer to be checked
    priority --> int/float: value to which add priority correction
    """
    backup = priority
    if to_check!=None:    
        for i in range(len(ranges)-1):
            if ranges[i]<=to_check<=ranges[i+1]:
                priority += priority_adder[i]
                return priority
        if ranges[-1]<to_check:
            priority += priority_adder[-1]
            return priority
        else:
            dprint("couldn't add to priority no appropriate range for {}".format(to_check))
            return backup
    else:
        return priority


