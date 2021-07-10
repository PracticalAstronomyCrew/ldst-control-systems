"""
Custom functions for output and logging
"""
from sqlite3.dbapi2 import Cursor
import sys
import sqlite3
import time
import random
import numpy as np


"""
Telescope Specific functions

add_randome_data --> Adds 99 random observations to be scheduled for Messier objects 1-99


"""


def add_randome_data(nr_of_points):
    """
    Helper Function adding randomised data to the Database
    -------------
    nr_of_points --> int: number of datapoints to add
    """
    #Create and add random dataset to Database:
    connect = sqlite3.connect('Database.db')
    with connect:
        try:
            connect.execute("DROP TABLE Schedule")
        except:
            print('Schedule does not exist')
        connect.execute("""CREATE TABLE Schedule
            (object, time_sensitive, Observer_type, Rarity, total_length, Submission_Date, Completed_by, priority)""")
    observer_types =  ['Moderator', 'OA', 'Staff','Student (Thesis)','Student','Outreach/schools','Public']
    obj = ['M'+str(int(i)) for i in np.linspace(1,99, 99)]
    time_sensitive = [True if i==1 else False for i in np.random.randint(0,2,nr_of_points)] 
    Observer_type = [observer_types[i] for i in np.random.randint(0,7,nr_of_points)]
    Rarity = np.random.randint(1,99,nr_of_points)
    #nr. of. frames * exp.time(multiple of 5 with max 30m) + 2m to move telescope and initiate
    total_length = np.random.randint(1,15,nr_of_points)*np.random.randint(1,6)*5+2
    #In order day - month - year
    Submission_Date = [random_date("1-1-2020", "5-7-2021", random.random()) for i in range(nr_of_points)]
    Completed_by = [random_date("5-7-2021", "30-12-2021", random.random()) for i in range(nr_of_points)]
    Random_Schedule = [[obj[i], time_sensitive[i], Observer_type[i],Rarity[i],total_length[i],Submission_Date[i], Completed_by[i],None] for i in range(nr_of_points)]
    for i in range(nr_of_points):
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
            rows = [{key:(rows[i][key] if key=='Observer_type' or  key=='object' or key=='time_sensitive' or key=='priority' or key=='Completed_by' or key=='Submission_Date' else int(rows[i][key])) for key in rows[i]} for i in range(len(rows))]
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
