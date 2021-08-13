from re import L
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.coordinates as coord
#import astropy.unit as u
from astropy.time import Time
import time
import sqlite3
import requests
import time
import datetime as dt
import ephem
import matplotlib.pyplot as plt
import numpy as np
import logging

from Helper_funcs import sqlite_retrieve_table, dprint

logger = logging.getLogger('main.Scheduler')
logger.debug("starting data logger")

def assign_priority(obj):
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

        #Checking for length of observation (in minutes)
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


def get_predicted_conditions(short=False): #TODO: Percentual cloud cover, how do we detect where the clouds are/what is observable? NN trained by human supervisor?
    """ #TODO: Get sky brightness
    Retrieves Data from OpenWeatherMap.org using API key #TODO: Get minute wise rain, #TODO: Get hourly moon position? i.e. avoid looking at objects close to the moon?
    """
    location = (53.38,6.23)
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
        weather_cond['Sunrise']=dt.datetime.utcfromtimestamp(weather['daily'][1]['sunrise'])
    if short:
        weather_cond = {}
        weather_cond['Sunset']=dt.datetime.utcfromtimestamp(weather['daily'][1]['sunrise'])
    return weather_cond



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
        obj[i] = check_min_conditions(obj[i],weather_data)
        if obj[i]['Possible']:
            obj[i] = check_visible(obj[i],altaz)
        else:
            pass
    #Assigning an observational schedule
    schedule = {(weather_data['Sunset']+dt.timedelta(seconds=600*i)):0 for i in range(84) if (weather_data['Sunset']+dt.timedelta(seconds=600*i)<weather_data['Sunrise'])}
    for i in obj: #i is dict object for each observation
        if i['Possible']: #Previous functions will have established this
            count = 0 #TODO: Check that we can split observations!!!
            obs_length = i['total_length']/10
            if int(obs_length) != float(obs_length): obs_length = int(obs_length)+1 #TODO: For now 10 minute indeces, see if and how to split it
            for key in schedule: #Keys are datetime objects 10 minutes seperated from each other
                if i['Obs_time'][0].to_datetime()<=key and schedule[key]==0 and key < i['Obs_time'][1].to_datetime() and count != obs_length: #Check start time onward, that nothing is assigned yet, and that entry is less than end time, and that the needed timeslots haven't all been assigned yet
                    schedule[key] = i['obs_id'] #Assign obs_id
                    count += 1
                elif key == i['Obs_time'][1].to_datetime() and schedule[key]==0: #Check end time, and that nothing is assigned yet
                    schedule[key] = i['obs_id']
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

    
def check_min_conditions(obj,weather):
    """Check that minimum conditions are satisfied
    --------
    obj --> dict: object containing schedule information
    weather --> dict: collected weather data for the night
    """
    #TODO: Add min condition to sqlite database as list
    for i in obj['min_cond']:
        if i[0] == 'min_moon_phase':
            date = dt.date.today()
            moon = ephem.Moon(date).moon_phase
            if moon < i[1]:
                weather['Moon'] = moon
                obj['Possible'] = True
        if i[0] == 'min_seeing': #TODO: Get min seeing - could use wind_gust, wind_speed, wind_deg of API return as proxy
            boolean = [True if i[1] < weather['min_seeing'][j] else False for j in range(len(weather['min_seeing']))]
            if len(boolean)<= (obj['Obs_time']/60): #Checking that the predicted seeing is good enough
                obj['min_seeing_pred'] = boolean
                obj['Possible'] = True
            else:
                obj['Possible'] = False
                return obj
        if i[0] == 'min_sky_brightness':
            boolean = [True if i[1] < weather['min_sky_brightness'][j] else False for j in range(len(weather['min_sky_brightness']))]
            if len(boolean)<= (obj['Obs_time']/60):
                obj['min_sky_brightness_pred'] = boolean
                obj['Possible'] = True
            else:
                obj['Possible'] = False
                return obj
    obj['Possible']=True
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

from Helper_funcs import sqlite_retrieve_table
def daily_Schedule(database, table):
    """
    Creates schedule every day prior to observing
    ---------
    database --> str: sqlite database
    table --> str: table name containing objects to be observed    
    """
    connect = sqlite3.connect(database)
    content = sqlite_retrieve_table(connect, table)
    count = 1
    for i in content: 
        i = assign_priority(i) 
        i['obs_id'] = count #assign obs_id for scheduling 
        count+=1
    content = sorted(content, key=lambda k: k['priority'], reverse=True)
    return content



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


