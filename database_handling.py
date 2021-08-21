
import csv
import sys
import os
from subprocess import call
import json
import numpy as np

approval_folder = r''
databasepath = r''

def parse_approval(): #FIXME: Add daily config backups
    """Parses which files are allowed"""
    f= open(os.path.join(approval_folder, 'approved.txt'),'r')
    file= f.read().split('\n')
    f.close()
    for i in range(len(file)):
        if file[i] == 'approved:':
            app_start = i+1
        elif file[i] == 'not approved:':
            app_end = i
            not_start = i+1
        elif file[i] == 'deferred:':
            not_end = i
            def_start = i+1
        else:
            pass
    #Seperate into the three relevant groups
    app = file[app_start:app_end:]
    not_app = file[not_start:not_end:]
    deferred = file[def_start::]

    #Load config file
    f= open(os.path.join(approval_folder, 'config'),'r')
    config= json.load(f)
    f.close()

    #Split PID's
    app = [j for j in np.array([i.split(',') for i in app]).flatten()]
    not_app = [j for j in np.array([i.split(',') for i in not_app]).flatten()]
    deferred = [j for j in np.array([i.split(',') for i in deferred]).flatten()] #This is simply an index of the files that arent suppose to be touched

    #Most of the processing can be put into this foreloop however to make this more resistant to errors (as we are editing the main config file) several loops will be used
    for i in app:
        try:
            #The two lines below are the only ones which could throw an error
            index = config['To_be_approved_PID'].index(i)#TODO:Check data types int vs str
            config['To_be_approved_PID']=config['To_be_approved_PID'].pop(index)
            config['To_be_completed_PID']=config['To_be_completed_PID'].append(i)
        except: #This can only occure if a non standard way of adding to the config file is used
            print('PID {} was not added to config upon creation, ignored for further processing')
            with open(os.path.join(approval_folder, 'config_error.txt'), 'a') as err_file:
                err_file.write('\nPID: {} was not in config["To_be_approved_PID"], the main source of this error is that the file was not submitted correctly. This is to be avoided as this means that a custom PID was assigned which is not supported by the current implementation')
            #Remove from further processing
            index = app.index(i)#TODO:Check data types int vs str
            app=app.pop(index)
    #We now have now created the relevant PID entries for approved applications

    for i in not_app:
        config['Rejected_PID']=config['Rejected_PID'].append(i)
    #We now appended all the not approved observations PID's to the config file

    for i in app:
        create_obsID_write_to_database(config, i, databasepath)

    
    # TODO: Reset approval file and create backup







