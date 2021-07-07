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

#Function imports from the same directory
from Helper_funcs import dprint, sqlite_retrieve_table

class Scheduler:
    """
    Overarching class taking care of Scheduling
    - Image calibration and other controls will be contained to seperate Classes
    This class is only required for execution and all other classes will not be

    https://observatorycontrolsystem.github.io/
    """
    def __init__(self, Controller):
        """
        AsCOM or INDI python bindings for controling the observatory
        https://www.indilib.org/develop/indi-python-bindings.html
        ASCOM ALPACA for communication
        """
        #List which will contain all observations
        self.schedule = []
        self.Dome = Controller.Dome
        self.Telescope = Controller.Telescope
        self.con = Controller.con
        self.obs = EarthLocation(53.3845258962902, 6.23475766593151) 
        self.cur = self.con.cursor()
        dprint('Retrieving Scheduling data')
        self.objects = sqlite_retrieve_table(self.cur, 'Schedule')
        for i in range(len(self.objects)):
            self.determine_priority(self.objects[i])
        order = self.do_tonight()
        dprint('Created observing Schedule in order: {}'.format(order))


    def determine_priority(self, obj):
        """
        Function that positions an Observing request 
        obj must contain: time sensitive	Observer type 	Rarity	total length (min)	Submission date
        """
        #Base variable onto which is added
        priority = 0
        #Checking if time sensitive
        if obj['time_sensitive'] == 'Yes':
            priority += 10
        #Checking who created the querry
        observer_dict =  {'Moderator':100, 'OA':1, 'Staff':0.5,'Student (Thesis)':0.4,'Student': 0.3,'Outreach/schools':0.2,'Public':0.1}
        for key in observer_dict:
            if obj['Observer_type'] == key:
                priority += 5*observer_dict[key]
        #Checking for rarity of observation
        if 0 < obj['Rarity'] <= 10:
            priority += 3*1
        if obj['Rarity'] > 10:
            priority += 3*0.1
        #Checking for length of observation
        if obj['total_length'] <= 30:
            priority += 2*1
        if 30 < obj['total_length'] <= 60:
            priority += 2*0.9
        if 60 < obj['total_length'] <= 120:
            priority += 2*0.85
        if 120<obj['total_length'] <= 360:
            priority += 2*0.8
        if 360<obj['total_length'] <= 1000:
            priority += 2*0.7
        if 1000<obj['total_length']:
            priority += 2*0.1
        #Checking for submission date
        if 0<=obj['submission_date'] <= 1:
            priority += 1*0.2
        if 1<obj['submission_date'] <= 2:
            priority += 1*0.3
        if 2<obj['submission_date'] <= 5:
            priority += 1*0.4       
        if 5<obj['submission_date'] <= 10:
            priority += 1*0.5
        if 10<obj['submission_date'] <= 100:
            priority += 1*1
        obj['priority'] = float(priority)
        #Iterating for position
        for index in range(len(self.schedule)):
            if type(self.schedule[index]['priority']) == float: #Check for manually changed order, not to be touched
                if self.schedule[index]['priority'] < obj['priority']:
                    break
        #Adding the request to list moving the element with a lower priority one order down
        self.schedule.insert(index, obj) #TODO: Maybe change to dictionary object with key being priority and obj being value

    def do_tonight(self):
        """
        Function determining which observations will occure to maximize observing time per night
        """
        observing_time = Time('2010-12-21 1:00')
        #base coordinate system
        altaz = AltAz(location=obs, obstime=observing_time)
        location = EarthLocation(53.3845258962902, 6.23475766593151) #Lon Lat of observatory (currently guessed)




        m1 = SkyCoord.from_name('M1')
        m1.transform_to(altaz)
        return 0

    def do_next(self):
        """
        Modified do_tonight, in case telescope has to close midway through observation or the weather is inconsistent
        """
        return 0
        



    def start_observing(self):
        """
        Checks weather conditions, time and sun's position. 
        Slews telescope
        If all checks are passed opens dome
        and starts observing
        """
        #sched.scheduler(time.monotonic(),) #TODO: Check if this could be useful
        #Check that telescope is allowed to observe

        for i in range(number_of_exposures):
            while self.Dome.open: 
                #TODO: Start imaging
                return 0
            while not self.Dome.open:
                time.sleep(60)
                #TODO: Add condition in case object is not visible anymore
                return 0

                


        



    def write_metadat(self):
        """
        Write observations metadata to fits file #TODO: Check if this is required
        """
        return 0




    def background_tasks(self):
        """
        Uses seperate script in background (preferably by doing computation while data is being collected) run as second
        process to compute Bias, Dark, and flat
        """
        return 0



from Helper_funcs import sqlite_retrieve_table

def assign_priority(obj, today):
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
    days_since_sub = (today-start).days
    #Determining priority additive for days left
    boundary = [0,0,1,2,5,10,100]
    priority_adder = [0.2,0.2,0.3,0.4,0.5,1]
    priority = range_comp(boundary, priority_adder, days_since_sub, priority)

        #Checking number of days until finish date
    end = dt.datetime.strptime(obj['Completed_by'], "%d-%m-%Y")
    days_to_fin = (end-today).days
    #Determining priority additive for days left
    boundary = [0,0,1,2,5,10,100]
    priority_adder = [100,100,70,30,20,1]
    priority = range_comp(boundary, priority_adder, days_to_fin, priority)

        #Creating dict entry
    obj['priority'] = float(priority)
    return obj


def get_predicted_conditions(): #TODO: Percentual cloud cover, how do we detect where the clouds are/what is observable? NN trained by human supervisor?
    """ #TODO: Get sky brightness
    Retrieves Data from OpenWeatherMap.org using API key #TODO: Get minute wise rain, #TODO: Get hourly moon position? i.e. avoid looking at objects close to the moon?
    """
    location = (53.38,6.23)
    api_key='52695aff81b7b6e5708ab0e924b859f2'
    url= "http://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=[current,minutely,alerts]&appid={}".format(*location, api_key)
    weather = requests.get(url).json()
    keys = ['Temperature', 'Pressure', 'Humidity', 'Dew_Point', 'Cloud_cover', 'Visibility', 'Wind_Speed','Wind_direction','Rain_Prob']
    key_return = ['temp','pressure','humidity','dew_point','clouds','visibility','wind_speed','wind_deg','pop']
    weather_cond = {keys[i]:[weather['hourly'][j][key_return[i]] for j in range(len(weather['hourly']))] for i in range(len(keys))}
    weather_cond['Time']=[dt.datetime.utcfromtimestamp(i['dt']) for i in weather['hourly']]
    weather_cond['Moon']=weather['daily'][0]['moon_phase']
    weather_cond['Sunset']=dt.datetime.utcfromtimestamp(weather['daily'][0]['sunset'])
    weather_cond['Sunrise']=dt.datetime.utcfromtimestamp(weather['daily'][1]['sunrise'])
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
     
    #Sunrise + weather data https://medium.com/nexttech/how-to-use-the-openweathermap-api-with-python-c84cc7075cfc

    for i in range(len(obj)):
        obj[i] = check_min_conditions(obj[i],weather_data) #TODO: Check which function executes quicker and sort accordingly
        if obj[i]['Possible']:
            obj[i] = check_visible(obj[i],altaz,location)
        else:
            pass
    return obj

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
    today = dt.datetime.now()
    for i in content: 
        i = assign_priority(i, today) #Pass date to compute days since and days to 
    content = sorted(content, key=lambda k: k['priority'], reverse=True)
    return content



