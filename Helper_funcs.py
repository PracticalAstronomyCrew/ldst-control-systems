"""
Custom functions for output and logging
"""
from sqlite3.dbapi2 import Cursor
import sys
import sqlite3





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