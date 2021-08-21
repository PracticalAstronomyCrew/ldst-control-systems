#Astropy and astroplan related stuff
from astropy import constants
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.coordinates as coord
import astropy.units as u
from astropy.time import Time
from astroplan.scheduling import PriorityScheduler, Schedule, TransitionBlock, Transitioner
from astroplan import ObservingBlock, FixedTarget, Observer
from astroplan import AltitudeConstraint,AtNightConstraint,MoonIlluminationConstraint, AirmassConstraint
from Helper_funcs import RainConstraint, SkyBrightnessConstraint
from astroplan.plots import plot_schedule_airmass



#python native modules
import sqlite3
import requests
import datetime as dt
import ephem
import os
import matplotlib.pyplot as plt
import numpy as np
import logging

import matplotlib.pyplot as plt

from pynput.keyboard import Controller

from Helper_funcs import sqlite_retrieve_table, dprint, create_new_interpolation_dataset

#Boilerplate logging
logger = logging.getLogger('main.scheduler')
logger.debug("starting scheduler logger")




class Scheduling:
    #Defining general parameters for the telescope, all the parameters outside of class functions will be assigned to the self parameter
    
    #   Telescope specifics
    filters = ['B*', 'G*', 'R*', 'H_alpha', 'None']
    # Filter transition rate
    ftr = {'filter':{   ('B*','G*'): 10*u.second,
                        ('G*','R*'): 10*u.second,
                        ('R*','H_alpha'): 10*u.second,
                        ('H_alpha','None'): 10*u.second,
                        ('None','B*'): 10*u.second}} #TODO: Change rates
    read_out_time = 20*u.second
    slew_rate = .8*u.deg/u.second
    location = EarthLocation(53.3845258962902, 6.23475766593151)
    observer = Observer(location=location)
    #Global constraints 
    twilight = AtNightConstraint.twilight_civil() #TODO: Check
    altitude = AltitudeConstraint(10*u.deg, 90*u.deg,boolean_constraint = True)#TODO: Check min height
    global_constraints = [twilight, altitude]


    def __init__(self, file_path, config):
        """Starts pipeline scheduling execution"""

        self.get_predicted_conditions(short=True)

        if os.path.isfile(os.path.join(file_path, 'sky_bright', 'Interpolation_Data.csv')):
            logger.info('Interpolation data present')
        else: #TODO: Create backup of file in case someone deletes it as a fall back and time how long it takes on the win machine
            logger.warning('No interpolation data present, retrieving now')
            create_new_interpolation_dataset('./sky_bright')
            logger.warning('Interpolation data retrieved')
            

        logger.info('Predicted sunset at {}, script will continue at {}'.format(self.sunset, self.sunset-dt.timedelta(hours=1)))
        '''#FIXME: Remove quotes
        if self.sunset > dt.datetime.now():
            time_to_sleep = ((self.sunset-dt.timedelta(hours=1))-dt.datetime.now()).total_seconds()
            if time_to_sleep <= 0:
                logger.warning('Script did not wait, check why execution started late!')
            else:
                time.sleep(time_to_sleep) #Sleeps until an hour to sunset
        else:
            logger.warning('The script reached execution after Sunset! Late start of Observation')
        '''
        logger.info('Starting applications using AutoHotkeyScript')
        self.file_path = file_path

        keyboard = Controller()
        keyboard.press('`') 
        logger.info('Triggered AHK script')

        logger.info('Retrieving weather data')

        self.weather_cond = self.get_predicted_conditions()

        logger.info('Creating priority ordered list')

        self.priority_ordered_list = self.daily_Schedule(os.path.join(file_path, 'Database.db'), 'Schedule') #Change this to reduce computation by using grouped PID and so on for priority assignment
        
        self.scheduled_blocks = self.create_priority_schedule() 

        logger.info('Created Schedule')
        #FIXME: Above doesnt fill all the timeframes only the given ones, check total free time and add other obs
        logger.info('Creating ACP scheduler text file')
        
        self.create_ACP_scheudle()

        logger.info('Created ACP schedule')
        '''
        if weather_pred['Sunrise']<dt.datetime.now():
            logger.info('Waiting until sunrise')
            (time.sleep(dt.datetime.now()-weather_pred['Sunrise'])).total_seconds()
        
        update_config()
        #Send observing results to kapteyn
        send_results(file_path,remote_path)'''

    def get_predicted_conditions(self,short=False):
        """ 
        Retrieves Data from OpenWeatherMap.org using API key 
        """
        location = (53.38,6.23) #TODO: Get location
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
            i = assign_priority(i)  #TODO: Change this script
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
            if image['seeing']!=None:
                pass #TODO: Create custom constraint
            if image['sky_brightness']!=None:
                constants.append(SkyBrightnessConstraint(weather=self.weather_cond,min=image['sky_brightness']))

            b = ObservingBlock.from_exposures(target=FixedTarget.from_name(image['object']), priority=priority, time_per_exposure=image['exposure']*u.second,number_exposures=image['number_of_exposures'], readout_time=self.read_out_time,configuration=config,constraints=constraints)
            blocks.append(b)

        transitioner = Transitioner(self.slew_rate,self.ftr)

        scheduler = PriorityScheduler(constraints = self.global_constraints, observer=self.observer, transitioner=transitioner)

        priority_schedule = Schedule(Time(self.weather_cond['Sunset']),Time(self.weather_cond['Sunrise']))

        schedule = scheduler(blocks, priority_schedule)

        if save_plot:
            plt.figure(figsize = (14,6))
            plot_schedule_airmass(priority_schedule)
            plt.legend(loc = "upper right")
            if not os.path.isdir(os.path.join(self.file_path, 'plots')):
                os.mkdir(os.path.join(self.file_path, 'plots'))
            plt.savefig(os.path.join(self.file_path, 'plots', dt.date.today().strftime('%Y%m%d')+'.png'))
            
        
        return schedule.scheduled_blocks #TODO: Fill empty spots

    def create_ACP_scheudle(self):
        """
        Creates ACP text file
        And directories for image files
        ---------
        objects --> dict as returned by night_schedule
        """
        #Create file header #FIXME: Flat plan! Prob always the same file but lets also make a constructor in case it doesnt exist
        nr_of_observations = len(self.scheduled_blocks)
        header = ';\n; --------------------------------------------\n; This plan was generated by the automated python script 4.2.6\n; --------------------------------------------\n;\n; For:           jacobus\n; Targets:       {}\n;\n; NOTE:          Timing features are disabled\n;\n; Autofocus at start of run.\n;\n; ---------------------------------------------\n;\n'.format(nr_of_observations)
        #Dusk Flat
        header += '#duskflats Schedule_flat_{}.txt  ; Acquire flat fields at dusk\n;\n#autofocus\n;\n'.format(dt.date.today().strftime('%d_%m_%Y'))
        #We will also take care of file handling here
        im_path = os.path.join(self.file_path, dt.date.today().strftime('%Y%m%d'))
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
                        params['repeat'] = '1' #FIXME: What is repeat?
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
                        header+=self.entry_layout(params,ObsID_path)
                        break #Break j loop
            elif 'THeOtherIDThing' in i.configuration:
                pass #FIXME: Add other observations
            else:
                logger.warning('Could not append observation {}'.format(i.configuration))

        #Dawn Flat
        header += '#dawnflats Schedule_flat_{}.txt  ; Acquire flat fields at dawn\n;\n;\n'.format(dt.date.today().strftime('%d_%m_%Y'))

        #End File
        header += ';\n; END OF PLAN\n;\n;'
        #Write schedule to file
        with open('Schedule_{}.txt'.format(dt.date.today().strftime('%d_%m_%Y')),'w') as file:
            file.write(header)
        #TODO Format below correctly (Bias and Darks)
        flat = '; ---------------------------------------------\n; ACP Auto-Flat Plan - Generated by Python Script\n; ---------------------------------------------\n;\n; For:      jacobus\n; At:       07:50:01\n; From:     Schedule_{}.txt\n; Flats:    16\n;\n; Lines are count,filter,binning (comma-separated)\n; Empty filter uses ACP-configured clear filter\n; ---------------------------------------------------\n;\n4,Luminance,1\n4,Red,1\n4,Green,1\n4,Blue,1\n;\n; ----------------\n; END OF FLAT PLAN\n; ----------------\n;'.format(dt.date.today().strftime('%d_%m_%Y'))

        with open('Schedule_flat_{}.txt'.format(dt.date.today().strftime('%d_%m_%Y')),'w') as file:
            file.write(flat)
    
    def entry_layout(self,params,imdir):
        """Returns string formated for ACP planner plan text file""" #TODO: Set default parameters 
        entry='; === Target Dark ({}x{}sec@bin1) ===\n;\n#repeat {}\n#count {}\n#interval {}\n#binning 1\n#dark\n;'.format(params['count'],params['interval'],params['repeat'],params['interval'],params['count'],params['interval'])
        entry+='; === Target Bias ({}@bin1) ===\n;\n#repeat {}\n#count {}\n#interval {}\n#binning 1\n#bias\n;'.format(params['count'],params['repeat'],params['count'],params['interval'])
        
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
    observer_dict =  {'Moderator':10, 'OA':1, 'Staff':0.5,'Student (Thesis)':0.4,'Student': 0.3,'Outreach/schools':0.2,'Public':0.1}
    for key in observer_dict:
        if obj['Observer_type'] == key:
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
    start = dt.datetime.strptime(obj['Submission_Date'], "%d-%m-%Y")
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





