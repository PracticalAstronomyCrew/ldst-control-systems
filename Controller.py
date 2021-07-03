
from astropy.coordinates import SkyCoord, EarthLocation
import sqlite3
import datetime as dt

#Function imports from the same directory
from Helper_funcs import dprint, sqlite_retrieve_table

"""
INDI or ASCOM?
https://www.indilib.org/develop/indi-python-bindings.html

https://www.ascom-standards.org/About/Projects.html

"""

class Dome:
    def __init__(self,obs_status):
        """
        Class to control the dome
        """
        #Check if the observatory has been used without registration
        res = self.check_state()
        for key in res:
            if res[key] != obs_status[key]:
                dprint('Observatory has been used without registration')
        self.open=(True if obs_status['dome_status']=='open' else False)

    def open(self):
        """
        Open's the dome
        """
        #TODO:
        self.open = True
        self.direction = [left_ang, right_ang]

    def close(self):
        """
        Closes the Dome
        """
        #TODO:
        self.open = False
        #Still get the direction
        self.direction = [left_ang, right_ang]
    
    def check_state(self):
        """
        Retrieve wheter or not open and angle of the dome
        """
        #TODO:

    def rotate(self):
        """
        Rotates the Dome
        """
        #TODO:
        self.direction = [left_ang, right_ang]





class Telescope:
    def __init__(self,obs_status):
        """
        Class to control Telescope
        """
        res = self.check_state()
        for key in res:
            if res[key] != obs_status[key]:
                dprint('Observatory has been used without registration')

    
    def slew(self, alt, az):
        """Slews the telescope and writes new orientation to self.orientation"""
        #TODO:
        self.orientation = [alt, az]

    def get_direction(self):
        """Gets the direction the telescope is currently looking towards"""
        #TODO: 

    def start_imaging(self,im_nr, exp_time):
        """
        Starts observational sequence
        ------------------
        in_nr --> int: Number of images to take
        exp_time --> int/list: Exposure time of each image (seconds)
        """
        for i in range(im_nr):
            if type(exp_time)==int:
                #TODO:
                do_the_thing()
            if type(exp_time)==list:
                #TODO:
                do_the_thing(exp_time[i])



class Controller:
    def __init__(self):
        """Packager for controll classes"""
        self.con = sqlite3.connect('Database.db')
        #Get previous usage data to see if the telescope has been used
        try:
            dat = sqlite_retrieve_table(self.con,'observatory_status')[-1]
        except:
            dprint('No prior usage registered')
            dat = {key: None for key in sqlite_get_columns(self.con, 'observatory_status').strip('()').split(', ')}
        self.Dome = Dome(dat)
        self.Telescope = Telescope(dat)
        
