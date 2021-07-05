from astropy.coordinates import SkyCoord, EarthLocation
import astropy.coordinates as coord
#import astropy.unit as u
from astropy.time import Time
import time
import sqlite3
import sched
import time
import datetime as dt

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

def get_predicted_conditions():
    """
    Retrieves Data from https://www.goodtostargaze.com/ for location 9976 (Lauwersoog)
    """


def night_schedule():
    """
    Function determining which observations will occure to maximize observing time per night

    https://clearoutside.com/forecast/53.38/6.23
    """
    observing_time = Time('2010-12-21 1:00')
    #base coordinate system
    
    location = EarthLocation(53.3845258962902, 6.23475766593151) #Lon Lat of observatory (currently guessed)
    weather_data = get_predicted_conditions()

    #Sunrise + weather data https://medium.com/nexttech/how-to-use-the-openweathermap-api-with-python-c84cc7075cfc
    m1 = SkyCoord.from_name('M1')
    altaz = AltAz(location=obs, obstime=observing_time)
    m1.transform_to(altaz)
    
    return 0


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


def daily_Schedule(database, table):
    """
    Creates schedule every day prior to observing

    #TODO: submission date key should be date string so do that later, also in retrieve_table!
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
        


