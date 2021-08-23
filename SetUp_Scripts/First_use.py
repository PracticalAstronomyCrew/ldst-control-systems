
import sys
import os
import time
import json
import sqlite3
from astropy.utils import data

import numpy as np

file_path = os.path.abspath(r'C:/LDST/')


"""Below First usage set up"""

def create_sql_database():
    """Create empty SQL database ready for usage

    THIS SHOULD NOT BE RUN!
    This could replace the original file and should only be run if you are aware of the implications

    -----------
    contains 3 tables:
    Schedule, Observations, Completed
    -----------
    Schedule will contain each individual obsID entry
    Observations will contain each individual PID entry
    Completed will contain each individual completed PID entry
    -------------
    Schedule .headers:
    obsID, object, PID, Filter, exposure, binning, airmass, moon, seeing, sky_brightness, Observer_type, time_sensitive, Submission_Date, Completed_by, total_length, rarity, exposures
    -----------
    Observations .headers:
    PID, Name, E-Mail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, missing_obsIDs, total_length, logsheet, Obs_days
    ----------
    Completed .headers:
    PID, Name, E-Mail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, total_length, logsheet, Obs_days
    """
    databasepath = os.path.join(file_path, 'config', 'Database.db')
    f = open(databasepath, 'x')
    f.close()
    
    connect = sqlite3.connect(databasepath)

    connect.execute("""CREATE TABLE Observations
            (PID, Name, EMail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, missing_obsIDs, total_length, logsheet, Obs_days)""")
    
    connect.execute("""CREATE TABLE Schedule
        (obsID, object, PID, Filter, exposure, binning, airmass, moon, seeing, sky_brightness, Observer_type, time_sensitive, Submission_Date, Completed_by, total_length, Rarity,number_of_exposures)""")
    
    connect.execute("""CREATE TABLE Completed
        (PID, Name, E-Mail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, total_length, logsheet, Obs_days)""")



def create_config():
    """Creates blank config file"""

    if os.path.isfile(os.path.join(file_path, 'config')): #A file check to be sure
        raise Exception('Config file already exists!')
    
    content = {}
    content['PID'] = 1
    content['obsID'] = 1
    content['To_be_approved_PID'] = []
    content['To_be_completed_PID'] = []
    content['To_be_completed_obsID'] = []
    content['Rejected_PID'] = []
    content['Completed_PID'] = []
    content['Completed_obsID'] = []

    with open(os.path.join(file_path, 'config'), 'w') as file:
        json.dump(content, file)


def create_folders():
    """Function to create structure of directory"""
    check_and_create(file_path, 'logs')
    check_and_create(file_path, 'logsheets')
    check_and_create(file_path, 'backups')
    check_and_create(file_path, 'backups', 'configs')
    check_and_create(file_path, 'backups', 'Databases')
    check_and_create(file_path, 'config')
    check_and_create(file_path, 'sky_bright')


def check_and_create(*args):
    directory = os.path.join(*args)
    if not os.path.isdir(directory):
        os.mkdir(directory)



if __name__=='__main__':
    print('This will initiate a new set of configs, the script will wait 1 minute prior to writing files')
    time.sleep(60)
    create_folders()
    create_config()
    create_sql_database()
    print('Created directory structure, a new config, and an empty sql database')

