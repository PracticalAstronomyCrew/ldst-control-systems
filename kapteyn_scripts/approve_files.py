#!/usr/bin/python3
import sqlite3
import os
import json
import sys
import shutil
from subprocess import call
import datetime as dt
import numpy as np

# This script is for the person taking care of approving observations

approval_folder = '/net/vega/data/users/observatory/LDST/approval/'
remote_path = '/net/vega/data/users/observatory/LDST/'



def parse_approval(): 
    """Parses which files are allowed"""
    f= open(os.path.join(approval_folder, 'approved.txt'),'r')
    file= f.read().split('\n')
    f.close()
    for i in range(len(file)):
        if file[i] == 'approved':
            app_start = i+1
        elif file[i] == 'not approved':
            app_end = i
            not_start = i+1
        elif file[i] == 'deferred':
            not_end = i
            def_start = i+1
        else:
            pass
    #Seperate into the three relevant groups
    app = file[app_start:app_end:]
    not_app = file[not_start:not_end:]
    deferred = file[def_start::]

    #Load and backup config file
    print('Backing up config and database before modification, saved under .../LDST/backups/... with todays date as its name')
    f= open(os.path.join(remote_path,'config', 'config'),'r')
    config= json.load(f)
    f.close()
    with open(os.path.join(remote_path, 'backups', 'configs','{}'.format(dt.date.today().strftime('%Y%m%d'))), 'w') as file:
        json.dump(config, file)
    shutil.copy2(os.path.join(remote_path,'config', 'config'),os.path.join(remote_path, 'backups', 'configs','{}'.format(dt.date.today().strftime('%Y%m%d'))))
    shutil.copy2(os.path.join(remote_path,'config', 'Database.db'),os.path.join(remote_path, 'backups', 'Databases','{}.db'.format(dt.date.today().strftime('%Y%m%d'))))

    #Split PID's
    if len(''.join(app))>0:
        app = [int(j) for j in np.array([i.split(',') for i in app]).flatten()]
    else:
        app = []
    if len(''.join(not_app))>0:
        not_app = [int(j) for j in np.array([i.split(',') for i in not_app]).flatten()]
    else:
        not_app=[]
    if len(''.join(deferred))>0:
        deferred = [int(j) for j in np.array([i.split(',') for i in deferred]).flatten()] #This is simply an index of the files that arent suppose to be touched
    else:
        deferred =[]

    #Most of the processing can be put into this foreloop however to make this more resistant to errors (as we are editing the main config file) several loops will be used
    new_app = False
    for i in app:
        try:
            #The two lines below are the only ones which could throw an error
            index = config['To_be_approved_PID'].index(i)
            config['To_be_approved_PID'].pop(index)
            config['To_be_completed_PID'].append(i)
        except: #This can only occure if a non standard way of adding to the config file is used
            print('PID {} was not added to config upon creation, ignored for further processing')
            with open(os.path.join(approval_folder, 'config_error.txt'), 'a') as err_file:
                err_file.write('\nPID: {} was not in config["To_be_approved_PID"], the main source of this error is that the file was not submitted correctly. This is to be avoided as this means that a custom PID was assigned which is not supported by the current implementation'.format(i))
            #Remove from further processing
            index = app.index(i)
            new_app=app.pop(index)
    if type(new_app)==list:
        app = new_app
    #We now have now created the relevant PID entries for approved applications

    for i in not_app:
        config['Rejected_PID'].append(i)
    #We now appended all the not approved observations PID's to the config file

    for i in app:
        config = create_obsID_write_to_database(config, i)

    
    # Reset approval file and create backups

    #Folder management
    if not os.path.isdir(os.path.join(approval_folder, 'backups')):
        os.mkdir(os.path.join(approval_folder, 'backups'))

    if not os.path.isdir(os.path.join(approval_folder, 'backups','proposals')):
        os.mkdir(os.path.join(approval_folder, 'backups','proposals'))
    
    if not os.path.isdir(os.path.join(approval_folder, 'backups','proposals','approved')):
        os.mkdir(os.path.join(approval_folder, 'backups','proposals','approved'))
    
    if not os.path.isdir(os.path.join(approval_folder, 'backups','proposals','rejected')):
        os.mkdir(os.path.join(approval_folder, 'backups','proposals','rejected'))
    
    if not os.path.isdir(os.path.join(approval_folder, 'backups','approval_files')):
        os.mkdir(os.path.join(approval_folder, 'backups','approval_files'))

    #Move approved and disapproved csv's
    for i in app:
        orig_path = os.path.join(approval_folder, str(i)+'.csv')
        approv_path = os.path.join(approval_folder, 'backups','proposals','approved',str(i)+'.csv')
        call(['mv',orig_path, approv_path])

    for i in not_app:
        orig_path = os.path.join(approval_folder, str(i)+'.csv')
        not_approv_path = os.path.join(approval_folder, 'backups','proposals','rejected',str(i)+'.csv')
        call('mv {} {}'.format(orig_path, not_approv_path))

    #Reset approval file
    content = 'approved\n\nnot approved\n\ndeferred\n'
    f= open(os.path.join(approval_folder, 'approved.txt'),'w')
    f.write(content)
    f.close()

    update_config(remote_path, config)

    return 0


