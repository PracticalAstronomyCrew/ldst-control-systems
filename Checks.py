from astropy.coordinates import SkyCoord, EarthLocation
import astropy.coordinates as coord
from astropy import time


def Checks():
    def __init__(self, Controller):
        """
        Class meant to run as subprocess eventually interrupting execution of the other in case of arrising problems
        """
        self.Controller = Controller
        self.location = EarthLocation(53.3845258962902, 6.23475766593151) #Telescope coordinates

        if self.Controller.dome.open: #Checks if dome is open, 
            self.start()
            print('Dome open on start of script!')



    def start(self):
        """This function will be run in combination with dome.open(), it invokes all below functions to check for weather sun and so on"""
        while self.Controller.dome.open:
            self.check_weather()
            sun = get_sun(time.Time.now()).transform_to(AltAz(location=self.location)) #TODO: include refraction effects in pressure attribute?
            if sun.alt.deg>0: #Checks if sun angle in AltAz is positive i.e. is it visible or not
                self.check_sun()



    def check_sun(self):
        """
        Checks if the sun could damage the telescope
        """
        sun_now = get_sun(time.Time.now()).transform_to(AltAz(location=self.location))
        if sun_now.seperation()



    def check_weather(self):
        """
        Gets data from weather station and closes dome in case of issues
        """
        get_data_from_weather_station() #TODO: 
        if weather_ok:
            return 0
        else:
            dome.close() #TODO: Add power saving settings and so on
            while not weather_ok:
                get_data_from_weather_station()
                time.sleep(60)
            #Above iterates untill allowed to continue
            dome.open()
            return 0