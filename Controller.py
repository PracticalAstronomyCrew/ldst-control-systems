"""
Interacting with the windows software, must be started from python script to work
"""

from pywinauto.application import Application #High level API to interact with windows application using Win32 API and MS UI Automation
from pywinauto.findwindows import ElementNotFoundError
from Helper_funcs import dprint

class GUI_interaction:
    def __init__(self): #TODO: Time init after cpmpletion so that all can be launched prior to sun down
        """
        Initiates all relevant window and sets them up for usage sequentially, stores window information for later control of telescope and dome
        """
        self.apps = {} #Dictionary containing all window interaction objects

        #           Set up AAG CloudWatcher ---> weather station
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\Program Files (x86)\AAG_CloudWatcher.exe') #TODO: Check which backends to use
        except:
            app = Application(backend="win32").start('C:\Program Files (x86)\AAG_CloudWatcher.exe') #TODO: Check which backends to use
            dprint('used win32')
        dlg_spec = app.AAG_CloudWatcherMASTER #TODO: maybe this is correct?
        actionable_dlg = dlg_spec.wait('visible')
        #Get Detailed Window specification:
        dlg_spec = app.window(title='AAG_CloudWatcher MASTER (v8.01.000)')
        try:
            dlg_spec.wrapper_object()
        except ElementNotFoundError as e:
            dprint('Title of application probably wrong')
        # To get possible control sequences print_control_identifiers()
        dlg_spec.Start.clock() #TODO: check ths starts
        #Assign window to dictionary for later usage
        self.apps['AAG'] = dlg_spec

        #       Set up ScopeDome ---> DomeControl
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\ScopeDome\Driver_LS\ASCOM.ScopeDomeUSBDome.exe') #TODO: Check which backends to use
        except:
            app = Application(backend="win32").start('C:\ScopeDome\Driver_LS\ASCOM.ScopeDomeUSBDome.exe') #TODO: Check which backends to use
            dprint('used win32')
        #TODO: run print_control_identifiers() to determine what button to click
        dlg_spec = app.whatisthis #TODO: find relevant interaction name
        actionable_dlg = dlg_spec.wait('visible')
        #Get Detailed Window specification:
        dlg_spec = app.window(title=something) #TODO:
        dlg_spec.OK.click() #This should be the first dialog window
        #TODO: How do i access the next window? Run in jupyter notebook on some windows device
        new_window.wait('visible')# TODO: new_window
        self.apps['ScopeDome'] = new_window


        #       Set up 10micron virtual keypad ---> mount control
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\Program Files (x86)\10micron\VirtKP2\virtkeypad.exe') #TODO: Check which backends to use
        except:
            app = Application(backend="win32").start('C:\Program Files (x86)\10micron\VirtKP2\virtkeypad.exe') #TODO: Check which backends to use
            dprint('used win32')
        #TODO: should be enough unpacking?
        self.apps['virtkeypad'] = app

        #       Set up MaximDL ---> CCD control
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL') #TODO: Check which backends to use
        except:
            app = Application(backend="win32").start('C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL') #TODO: Check which backends to use
            dprint('used win32')
        #TODO: Do unpacking, currently license issues

        #       Set up ACP Planer ---> Scheduler
        try:   #TODO: check if flag: allow_magic_lookup=False should be added due to ambigiosity
            app = Application(backend="uia").start('C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL') #TODO: Check which backends to use
        except: #TODO: Fix location, cant get past shortcut for some reason
            app = Application(backend="win32").start('C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL') #TODO: Check which backends to use
            dprint('used win32')

    def check_processes(self):
        """Monitor weather data and scheduler
        IMPORTANT: This should be running in parallel to CCD control and new scheduler so write independently
        """ #TODO: change bios to auto boot, get some random pc for wake on lan?
        raise Exception('Not Implemented yet')