def create_obsID_write_to_database(config, PID):
    """ Creates obsID for all observations, then writes to the sql database, sample proposal can be found in create_csv below
    --------
    config --> dict: as retrieved from config file
    PID --> PID of observation for which to add
    """
    #Open Proposal to read relevant data
    file = open(os.path.join(approval_folder, str(PID)+'.csv'))
    proposal = file.read().split('\n')
    file.close()
    prop_text = []
    for i in range(len(proposal)):
        if len(proposal[i])==0: #Remove emptylines
            pass
        elif proposal[i][0]=='#': #Remove Comment lines
            pass
        else:
            prop_text.append(proposal[i])
    proposal = prop_text
    try:
        Deadline = proposal[4].split(':')[1] 
    except:
        Deadline = None
    date = proposal[6].split(':')[1]
    observer_type = proposal[7].split(':')[1]
    time_sensitive = proposal[8].split(':')[1]
    Observation = { 'PID':PID,
                    'Name':proposal[0].split(':')[1],
                    'E-Mail':proposal[1].split(':')[1],
                    'Phone':proposal[2].split(':')[1],
                    'Completed_by':Deadline,
                    'Submission_Date':date,
                    'Observer_type':observer_type,
                    'time_sensitive':time_sensitive,
                    'obsIDs':[],
                    'missing_obsIDs':[],
                    'total_length':0,
                    }
    #Below is a container for each individual obsID
    indiv_obs= {}
    proposal = proposal[8::]
    EOT = 0
    for i in range(len(proposal)):
        if '[EOT]' in proposal[i]:
            EOT+=1
            if EOT == 2:
                break #Gets index of second example, rest of file will be actual observations
    proposal = proposal[i+1::]
    start = 0

    # The below loop splits the proposal into several tables and iterates each, when a column is found a new obsID will be assigned 
    # one for each image to be taken
    new_obsids = []
    for i in range(len(proposal)):
        if proposal[i] == '[EOT]':
            #Gets index of end of table
            end = i
            #Get table only
            table = proposal[start:end:]
            #Get name
            catalogue_name = table[0].split(':')[1]
            #Remove Header
            table = table[2::]
            for j in table: #Iterate over rows of table
                entry= j.split(',')
                nr_of_times = entry[3]
                #Check if it is a number or not
                try: 
                    nr_of_times = int(nr_of_times)
                except:
                    nr_of_times = 1
                filters = entry[0].split(' ')
                for l in filters:
                    #Below so that different notations dont mess up the scheduling
                    filter_option = {'H':'H_alpha', 'R':'R*', 'G':'G*', 'B':'B*','N':'Filter 16','L':'Lum'}
                    filter = filter_option[l[0].strip(' ').upper()]
                    new_obsids.append(config['obsID'])
                    indiv_obs[config['obsID']]= {   
                                                    'object': catalogue_name,
                                                    'PID': PID,
                                                    'Filter':filter, 
                                                    'exposure': entry[1], 
                                                    'binning':entry[2], 
                                                    'number_of_exposures':entry[3],
                                                    'airmass':entry[4],
                                                    'moon':entry[5],
                                                    'seeing':entry[6],
                                                    'twilight':entry[7],
                                                    'sky_brightness':entry[8],
                                                    'Observer_type':observer_type,
                                                    'time_sensitive':time_sensitive,
                                                    'Submission_Date':date,
                                                    'Completed_by':Deadline,
                                                    'Rarity':None
                                                }
                    Observation['total_length'] += int(entry[2]) #Add exposure length
                    Observation['obsIDs'].append(config['obsID'])
                    Observation['missing_obsIDs'].append(config['obsID'])
                    config['obsID'] += 1
            start = end+1 #Create new starting index after [EOT]
        else:
            pass
    
    for i in new_obsids:
        indiv_obs[i]['total_length'] =  Observation['total_length'] #That is total length of PID

    #Now we will write to each obsID to the schedule data base
    databasepath = os.path.join(remote_path, 'config', 'Database.db')

    connect = sqlite3.connect(databasepath)

    for i in new_obsids:
        #Get the values in the correct order
        keys = ('object', 'PID', 'Filter', 'exposure', 'binning', 'airmass', 'moon', 'seeing', 'sky_brightness', 'Observer_type', 'time_sensitive', 'Submission_Date', 'Completed_by', 'total_length', 'Rarity','number_of_exposures', 'twilight')
        #first i will be the obsID
        to_add = [i,*[indiv_obs[i][key] for key in keys]]
        sqlite_add_to_table(connect, 'Schedule', to_add)

    #And each PID to the Observations database
    keys = ('PID', 'Name', 'E-Mail', 'Phone', 'Completed_by', 'Submission_Date', 'Observer_type', 'time_sensitive', 'obsIDs', 'missing_obsIDs', 'total_length', 'logsheet', 'Obs_days')
    #Below None since parameters like Obs_days will be added after observations
    to_add = [Observation[i] if i in Observation.keys() else None for i in keys]
    sqlite_add_to_table(connect, 'Observations', to_add)

    return config



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

def update_config(local_dir,content):
    """Updates config file with new parameters"""
    with open(os.path.join(local_dir, 'config','config'), 'w') as file:
        json.dump(content, file)


if __name__ == '__main__':
    sys.exit(parse_approval())