def create_obsID_write_to_database(config, PID):
    """ Creates obsID for all observations, then writes to the sql database, sample proposal can be found in create_csv below
    --------
    config --> dict: as retrieved from config file
    PID --> PID of observation for which to add
    """
    #Open Proposal to read relevant data
    file = open(os.path.join(approval_folder, str(PID)+'.csv'))
    proposal = file.read().split('\n') #Removes empty lines
    file.close()
    for i in range(len(proposal)):
        if len(proposal[i])==0: #Remove emptylines
            proposal = proposal.pop(i)
        elif proposal[i][0]=='#': #Remove Comment lines
            proposal = proposal.pop(i)
        else:
            pass
    try:
        Deadline = proposal[4].split(':')[1] #FIXME: Write something more resiliant
    except:
        Deadline = None
    #TODO: Below should be added to overarching PID directory, should also contain columns: LogSheetFile, ObsDate\s
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
        if i == '[EOT]':
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
            catalogue_name = table[0].split('\n')[1]
            #Remove Header
            table = table[2::] #TODO: For each table find rarity and append to both obsID and PID
            for j in table: #Iterate over rows of table
                entry= j.split(',')
                nr_of_times = entry[4]
                #Check if it is a number or not
                try: 
                    nr_of_times = int(nr_of_times)
                except:
                    nr_of_times = 1
                for k in range(nr_of_times): #Iterate over how often this observation has to be done
                    filters = entry[1].split(' ')
                    for l in filters:
                        new_obsids=new_obsids.append(config['obsID'])
                        indiv_obs[config['obsID']]= {   
                                                        'object': catalogue_name
                                                        'PID': PID
                                                        'Filter':l, 
                                                        'exposure': entry[2], 
                                                        'binning':entry[3], 
                                                        'airmass':entry[5],
                                                        'moon':entry[6],
                                                        'seeing':entry[7],
                                                        'sky_brightness':entry[8],
                                                        'Observer_type':observer_type,
                                                        'time_sensitive':time_sensitive,
                                                        'Submission_Date':date,
                                                        'Completed_by':Deadline,
                                                    }
                        Observation['total_length'] += entry[2] #Add exposure length
                        Observation['obsID']=Observation['obsID'].append(config['obsID'])
                        Observation['missing_obsID']=Observation['missing_obsID'].append(config['missing_obsID'])
                        config['obsID'] += 1
            start = end+1 #Create new starting index after [EOT]
        else:
            pass
    
    for i in new_obsids:
        indiv_obs[i]['total_length'] =  Observation['total_length'] #That is total length of PID
        

    #Now we will write to each obsID to the scheduler data base

    #TODO:
    #And each PID to the Observations database

            




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
    object, PID, Filter, exposure, binning, airmass, moon, seeing, sky_brightness, Observer_type, time_sensitive, Submission_Date, Completed_by, total_length
    -----------
    Observations .headers:
    PID, Name, E-Mail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, missing_obsIDs, total_length, logsheet, Obs_days
    ----------
    Completed .headers:
    PID, Name, E-Mail, Phone, Completed_by, Submission_Date, Observer_type, time_sensitive, obsIDs, total_length, logsheet, Obs_days
    """
    #TODO:







def create_csv(file_path=None, submit_file = False):
    """Creates csv file layout to be filled for proposal
    --------
    file_path --> str: path on which to save a copy of the proposal file
    submit_file --> bool: wheter or not a manually filled file is supposed to be submitted
    """
    
    file_content = """#Lauwersoog Observing Request Form
    #All lines starting with a # are instructional comments
    #This file should be Excel Compliant, however please start in the lines below these instructional comments as otherwise parsing will not work
    #Possible Observer Types: Moderator, OA, Staff, Student (Thesis), Student, Outreach/School, Public
    #Below enter your information
    Name:
    E-Mail:
    Phone:
    Reason/Explanation:
    Deadline (if applicable)(dd-mm-YYYY): 
    Date (dd-mm-YYYY):
    Observer Type: 
    Time Sensitive (Yes/No): 
    #For each object you want to observe create a new Table, an example of an observation of two non existent objects from the NGC catalogue is given below
    #After a table for an object is completed an line with content [EOT] is required, empty lines will be ignored
    #The object name should be written as catalogue identifier, space, in catalogue identifier i.e. M 31, NGC 1952
    #Flats do not need to be specified as dusk and dawn flats are taken (provided it is possible in the relevant night)
    #For all columns but the first two if the input is not an integer it will be read as not applicable or the default value will be filled
    #For the first two collumns acceptable strings are: 
    #Image Type = Bias, Dark, Light
    #Filter = R*, G*, B*, H_Alpha, None
    #For the first NGC 9999, all images to be recorded require the same parameters with differnt filters so it is entered in without commas
    #For the second object NGC 9998, all images to be taken are entered seperately
    object: NGC 9999
    Image Type, Filter, Exposure Time (s), Binning, Number of Images, Max Airmass, Max Moon phase (%), Min Seeing, Min Sky Brightness
    Bias, -, -, 1, 5, -,-,-,-
    Dark, -, 120, 1, 5, -,-,-,-
    Light, R* G* B*, 120, 1, 3, -, 50, -, - 
    [EOT]

    object: NGC 9998
    Image Type, Filter, Exposure Time (s), Binning, Number of Images, Max Airmass, Max Moon phase (%), Min Seeing, Min Sky Brightness
    Bias, -, -, 1, 5, -,-,-,-
    Dark, -, 120, 1, 2, -,-,-,-
    Dark, -, 60, 1, 1, -,-,-,-
    Dark, -, 20, 1, 1, -,-,-,-
    Light, H_Alpha, 120, 1, 3, -, 50, -, -
    Light, R*, 60, 1, 1, -, 50, -, - 
    Light, G*, 120, 1, 3, -, 80, -, -
    Light, R*, 60, 1, 1, -, 50, -, - 
    Light, G*, 120, 1, 3, -, 100, -, -
    Light, B*, 20, 1, 1, -, 90, -, - 
    [EOT]

    #Add your observations below
    object:
    Image Type, Filter, Exposure Time (s), Binning, Number of Images, Max Airmass, Max Moon phase (%), Min Seeing, Min Sky Brightness

    """

    if file_path==None:
        file_path = '/tmp/proposal.csv' #TODO: Check if this is acceptable
    elif not submit_file:
        if len(file_path.split('/'))<2:
            print('Please provide a full filepath to avoid problems')
            sys.exit(0)
        if not os.path.isdir(file_path.split('/')[::-2].join('/')):
            print('The containing folder does not appear to exist\nPlease provide an existing file path')
        if file_path[:-4] != '.csv':
            file_path+= file_path+'.csv'
            print('Appended file extension, new filepath: {}'.format(os.path.abspath(file_path)))

    # Create file and open editor if wanted
    if not submit_file:
        while True:
            # Ask which editor to use
            res = input('Which editor would you like to use?\n0-Saves file, 1-nano, 2-vim, 3-vi')
            try:
                with open(file_path, 'w') as file:
                    editor = {0:None,1:'nano',2:'vim',3:'vi'}
                    editor = editor[int(res)]
                    file.write(file_content)
                    if editor == None:
                        #Saves file stops script so user can edit file in own editor
                        print('The file has been saved under {}'.format(os.path.abspath(file_path)))
                        print('You can now download it and edit it in excel or alike')
                        print('To submit this file rerun the script with the filepath and flag: --submit=True') #TODO: Check that the flag is correct
                        sys.exit(0)
                    else:
                        call([editor, file_path])
                    #Leave while loop
                    break
            except:
                print('Invalid option please try again')
                pass
        
        #If the file is to be submitted only
        if submit_file:
            while True:
                print('Moving file {}'.format(os.path.abspath(file_path)))
                res = input('Is that correct and the full filepath? y-yes, n-no')
                if res == 'y':
                    if os.path.isfile(file_path):
                        add_to_approval_file(file_path)
                    else:
                        file_path = input('The file can not be found please enter the complete filepath\n')
                elif res == 'n':
                    file_path = input('Please enter the complete file path\n')


        #This only gets triggered if an editor was used
        while True:
            res = input('Would you like to 0-submit the file for admission 1-save the file for later submission 2-delete the file and terminate script')
            try:
                res = int(res)
                if res > 2: #Raise exception to be caught so that while loop restarts
                    raise Exception('Unrecognized option')
                break
            except:
                print('Invalid option please try again')
                pass
        if res == 0:
            add_to_approval_file(file_path)
        elif res == 1:
            print('The file is saved under {}'.format(os.path.abspath(file_path)))
            print('To submit this file rerun the script with the filepath and flag: --submit=True') #TODO: Check that the flag is correct
            sys.exit(0)
        elif res == 2:
            while True:
                res = input('Are you sure you want to delete the file? y-yes, n-no')
                if res =='y':
                    os.remove(file_path)
                    print('The file has been deleted')
                    sys.exit(0)
                elif res =='n':
                    print('The file is saved under {}'.format(os.path.abspath(file_path)))
                    print('To submit this file rerun the script with the filepath and flag: --submit=True') #TODO: Check that the flag is correct
                    sys.exit(0)
            
            

def add_to_approval_file(file_path):
    """Adds request to folder containing all approval files and index"""
    while True:
        if not os.path.isfile(file_path): #A file check to be sure
            file_path = input('The file can not be found, please enter the full file path\n')
        else:
            break
    if os.path.isfile(os.path.join(approval_folder, 'config')):
        create_config()
    f= open(os.path.join(approval_folder, 'config'),'r')
    config= json.load(f)
    f.close()
    call('cp {} {}'.format(file_path, os.path.join(approval_folder, str(config['PID'])+'.csv')))
    #Add 1 to PID, current set value of PID should always be available
     
    #Obs ID will be assigned later
    #Unrealized PID's will not be reassigned
    config['To_be_approved_PID'].append(config['PID'])
    print('Your assigned PID is: {}'.format(config['PID']))
    print('You will soon be contacted about your observation')
    config['PID'] += 1

    update_config()


def update_config(content):
    """Updates config file with new parameters"""
    with open(os.path.join(approval_folder, 'config'), 'w') as file:
        json.dump(content, file)



def create_config():
    """Creates blank config file"""

    if os.path.isfile(os.path.join(approval_folder, 'config')): #A file check to be sure
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

    with open(os.path.join(approval_folder, 'config'), 'w') as file:
        json.dump(content, file)