"""





The below can most likely be removed

Wait for now




"""


#FUNction definitionass
def night_schedule(obj):
    """
    Function determining which observations will occure to maximize observing time per night
    -------------
    obj ---> Priority Sorted list of dict returned from func: assign_priority or otherwise sorted

    https://clearoutside.com/forecast/53.38/6.23
    """

    weather_data = get_predicted_conditions()

    #Create Coordinate System
    location = EarthLocation(53.3845258962902, 6.23475766593151) #Lon Lat of observatory (currently guessed)
    t = Time([(weather_data['Sunset']+i*dt.timedelta(seconds=600)).strftime('%Y-%m-%dT%H:%M:%S') for i in range(24) if ((weather_data['Sunset']+i*dt.timedelta(seconds=600))<weather_data['Sunrise'])])
    altaz = coord.AltAz(location=location, obstime=t)
    #Below filtering is done for wheter or not observation is actually possible and within which timeframe
    for i in range(len(obj)):
        obj[i] = check_min_conditions(obj[i],weather_data) #TODO: Since now all obsID's are split save data and reassign to all
        if obj[i]['Possible']:
            obj[i] = check_visible(obj[i],altaz)
        else:
            pass
    #Assigning an observational schedule
    schedule = {(weather_data['Sunset']+dt.timedelta(seconds=600*i)):0 for i in range(84) if (weather_data['Sunset']+dt.timedelta(seconds=600*i)<weather_data['Sunrise'])}
    for i in obj: #i is dict object for each observation
        if i['Possible']: #Previous functions will have established this
            count = 0 
            obs_length = i['total_length'] 
            if int(obs_length) != float(obs_length): obs_length = int(obs_length)+1 #TODO: For now 10 minute indeces, see if and how to split it
            for key in schedule: #Keys are datetime objects 10 minutes seperated from each other
                if i['Obs_time'][0].to_datetime()<=key and schedule[key]==0 and key < i['Obs_time'][1].to_datetime() and count != obs_length: #Check start time onward, that nothing is assigned yet, and that entry is less than end time, and that the needed timeslots haven't all been assigned yet
                    schedule[key] = i['obsID'] #Assign obs_id
                    count += 1
                elif key == i['Obs_time'][1].to_datetime() and schedule[key]==0: #Check end time, and that nothing is assigned yet
                    schedule[key] = i['obsID']
                    count+=1
                    break
                elif count == obs_length:
                    break
    return obj, schedule