def create_ACP_scheudle(objects, schedule):
    """
    Creates ACP text file
    ---------
    objects --> dict as returned by night_schedule
    """
    #Below segment to determine number of objects to be observed during night
    obj = {}
    for key in schedule:
        if schedule[key] !=0:
            if schedule[key] in obj:
                obj[schedule[key]] +=1
            else:
                obj[schedule[key]] =1
    nr_of_observations = len(obj.keys())
    
    #Create file header
    header = ';\n; --------------------------------------------\n; This plan was generated by the automated python script 4.2.6\n; --------------------------------------------\n;\n; For:           jacobus\n; Targets:       {}\n;\n; NOTE:          Timing features are disabled\n;\n;\n; ---------------------------------------------\n;\n'.format(nr_of_observations)
    #Dusk Flat
    if dusk_flat: #FIXME define variable + flat plan
        header += '#duskflats Schedule_flat_{}.txt  ; Acquire flat fields at dusk\n;\n;\n'.format(dt.date.today().strftime('%d_%m_%Y'))
    else:
        header += ';\n'
    # Reference to current obs_id
    curr = 0
    for key in schedule: #Key here are date objects seperated by 10 minutes
        if schedule[key]!=curr and schedule[key]!=0:
            curr = schedule[key]
            params = {}
            for entry in objects: #Iterate through list of observations, should be in correct order
                if entry['obs_id']==curr: #FIXME: Add the darks flats and bias`s here
                    for quantifier in ['catalogue_name','count','interval','repeat'] #FIXME: FILTERS!
                        params[quantifier] = entry[quantifier]
                    header += entry_layout(params) #Add dark and bias and what not
                    break
    #Dawn Flat
    if dawn_flat: #FIXME define variable + flat plan
        header += '#dawnflats Schedule_flat_{}.txt  ; Acquire flat fields at dawn\n;\n;\n'.format(dt.date.today().strftime('%d_%m_%Y'))
    else:
        header += ';\n'

    header += ';\n; END OF PLAN\n;\n;'
    #Write schedule to file
    with open('Schedule_{}.txt'.format(dt.date.today().strftime('%d_%m_%Y')),'w') as file:
        file.write(header)
    #TODO Format below correctly
    flat = '; ---------------------------------------------\n; ACP Auto-Flat Plan - Generated by Python Script\n; ---------------------------------------------\n;\n; For:      jacobus\n; At:       07:50:01\n; From:     Schedule_{}.txt\n; Flats:    16\n;\n; Lines are count,filter,binning (comma-separated)\n; Empty filter uses ACP-configured clear filter\n; ---------------------------------------------------\n;\n4,Luminance,1\n4,Red,1\n4,Green,1\n4,Blue,1\n;\n; ----------------\n; END OF FLAT PLAN\n; ----------------\n;'.format(dt.date.today().strftime('%d_%m_%Y'))

    with open('Schedule_flat_{}.txt'.format(dt.date.today().strftime('%d_%m_%Y')),'w') as file:
        file.write(flat)

def entry_layout(params, dark=False, bias=False):
    """Returns string formated for ACP planner plan text file"""
    if dark: #FIXME: Below incomplete still need to add filters and what not
        entry='; === Target Dark ({}x{}sec@bin1) ===\n;\n#repeat {}\n#count {}\n#interval {}\n#binning 1\n#dark\n;'.format(params['count'],params['interval'],params['repeat'],params['interval'],params['count'],params['interval'])
    elif bias:
        entry='; === Target Bias ({}@bin1) ===\n;\n#repeat {}\n#count {}\n#interval {}\n#binning 1\n#bias\n;'.format(params['count'],params['repeat'],params['count'],params['interval'])
    else:
        entry = '; === Target {} ===\n;\n'.format(params['catalogue_name'])
        if autofocus: #FIXME: define variable
            entry += '#autofocus    ; AF before target requested\n'
        #FIXME: Define sourcedir as global!
        entry += '; WARNING: Folder path is not portable.\n#dir {}    ; Images forced to go into this folder\n'.format(os.path.join("C:/", sourcedir))
        entry +=  '#repeat {}\n'format(params['repeat'])
        entry += '#count {}\n'.format(','.join(params['count'])) #TODO: Make sure params count is a list of str numbers, with the same order as filters
        entry += '#filter {}\n'.format(','.join(params['Filter']))
        entry += '#interval {}\n'.format(','.join(params['interval'])) #list of exp times #TODO: All ,ust be string!
        entry += '#binning {}\n'.format(','.format(params['binning']))
        entry += '{}\n'.format(params['catalogue_name'])
        entry += '#dir    ; Revert to default images folder\n;\n'
    return entry