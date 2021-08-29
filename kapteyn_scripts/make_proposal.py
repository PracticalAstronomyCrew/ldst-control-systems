#!/usr/bin/python3
import sys
import json
from subprocess import call
import os
import time


approval_folder = '/net/vega/data/users/observatory/LDST/approval/'
remote_path = '/net/vega/data/users/observatory/LDST/'

info = """----------------------------------------------------------------------------------
    Usage of arguments
    --path = file path  : file path under which the file is either created or submitted from
    --submit = bool     : wheter or not to submit a pre existing file
    -h                  : Print this

    Usage:
    make_proposal.py                                            : Creates file and opens in editor

    make_proposal.py --path =/tmp/proposal.csv                  : Creates file in path and opens in editor

    make_proposal.py --path =/tmp/proposal.csv --submit=True    : Submit file from path
    ----------------------------------------------------------------------------------"""

args = dict()

def add_to_args(key, value):
    if key == '':
        return
    global args
    if key in ('PATH', 'SUBMIT'):
        if value != '-':
            args[key] = [value]
    else:
        sys.exit('Unknown key %s' % key)
    return

def get_arguments():
    for arg in sys.argv[1:]:
        if arg[0:2] == '--':
            opt = arg[2:].strip().upper()
            valpos = opt.find('=')
            if valpos != -1:
                key, value = opt.split('=')
            add_to_args(key=key.strip(), value=value.strip())
        elif arg[0:2] == '-h':
            print(info)
            sys.exit(0)
    return



def create_csv(file_path=None, submit_file = False):
    """Creates csv file layout to be filled for proposal
    --------
    file_path --> str: path on which to save a copy of the proposal file
    submit_file --> bool: wheter or not a manually filled file is supposed to be submitted
    """
    file_content = """#Lauwersoog Observing Request Form
#Seeing not implemented yet; any value placed will be ignored!
#All lines starting with a # are instructional comments
#This file should be Excel Compliant; however please start in the lines below these instructional comments as otherwise parsing will not work
#Possible Observer Types: Moderator; OA; Staff; Student (Thesis); Student; Outreach/School; Public
#Below enter your information
Name:
E-Mail:
Phone:
Reason/Explanation:
Deadline (if applicable)(dd-mm-YYYY): 
Date (dd-mm-YYYY):
Observer Type: 
Time Sensitive (Yes/No): 
#For each object you want to observe create a new Table; an example of an observation of two non existent objects from the NGC catalogue is given below
#After a table for an object is completed an line with content [EOT] is required; empty lines will be ignored
#The object name should be written as catalogue identifier; space; in catalogue identifier i.e. M 31; NGC 1952
#Flats do not need to be specified as dusk and dawn flats are taken (provided it is possible in the relevant night)
#For all columns but the first two if the input is not an integer it will be read as not applicable or the default value will be filled
#For the first collumn acceptable strings are
#Filter = Lum; R*; G*; B*; H_alpha; None 
#For the twilight constraint acceptable answers are (do keep in mind that astronomical sunset is not reached in summer; civili twilight is a constraint always imposed):
#Twilight = civil;nautical;astronomical
#For the first NGC 9999; all images to be recorded require the same parameters with differnt filters so it is entered in without commas
#For the second object NGC 9998; all images to be taken are entered seperately
object: NGC 9999
Filter, Exposure Time (s), Binning, Number of Images, Max Airmass, Max Moon phase (%), Min Seeing, Twilight, Min Sky Brightness
R* G* B*, 120, 1, 3, -, 50, -, -,-
[EOT]

object: NGC 9998
Filter, Exposure Time (s), Binning, Number of Images, Max Airmass, Max Moon phase (%), Min Seeing, Twilight, Min Sky Brightness
H_alpha, 120, 1, 3, -, 50, -,astronomical, -
R*, 60, 1, 1, -, 50, -, - 
G*, 120, 1, 3, -, 80, -, -
R*, 60, 1, 1, -, 50, -, - 
G*, 120, 1, 3, -, 100, -, -
B*, 20, 1, 1, -, 90, -, - 
[EOT]

#Add your observations below
object:
Filter, Exposure Time (s), Binning, Number of Images, Max Airmass, Max Moon phase (%), Min Seeing, Twilight, Min Sky Brightness
"""

    if file_path==None:
        file_path = '/tmp/proposal.csv'
    elif submit_file:
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
            res = input('Which editor would you like to use?\n0-Saves file, 1-nano, 2-vim, 3-vi\n')
            try:
                with open(file_path, 'w') as file:
                    editor = {0:None,1:'nano',2:'vim',3:'vi'}
                    editor = editor[int(res)]
                    file.write(file_content)
                if editor == None:
                    #Saves file stops script so user can edit file in own editor
                    print('The file has been saved under {}'.format(os.path.abspath(file_path)))
                    print('You can now download it and edit it in excel or alike')
                    print('To submit this file rerun the script with the filepath and flag: --submit=True')
                    sys.exit(0)
                else:
                    #time.sleep(1)
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
                res = input('Is that correct and the full filepath? y-yes, n-no\n')
                if res == 'y':
                    if os.path.isfile(file_path):
                        add_to_approval_file(file_path)
                    else:
                        file_path = input('The file can not be found please enter the complete filepath\n')
                elif res == 'n':
                    file_path = input('Please enter the complete file path\n')


        #This only gets triggered if an editor was used
        while True:
            res = input('Would you like to 0-submit the file for admission 1-save the file for later submission 2-delete the file and terminate script\n')
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
            print('To submit this file rerun the script with the filepath and flag: --submit=True')
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
                    print('To submit this file rerun the script with the filepath and flag: --submit=True') 
                    sys.exit(0)
            
            

def add_to_approval_file(file_path):
    """Adds request to folder containing all approval files"""
    while True:
        if not os.path.isfile(file_path): #A file check to be sure
            file_path = input('The file can not be found, please enter the full file path\n')
        else:
            break
    if not os.path.isfile(os.path.join(remote_path,'config', 'config')):
        print('Warning: Please contact the person in charge of the Observatory the config files can not be found, your request is located in {}'.format(file_path))
        sys.exit(0)
    f= open(os.path.join(remote_path,'config', 'config'),'r')
    config= json.load(f)
    f.close()
    call('cp {} {}'.format(file_path, os.path.join(approval_folder, str(config['PID'])+'.csv')))
    #Obs ID will be assigned after approval
    #Unrealized PID's will not be reassigned
    config['To_be_approved_PID'].append(config['PID'])
    print('Your assigned PID is: {}'.format(config['PID']))
    print('You will soon be contacted about your observation')
    config['PID'] += 1
    update_config(config)


def update_config(local_dir,content):
    """Updates config file with new parameters"""
    with open(os.path.join(local_dir, 'config','config'), 'w') as file:
        json.dump(content, file)


def main():
    get_arguments()

    if 'PATH' in args:
        file_path = args['PATH']
    else:
        file_path = None
    if 'SUBMIT' in args:
        submit_file = args['SUBMIT']
    else:
        submit_file = False
    
    create_csv(file_path=file_path, submit_file = submit_file)


if __name__=='__main__':
    sys.exit(main())