def check_visible(obj,altaz):
    """
    Checks if object is visible during the night
    ---------
    obj --> dict: object containing scheduling information
    altaz --> Coordinate Frame of observatory
    location --> EarthLocation: Location of Observatory
    """
    #base coordinate system
    res = SkyCoord.from_name(obj['object'])
    res = res.transform_to(altaz)
    observing_points = [[res[i], i] for i in range(len(res)) if (res[i].alt>0)] #Check min angle
    if len(observing_points)==0:
        obj['Possible'] = False
        return obj
    else:
        if observing_points[0][0].obstime.to_datetime()+dt.timedelta(seconds=obj['total_length']*60)<observing_points[-1][0].obstime.to_datetime():
            obj['Possible'] = True
            obj['Obs_time'] = [observing_points[0][0], observing_points[-1][0]]
        else:
            obj['Possible'] = False
            return obj
    if 'airmass' in obj['min_cond']:
        res = res[observing_points[0][1]:observing_points[-1][1]] #Getting visible time range
        airmass = res.secz
        observing_times = [t[i] for i in range(len(airmass)) if airmass[i]<objects[0]['min_cond']['airmass']]
        if len(observing_times)==0:
            obj['Possible'] = False
            return obj
        else:
            objects[0]['Obs_time'] = [observing_times[0].obstime,observing_times[-1].obstime]
            obj['Possible'] = True
    else: 
        obj['Obs_time'] = [obj['Obs_time'][0].obstime, obj['Obs_time'][-1].obstime]

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
    for i in range(len(ranges)-1):
        if ranges[i]<to_check<=ranges[i+1]:
            priority += priority_adder[i]
            return priority
    if ranges[-1]<to_check:
        priority += priority_adder[-1]
        return priority
    else:
        dprint("couldn't add to priority no appropriate range for {}".format(to_check))
        return backup





