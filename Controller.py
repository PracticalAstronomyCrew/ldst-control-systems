"""
Interacting with the windows software, must be started from python script to work
"""

from pywinauto.application import Application #High level API to interact with windows application using Win32 API and MS UI Automation
from pywinauto.findwindows import ElementNotFoundError
from Helper_funcs import dprint
import os

class GUI_interaction:
    def __init__(self): #TODO: Time init after cpmpletion so that all can be launched prior to sun down
        """
        Initiates all relevant window and sets them up for usage sequentially, stores window information for later control of telescope and dome
        """
        self.apps = {} #Dictionary containing all window interaction objects

        #           Set up AAG CloudWatcher ---> weather station
        try:
            app = Application(backend="uia").start('C:\Program Files (x86)\AAG_CloudWatcher\AAG_CloudWatcher.exe')
            app.AAG_CloudWatcher.START2.click()
        except:
            dprint('Restarting AAG_CloudWatcher.exe')
            os.system("TASKKILL /F /IM AAG_CloudWatcher.exe")
            app = Application(backend="uia").start('C:\Program Files (x86)\AAG_CloudWatcher\AAG_CloudWatcher.exe')
            app.AAG_CloudWatcher.START2.click()
        self.apps['AAG'] = app.AAG_CloudWatcher

        #       Set up ScopeDome ---> DomeControl #TODO:
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\ScopeDome\Driver_LS\ASCOM.ScopeDomeUSBDome.exe') #TODO: Check which backends to use
        except:
            app = Application(backend="win32").start('C:\ScopeDome\Driver_LS\ASCOM.ScopeDomeUSBDome.exe') #TODO: Check which backends to use
            dprint('used win32')
        #TODO: run print_control_identifiers() to determine what button to click
        
        self.apps['ScopeDome'] = new_window


        #       Set up 10micron virtual keypad ---> mount control #TODO:
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\Program Files (x86)\10micron\VirtKP2\virtkeypad.exe') #TODO: Check which backends to use
        except:
            app = Application(backend="win32").start('C:\Program Files (x86)\10micron\VirtKP2\virtkeypad.exe') #TODO: Check which backends to use
            dprint('used win32')
        #TODO: should be enough unpacking?
        self.apps['virtkeypad'] = app

        #       Set up MaximDL ---> CCD control
        try:
            app = Application(backend="uia").start('C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL.exe')
        except:
            dprint('Restarting MaxIm_DL.exe')
            os.system("TASKKILL /F /IM MaxIm_DL.exe")
            app = Application(backend="uia").start('C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL.exe')

        #TODO: License issues, finish set up

        #       Set up ACP Planer ---> Scheduler
        try:
            app = Application(backend="uia").start('C:\Program Files (x86)\ACP Obs Control\Planner\ACPPlanGen.exe')
        except:
            dprint('Restarting ACP Planner.exe')
            os.system("TASKKILL /F /IM ACPPlanGen.exe")
            app = Application(backend="uia").start('C:\Program Files (x86)\ACP Obs Control\Planner\ACPPlanGen.exe')

        app['Dialog'].OK.click()
        app['ACP Planner Tips'].CLOSE.click()
        main_win = app['Create Plan for My Observatory']
        self.apps['ACP'] = main_win

    def check_processes(self):
        """Monitor weather data and scheduler
        IMPORTANT: This should be running in parallel to CCD control and new scheduler so write independently
        """ #TODO: change bios to auto boot, get some random pc for wake on lan?
        raise Exception('Not Implemented yet')

