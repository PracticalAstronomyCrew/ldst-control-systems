from Controller import Telescope
from astropy.coordinates import SkyCoord, EarthLocation, Angle, AltAz
import astropy.coordinates as coord
from astropy.time import Time
import time

#Function imports from the same directory
from Helper_funcs import dprint

class Checks:
    def __init__(self, Controller):
        """
        Class meant to run as subprocess eventually interrupting execution of the other in case of arrising problems
        """
        self.Dome = Controller.Dome
        self.Telescope = Controller.Telescope
        self.con = Controller.con
        self.location = EarthLocation(53.3845258962902, 6.23475766593151) #Telescope coordinates

        if self.Dome.open: #Checks if dome is open, 
            dprint('Dome open on start of script!')
            sun = get_sun(Time.now()).transform_to(AltAz(location=self.location)) #TODO: include refraction effects though pressure,temperature, relative_humidity
            if sun.alt.deg>0: #Checks if sun angle in AltAz is positive i.e. is it visible or not
                dprint('Dome open while the Sun is out!')
                self.Dome.close()
                domestat= ('open' if self.Dome.open else 'closed')
                #Write to database everytime something mechanical happens
                cur.execute("""INSERT INTO observatory_status VALUES
                ('{}', '{}', '[{}, {}]', '[{}, {}]')""".format(dt.datetime.now(), domestat, self.Dome.direction[0], self.Dome.direction[1], self.Telescope.orientation[0],self.Telescope.orientation[1]))
                con.commit()
                self.sun_set()
            self.start()
            

    def start(self):
        """This function will be run in combination with dome.open(), it invokes all below functions to check for weather, sun and so on"""
        dprint('Starting Checks')
        while self.Dome.open:
            self.check_weather()
        dprint('Dome closed')
    
    def sun_set(self):
        """Determines sun set and modifies a powershell script to run the script at the specific time"""
        #TODO: Write this
        #TODO: Create seperate function which runs everyday doing this

        dprint('Modifying powershell script to restart at {}'.format(sun_set_time))


    def check_weather(self):
        """
        Gets data from weather station and closes dome in case of issues

        Not required!
        """
        get_data_from_weather_station() #TODO: 
        if weather_ok:
            return 0
        else:
            self.Dome.close() #TODO: Add power saving settings and so on
            dprint('Closed dome due to weather conditions')
            domestat= ('open' if self.Dome.open else 'closed')
                #Write to database everytime something mechanical happens
            cur.execute("""INSERT INTO observatory_status VALUES
                ('{}', '{}', '[{}, {}]', '[{}, {}]')""".format(dt.datetime.now(), domestat, self.Dome.direction[0], self.Dome.direction[1], self.Telescope.orientation[0],self.Telescope.orientation[1]))
            con.commit()
            while not weather_ok:
                get_data_from_weather_station()
                time.sleep(60)
            #Above iterates untill allowed to continue
            self.Dome.open()
            domestat= ('open' if self.Dome.open else 'closed')
                #Write to database everytime something mechanical happens
            cur.execute("""INSERT INTO observatory_status VALUES
                ('{}', '{}', '[{}, {}]', '[{}, {}]')""".format(dt.datetime.now(), domestat, self.Dome.direction[0], self.Dome.direction[1], self.Telescope.orientation[0],self.Telescope.orientation[1]))
            con.commit()
            #Restart
            self.start()
            return 0





#Get sunset and sunrise form astropy.time or others