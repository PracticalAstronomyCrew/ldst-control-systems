#!/usr/bin/python
"""
Custom functions for output and logging
"""
from sqlite3.dbapi2 import Cursor
import sys
import sqlite3
import time
import random
import numpy as np

#interpolation routines
from scipy.interpolate import interp1d, NearestNDInterpolator
"""
Telescope Specific functions

add_randome_data --> Adds 99 random observations to be scheduled for Messier objects 1-99


"""


def add_randome_data(nr_of_PIDs):
    """
    Helper Function adding randomised data to the Database
    -------------
    nr_of_points --> int: number of datapoints to add
    """
    #Create and add random dataset to Database:
    connect = sqlite3.connect('Database.db') #FIXME: Rarity needs to be added or removed
    with connect:
        try:
            connect.execute("DROP TABLE Observations")
        except:
            print('Schedule does not exist')
        connect.execute("""CREATE TABLE Observations
            (PID, Name, EMail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, missing_obsIDs, total_length, logsheet, Obs_days)""")
        try:
            connect.execute("DROP TABLE Schedule")
        except:
            print('Schedule does not exist')
        connect.execute("""CREATE TABLE Schedule
            (obsID, object, PID, Filter, exposure, binning, airmass, moon, seeing, sky_brightness, Observer_type, time_sensitive, Submission_Date, Completed_by, total_length, Rarity,number_of_exposures)""")
    #Create PID entries for Observations
    PID = np.linspace(1, nr_of_PIDs, nr_of_PIDs)
    Name = ['User' for i in range(nr_of_PIDs)]
    EMail = ['User@kapteyn.nl' for i in range(nr_of_PIDs)]
    Phone = ['001123121' for i in range(nr_of_PIDs)]
    Completed_by = [random_date("5-7-2021", "30-12-2021", random.random()) for i in range(nr_of_PIDs)]
    Submission_Date = [random_date("1-1-2020", "5-7-2021", random.random()) for i in range(nr_of_PIDs)]
    observer_types =  ['Moderator', 'OA', 'Staff','Student (Thesis)','Student','Outreach/schools','Public']
    Observer_type = [observer_types[i] for i in np.random.randint(0,7,nr_of_PIDs)]
    time_sensitive = [True if i==1 else False for i in np.random.randint(0,2,nr_of_PIDs)] 
    obsIDs = []
    obsID= 1
    for i in PID: #Creating a random number of obsIDs [5, 15] for each PID 
        ls = []
        for j in range(np.random.randint(1, 5)):
            ls.append(obsID)
            obsID+=1
        obsIDs.append(ls)
    missing_obsIDs = obsIDs
    logsheet = [None for i in PID] #Both empty as nothing happened
    Obs_days= [None for i in PID] 
    total_length = np.zeros(len(PID))
    #For PID we still need total_length, first we construct the inidividual obsIDs for  the Scheduler database
    Sched_obsID = [val for sublist in obsIDs for val in sublist]
    Sched_PID = []
    Sched_obj = []
    filter = []
    exposure = []
    nr_exposures = []
    rarity =  [1 for i in range(len(Sched_obsID))]
    binning = [1 for i in range(len(Sched_obsID))] #Prob never going to use a different binning
    airmass = np.random.random(len(binning))*4
    airmass = [i if 1<i<3 else None for i in airmass]
    moon = np.random.random(size=len(Sched_obsID))
    seeing = [None for i in binning] #TODO:
    sky_brightness = [None for i in binning] #TODO:
    Sched_Observer = [[Observer_type[i] for j in range(len(obsIDs[i]))] for i in range(len(PID))]
    Sched_Observer = [val for sublist in obsIDs for val in sublist]
    Sched_time_sensitive = [[time_sensitive[i] for j in range(len(obsIDs[i]))] for i in range(len(PID))]
    Sched_time_sensitive =[val for sublist in Sched_time_sensitive for val in sublist]
    Sched_Submission_Date = [[Submission_Date[i] for j in range(len(obsIDs[i]))] for i in range(len(PID))]
    Sched_Submission_Date = [val for sublist in Sched_Submission_Date for val in sublist]
    Sched_Completed_by = [[Completed_by[i] for j in range(len(obsIDs[i]))] for i in range(len(PID))]
    Sched_Completed_by = [val for sublist in Sched_Completed_by for val in sublist]
    for i in range(len(obsIDs)):
        for entry in obsIDs[i]:
            #Sched_obsID.append(entry) #Append obsIDs in order
            Sched_obj.append('M '+str(np.random.randint(1,99)))
            Sched_PID.append(PID[i])
            filter.append(['R*', 'G*', 'B*', 'H_Alpha', 'None'][np.random.randint(0,5)])
            exposure.append(60*np.random.randint(1,5))
            nr_exposures.append(np.random.randint(1,10))
            total_length[i] += exposure[-1]
    Sched_total_length = [total_length[int(i)-1] for i in Sched_PID]
    
    Random_Schedule = [[PID[i], Name[i], EMail[i], Phone[i], Completed_by[i], Submission_Date[i], Observer_type[i], time_sensitive[i], obsIDs[i], missing_obsIDs[i], total_length[i], logsheet[i], Obs_days[i]] for i in range(nr_of_PIDs)]   
    
    for i in range(nr_of_PIDs):
        sqlite_add_to_table(connect, 'Observations', Random_Schedule[i])
    
    Random_Schedule = [[Sched_obsID[i], Sched_obj[i], Sched_PID[i], filter[i], exposure[i], binning[i], airmass[i], moon[i], seeing[i], sky_brightness[i], Sched_Observer[i], Sched_time_sensitive[i], Sched_Submission_Date[i], Sched_Completed_by[i], Sched_total_length[i], rarity[i],nr_exposures[i]] for i in range(len(Sched_obsID))]   
    
    for i in range(len(Sched_obsID)):
        sqlite_add_to_table(connect, 'Schedule', Random_Schedule[i])




