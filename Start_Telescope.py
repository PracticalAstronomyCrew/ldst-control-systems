

import multiprocessing
import signal


#Custom function imports
from .Checks import Checks
from .Controller import Controller
from .Scheduler import Scheduler

class Logger(object):
    '''Class that redirects output to terminal and log file
    https://stackoverflow.com/questions/20525587/python-logging-in-multiprocessing-attributeerror-logger-object-has-no-attrib'''
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("Operations_log_{}".format(datetime.date.today()), 'a')
    
    def __getattr__(self, attr):
        return getattr(self.terminal, attr)

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  
        
    def flush(self):
        pass  

class Process(multiprocessing.Process):
    def __init__(self, id, *args):
        """
        This class will handle each running class/script, this is so that the Checks class can constantly be running and interrupt other processes
        --------------------------
        id --> 0,1,2 - determines which class is to be run
        args --> already running class to be passed to others
        """
        super(Process, self).__init__()
        self.id = id
        self.args = args
    
    def run(self):
        time.sleep(1)
        if self.id == 0:
            self.Controller = Controller()
        if self.id == 1: #TODO: Initiate relevant functions within self.keyboard_interrupt(), for all 3 id's
            self.Check = Checks
            self.keyboard_interrupt(self.Check, *self.args)
        if self.id == 2:
            self.Scheduler = Scheduler()

    def keyboard_interrupt(self, func, *args):
        """Helper function, executes func until keyboard interrupt"""
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while not self.exit.is_set():
            func(*args)
        print("Process exited")



if __name__ == "__main__":
    import sys
    #Below so that terminal output gets written to log file and terminal
    sys.stdout = Logger()
    controller = Process(0)
    controller.start()
    check = Process(1, controller)
    check.start()
    scheduler = Process(2)
    scheduler.start()



