

import multiprocessing
import signal
import sys

#Custom function imports
from Checks import Checks
from Controller import Controller
from Scheduler import Scheduler
from Helper_funcs import dprint, Logger
 

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
            self.Check = Checks()
        if self.id == 2:
            self.Scheduler = Scheduler()
        self.keyboard_interrupt(self.Check, *self.args)

    def keyboard_interrupt(self, func, *args):
        """Helper function, executes func until keyboard interrupt"""
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while not self.exit.is_set():
            func(*args)
        dprint("Process exited")


if __name__ == "__main__":
    #Pass output to logger so that it gets printed and saved
    sys.stdout = Logger(name="Operations_log_{}".format(datetime.date.today()))
    #initiating sub processes
    controller = Process(0)
    controller.start()
    check = Process(1, controller)
    check.start()
    scheduler = Process(2, controller)
    scheduler.start()