"""
Logging related functions

Logger ---> redirects terminal output
dprint ---> Modified print function, prints script_name: [function_name] : line_number   and then message
"""

class Logger(object):
    '''
    Class that redirects output to terminal and log file
    https://stackoverflow.com/questions/20525587/python-logging-in-multiprocessing-attributeerror-logger-object-has-no-attrib
    Usage:
    sys.stdout = Logger(name="{name for log file}")
    '''
    def __init__(self, name):
        self.terminal = sys.stdout
        self.log = open(name, 'a')
    
    def __getattr__(self, attr):
        return getattr(self.terminal, attr)

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  
        
    def flush(self):
        pass 

def dprint(fmt=None, *args, **kwargs):
    """Modifed print function
    prints script_name: [function_name] : line_number   and then message
    """
    #Open/create log file so that all print statements are written to
    try:
        name = sys._getframe(1).f_code.co_name
    except (IndexError, TypeError, AttributeError):  # something went wrong
        name = "<unknown>"
    try:
        line = sys._getframe(1).f_lineno
    except:
        line = "<unknown>"
    try:
        print("{}:[{}]:{} {}".format(sys.argv[0].split('/')[-1],name,line,(fmt or "{}").format(*args, **kwargs)))
    except:
        #In some print statements the above does not work and the below is just the easier method of fixing it
        print(fmt, args, kwargs)





"""
Sqlite3 helper functions

sqlite_retrieve_table(cursor, table) ---> Retrieve data from table
sqlite_add_to_table(connect, table, to_add) ---> Appends data to sqlite table
sqlite_get_tables(conn) ---> Returns list of tables
"""