def make_plot(objects, schedule,weather,print_out=True, save_dir = ''):
    """Makes standardized graphs of objects planned for observation and the weather conditions"""
    keys = {'Temperature', 'Pressure', 'Humidity', 'Dew_Point', 'Cloud_cover', 'Visibility', 'Wind_Speed', 'Wind_direction', 'Rain_Prob', 'Time', 'Moon', 'Sunset', 'Sunrise'}
    fig = plt.figure(figsize=(12,12))
    fig,ax = plt.subplots(nrows=2,ncols=2,figsize=(24,12))
    ax[0,0].plot(weather['Time'],np.array(weather['Temperature'])-273.15,label='Temperature C')
    ax[0,0].plot(weather['Time'],np.array(weather['Dew_Point'])-273.15,label='Dew Point C')
    ax[0,1].plot(weather['Time'],np.array(weather['Pressure']),label='Pressure kPa')
    ax[0,1].plot(weather['Time'],np.array(weather['Visibility'])/10,label='Visibility 10*m')
    ax[1,0].plot(weather['Time'],np.array(weather['Humidity']),label='Humidity %')
    ax[1,0].plot(weather['Time'],np.array(weather['Cloud_cover']),label='Cloud Cover %')
    ax[1,0].plot(weather['Time'],np.array(weather['Rain_Prob']),label='Rain Probability %')
    ax[1,1].plot(weather['Time'],np.array(weather['Wind_Speed']),label='Wind Speed m/s')
    observing = False
    for key in schedule:
        if schedule[key]!=0 and not observing:
            name = [i['object'] for i in objects if i['obs_id']==schedule[key]]
            ax[0,0].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            ax[1,0].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            ax[0,1].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            ax[1,1].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            observing = True
            obs_id = str(schedule[key])
        elif int(schedule[key])!=int(obs_id) and observing:
            observing = False
            ax[0,0].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            ax[1,0].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            ax[0,1].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            ax[1,1].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            if schedule[key]!=0: #In case new observation is started here
                name = [i['object'] for i in objects if i['obs_id']==schedule[key]]
                ax[0,0].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                ax[1,0].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                ax[0,1].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                ax[1,1].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                observing = True
                obs_id = str(schedule[key])


    for j in range(len(ax)):
        for i in range(len(ax[j])):
            ax[j][i].set_xlim(weather['Sunset']-dt.timedelta(seconds=5*60),weather['Sunrise']-dt.timedelta(seconds=5*60))
            ax[j][i].legend()
    if print_out:
        plt.show()
    else:
        plt.savefig(os.path.join(save_dir,'{}_pred_plot.png'.format(dt.date.today().strftime('%d_%m_%Y'))))