def sqlite_retrieve_table(connect, table):
    """
    Retrieves all data from passed sqlite table and returns list of dictionary object
    performs type conversions specific for telescope schedule
    -------------
    connect --> sqlite3.connect(Datbase)
    table --> str: table name
    """
    rows = []
    dict_names = []
    with connect:
        for item in connect.execute('''PRAGMA table_info({});'''.format(table)).fetchall():
            dict_names.append(item[1])
        res = connect.execute('SELECT * FROM {}'.format(table)).fetchall()
        if len(res) != 0:
            for row in res:
                rows.append({dict_names[i]:row[i] for i in range(len(dict_names))})
            #This is a sequence of if else statements given the different key's
            rows = [{key:(rows[i][key] if key in ['Observer_type','Name','EMail','Phone','Filter','object','time_sensitive','priority','Completed_by','Submission_Date'] else None if rows[i][key]=='None' else rows[i][key][1:-2:].split(',') if key in ['obsIDs', 'missing_obsIDs'] else int(float(rows[i][key]))) for key in rows[i]} for i in range(len(rows))]
        else:
            dprint('file is empty')
    return rows

def sqlite_add_to_table(connect, table, to_add):
    """
    Appends data to sqlite table
    -------------
    connect --> sqlite3.connect(Datbase)
    table --> str: table name
    to_add --> list of items for row to be added
    """
    with connect:
        data = '('
        for i in range(len(to_add)-1): 
            data+= "'"+str(to_add[i])+"', "
        data += "'"+str(to_add[-1])+"')"
        print("""INSERT INTO {}{} VALUES{};""".format(table, sqlite_get_columns(connect, table),data))
        connect.execute("""INSERT INTO {}{} VALUES{};""".format(table, sqlite_get_columns(connect, table),data))
    

def sqlite_get_columns(connect, table):
    with connect:
        res = connect.execute("""SELECT * FROM sqlite_master;""").fetchall()
    for i in res:
        if i[1]==table:
            return '('+i[-1].split('(')[-1]


def sqlite_remove_row(connect, table, Identifier_string, Identifier_value):
    """table ---> table to be modified
    Identifier_string --> the header from which the row can be recognized 
    Identifier_value --> The value of the header which identifies the row"""
    connect.execute("DELETE from {} where {}={}".format(tabel, Identifier_string, Identifier_value))

def sqlite_get_tables(conn):
    """
    Gets list of names of tables in database
    ----------------
    conn --> sqlite3.connect(Datbase)
    """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [
        v[0] for v in cursor.fetchall()
        if v[0] != "sqlite_sequence"
    ]
    cursor.close()
    return tables



"""
Time functions
"""
import random
import time
    
def str_time_prop(start, end, time_format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formatted in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(time_format, time.localtime(ptime))

def random_date(start, end, prop):
    """
    Returns random date between the two specified
    """
    return str_time_prop(start, end, '%d-%m-%Y', prop)
    

"""
Downlaod Sky brightness data from washetdonker.nl

"""

import requests
import os
import datetime as dt
import csv

def get_sky_bright_hist(dir):
    """
    Dir relative to current directory, directory must be empty or content will be deleted
    Takes approx 130s
    """
    if os.path.isdir(dir):
        for root, dirs, files in os.walk(dir, topdown=True):
            for i in files:
                os.remove(os.path.join(root, i))
    else:
        os.mkdir(dir)

    #Below is date of first entry
    date = dt.date(2019,10,15)
    while date < dt.date.today():
        file_name = date.strftime('%Y%m%d')
        url = 'https://www.washetdonker.nl/data/Lauwersoog/{}/{}/{}_120000_SQM-Lauwersoog.dat'.format(date.strftime('%Y'),date.strftime('%m'),file_name)
        with open(os.path.join(dir, file_name+'.csv'),'wb') as f, requests.get(url, stream=True) as r:
            for line in r.iter_lines():
                f.write(line+'\n'.encode())
        date += dt.timedelta(days=1)

def overwrite_dir(dir, data):
    """overwrite csv dir with data apssed
    --------
    dir --> string of directory
    data --> dict of iterables with key file name
    """
    for root, dirs, files in os.walk(dir, topdown=True):
        for i in files:
            os.remove(os.path.join(root, i))
    for key in data:
        with open(os.path.join(dir, key+'.csv'),'w') as f:
            spamwriter = csv.writer(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in data[key]:
                spamwriter.writerow(i)


def load_all_csv(dir):
    """
    Loads all csv files in a directory and appends them to a dictionary object using the file name without extension
    If there are files that gave a bad HTML response they will be filtered
    approx 3s
    """

    loaded_data = {}

    for root, dirs, files in os.walk(dir, topdown=True):
        for i in files:
            with open(os.path.join(root, i), mode ='r')as file:
                data = list(csv.reader(file))
                if data[0] == ['<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">']:
                    pass
                else:
                    loaded_data[str(i)[:-4:]] = data
            

    return loaded_data

from astropy.coordinates import EarthLocation,AltAz,get_moon,get_sun
from astropy.time import Time

def create_new_interpolation_dataset(dir, remove = True):
    ''' Execution time: 30-45 minutes
    This function downloads all data from washetdonker.nl for Lauwersoog
    It then saves the data to dir, as there is a lot of data
    Then it loads each dataset and clips it around sunset and sunrise
    This new dataset will be saved as a csv ready for interpolation 
    (However further cliping i.e. using every 3rd entry is recommended)
    '''''
    #Download past data (on my device 132sec)
    get_sky_bright_hist(dir)
    #Load the csv's into ram''
    dat = load_all_csv(dir)
    #Create datetime objects
    for key in dat.keys():
        try:
            temp = [np.array([i[0].split(';') for i in dat[key][35:]]).transpose()[j] for j in (1,2,-1)]
        except:
            print(dat[key]) 
        dat[key] = [[dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.000') for x in temp[0]], temp[1], temp[2]]
    #Append relevant parameters This takes long! 2000s on  my device
    location = EarthLocation(53.3845258962902, 6.23475766593151)
    for key in dat:
        time = Time(dat[key][0])
        altaz = AltAz(location=location, obstime=time)
        moon = get_moon(time, location).transform_to(altaz).alt.deg
        dat[key].append(moon)
        moon_phase = get_moon_phase(dat[key][0][0]) #Not the most scientific but good enough for now
        dat[key].append([moon_phase for i in range(len(moon))])
        sun = get_sun(time).transform_to(altaz).alt.deg
        dat[key].append(sun)
    # now dat is a dict containing transposed csv type lists with contents: [datetime object, Temp, mag/arcsec^2, moon alt, moon phase, sun alt]  
    #We now overwrite the csv's with the newly created data
    overwrite_dir('./sky_bright', dat)
    print('Now the data should be in csv format, check it!')
    #   Clipping data
    #First change data type of the suns altitude to decide where to clip
    data = load_all_csv(dir)
    csv_data = [[],[],[],[],[],[],[],[]]
    for key in data:
        temp = data[key]
        temp[-1] = [float(i) for i in temp[-1]]
        j = None #Something weird happends with the below loop
        k = None
        for j in range(len(temp[-1])): #
            if temp[-1][j] < 1:
                break #J will keep the index of the last point
        if j == None:
            print('j was not defined in iteration')
            j = 0
        for k in range(j+500,len(temp[-1])): #Starting point with conservative offset of 500 TODO: Find out how many datapoints are actually taken
            if temp[-1][k] > 1:
                break
        if k == None:
            print('k was not defined in iteration')
            j = 0
        #We now have our start and stop indices
        #We will now append to a list to save the clipped data
        clipped = np.array(temp,dtype=object)[::,j:k].tolist()
        #First create datetime objects
        clipped[0] = [dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in clipped[0]]
        csv_data[0] += clipped[0] #Save datetime object as well
        csv_data[1] += [(i.date()-i.date().replace(day=1,month=1)).day for i in clipped[0]]
        csv_data[2] += [int((i-i.replace(hour=0, minute=0,second=0)).total_seconds()/60) for i in clipped[0]]
        for i in range(1,len(csv_data)): #Skip dattime object 
            csv_data[i+1] += clipped[i]
        #And now delete unused variables
        del temp, clipped
    
    #Now to remove the downloaded files
    if remove:
        for root, dirs, files in os.walk(dir, topdown=True):
            for i in files:
                os.remove(os.path.join(root, i))

    #And to save the file (in wrong format)
    writer = csv.writer(open(os.path.join(dir, 'Interpolation_Data.csv'), 'w'))
    writer.writerow(['#datetime obj','days from newyear','sec from midnight', 'Temperature', 'Sky Brightness mag/arcsec^2', 'Moon Alt', 'Moon Phase', 'Sun Alt'])
    for row in csv_data:
        writer.writerow(row)
    
            
"""
Astroplan Constraint classes

- SeeingConstraint: To be defined

- RainConstraint: On default constrains for uni observations to < 70%, not implemented for non uni obs

- SkyBrightnessConstraint: Uses interpolation of last years data to predict tonights sky brightness

"""
from astroplan import Constraint
class RainConstraint(Constraint): 
    """
    Constrains Rain.

    For uni observations only, returns percentage rain predicted, if there is 70%+ prob of rain obs wont be scheduled for the time slot 
    
    Parameters
    ----------
    max : `~astropy.units.Quantity` or `None`
        Maximum altitude of the target (inclusive). `None` indicates no limit.
    boolean_constraint : bool
        If True, the constraint is treated as a boolean (True for within the
        limits and False for outside).  If False, the constraint returns a
        float on [0, 1], where 0 is the min altitude and 1 is the max.
    """

    def __init__(self, weather,max=None, boolean_constraint=True):
        if max is None:
            self.max = 0.7
        else:
            self.max = max
        
        rain_prob = weather['Rain_Prob']
        time = [(i-weather['Time'][0]).total_seconds() for i in weather['Time']] #Total seconds since start
        self.norm = weather['Time'][0] #We are going to take this as our starting point
        offset = (weather['Sunset']-dt.datetime.now()).seconds//3600+1 #Add one for good measure
        self.interp = interp1d(time[:18+offset:], rain_prob[:18+offset:],kind='linear') #This is hourly data, we will use the length of the winter solistice night (17-18h) + offset to account for time until sunset
        self.boolean_constraint = boolean_constraint

    def compute_constraint(self, times, observer, targets):
        rain_probs =  self.interp([i.total_seconds() for i in (times.to_datetime()-self.norm)]) #Check that array subtraction works 
        if self.boolean_constraint:
            uppermask = rain_probs <= self.max
            return uppermask


class SkyBrightnessConstraint(Constraint): 
    """
    Constrains SkyBrightness using an interpolation of the last few years. 

    Parameters
    ----------
    max : `~astropy.units.Quantity` or `None`
        Maximum altitude of the target (inclusive). `None` indicates no limit.
    boolean_constraint : bool
        If True, the constraint is treated as a boolean (True for within the
        limits and False for outside).  If False, the constraint returns a
        float on [0, 1], where 0 is the min altitude and 1 is the max.
    """

    def __init__(self, weather, min=None, boolean_constraint=True):
        if min is None:
            self.min = 0
            self.compute = False
        else:
            self.min = min
            self.compute = True
        # Setting up interpolators, one for Temperature and one for seeing

        if self.compute: #TODO: Check array shape should already be transposed
            #First temperature
            temp = weather['Temperature']
            time = [(i-weather['Time'][0]).total_seconds() for i in weather['Time']] #Total seconds since starttime
            self.norm = weather['Time'] #We are going to take this as our time starting point
            self.interp = interp1d(time[:15:], temp[:15:],kind='linear') #Only use 15 hours worth
            #Now sky brightness
            interp_dat = load_all_csv('./sky_bright') #Now the interpolation data should be the only thing there
            for key in interp_dat:
                interp_dat = interp_dat[key]
            interp_dat = interp_dat[1::] #Remove header
            res = interp_dat[-1] #Get sky brightness values
            interp_dat = interp_dat[:-2:] #Get data
            self.nndi = NearestNDInterpolator(interp_dat,res, rescale=True)
        

    def compute_constraint(self, times, observer, targets):
        #Get relevant parameters
        if self.compute:
            days = [(i.date().day-i.date().replace(day=1,month=1)).day for i in times.to_datetime()] 
            secs = [int((i-i.replace(hour=0, minute=0,second=0)).total_seconds()/60) for i in times.to_datetime()]
            Temp = self.interp((times.to_datetime()-self.norm).total_seconds())
            altaz = AltAz(location=observer.location, obstime=times)
            moon = get_moon(times, observer.location).transform_to(altaz).alt.deg
            moon_phase = get_moon_phase(times[0].to_datetime())
            moon_phase = [moon_phase for i in range(len(times))] #Create list of moon phase
            sun = get_sun(times).transform_to(altaz).alt.deg

            sky_brightness = self.nndi(days, secs, Temp, moon,moon_phase,sun)
        else: #No point in computing if no min value provided
            sky_brightness = [1 for i in range(len(times))]
        if self.boolean_constraint:
            uppermask = sky_brightness >= self.max
            return uppermask











#!/usr/bin/python
import ephem

def get_moon_phase(day):
    """Returns a floating-point number from 0-1. where 0=new, 0.5=full, 1=new"""
    try:
        date=ephem.Date(day.date())
    except:
        date = ephem.Date(day) 
    nnm = ephem.next_new_moon    (date)
    pnm = ephem.previous_new_moon(date)

    lunation=(date-pnm)/(nnm-pnm)

    return lunation

"""
General Helper Functions for system interaction




"""



try:
    from win10toast import ToastNotifier
except:
    print('wind10toast not installed')

try:
    from plyer import notification
except:
    print('plyer not installed')


def desktop_notifier(message, Notification_name="Notification"):
    """
    Creates desktop notification
    ----------
    message --> str: The message to be sent
    Notification_name --> str: Name of the Notification
    """
    try:
        notify = ToastNotifier()
        notify.show_toast("Notification", message,icon_path=None,duration=20)
    except:
        notification.notify(title=Notification_name, message=message,app_icon=None,timeout=20)

import requests
def gpt_j(context):
    payload = {
        "context": context,
        "token_max_length": 512,
        "temperature": 1,
        "top_p":0.9,
    }
    response = requests.post("http://api.vicgalle.net:5000/generate", params=payload).json()
    print(response)
    return response

def gpt_j2(context,examples=None,User=None,Bot=None, max_length=100, temperature=0.09, top_probability=1.0,):
    """
    context : str text from whcih the model generates
    examples: dict gives inputs as keys and required outputs as value of key DO NOT USE PERIODS AT THE END OF USER EXAMPLE!
    User: str relevant name for task provided (if examples provided)
    Bot: str relevant name for task provided (if examples provided)
    max_length : int maximum length of output text
    temperature: float creativity of network (high val = high creativity)
    top_probability: float alternative to temperature either of these variables has to be 1 
    
    """
    if examples == None:
        from GPTJ.Basic_api import SimpleCompletion
        query = SimpleCompletion(context, length=max_length, t=temperature, top=top_probability)
        Query = query.simple_completion()
        return Query
    else:
        from GPTJ.gptj_api import Completion
        context_setting = Completion(context, examples)
        response = context_setting.completion(context,
              user=User,
              bot=Bot,
              max_tokens=max_length,
              temperature=temperature,
              top_p=top_probability)
        return response




if __name__ == '__main__':
    create_new_interpolation_dataset('./sky_bright', remove = False)