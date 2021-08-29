#!/usr/bin/python3
import sys
import os
import sqlite3
import shutil


#TODO: Add status flag
info = """------------------------------------------------------------------------------------------
    Usage of arguments
    --PID=int           : your observations PID
    --path=filepath     : absolute file path
    --status            : Returns assigned obsID's and which are missing 
    -h                  : Print this

    Usage:
    retrieve_PID.py --PID=1 --filepath='/net/this/dir'    : Loads all PID obs into filepath

    -----------------------------------------------------------------------------------------"""
remote_path = '/net/vega/data/users/observatory/LDST/'

args = dict()

def add_to_args(key, value):
    if key == '':
        return
    global args
    if key in ('PATH', 'PID','STATUS'):
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

def sqlite_retrieve_table(connect, table):
    """
    Retrieves all data from passed sqlite table and returns list of dictionary object
    performs type conversions specific for telescope schedule
    -------------
    connect --> sqlite3.connect(Datbase)
    table --> str: table name
    """
    rows = []
    dict_names = []
    with connect:
        for item in connect.execute('''PRAGMA table_info({});'''.format(table)).fetchall():
            dict_names.append(item[1])
        res = connect.execute('SELECT * FROM {}'.format(table)).fetchall()
        if len(res) != 0:
            for row in res:
                rows.append({dict_names[i]:row[i] for i in range(len(dict_names))})
            #This is a sequence of if else statements given the different key's as some are strings some are ints and some are list strings
            rows = [{key:(rows[i][key] if key in ['Observer_type','Name','EMail','Phone','Filter','object','time_sensitive','priority','Completed_by','Submission_Date','twilight'] else None if rows[i][key]=='None' else rows[i][key][1:-2:].split(',') if key in ['obsIDs', 'missing_obsIDs'] else int(float(rows[i][key]))) for key in rows[i]} for i in range(len(rows))]
        else:
            dprint('file is empty')
    return rows
    
def move_associated(file_path, PID):
    connect = sqlite3.connect(os.path.join(remote_path,'config','Database.db'))
    content = sqlite_retrieve_table(connect, 'Completed')
    for i in content:
        if i['PID'] == PID:
            os.mkdir(os.path.join(file_path, 'logpath'))
            for j in i['Obs_days']:
                for k in i['obsIDs']: 
                    #Copy individual obs id folders
                    copytree(os.path.join(remote_path,j,PID,k),os.path.join(file_path,k))
                #COpy the relevant log sheets
                shutil.copy2(os.path.join(remote_path,'logpath',j),os.path.join(file_path,'logpath',j))
                #Copy the flats dark and biases
                copytree(os.path.join(remote_path,j,PID,'calibration'),os.path.join(file_path,'calibration'))

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def get_status(PID):
    connect = sqlite3.connect(os.path.join(remote_path,'config','Database.db'))
    #Check completed databse
    content = sqlite_retrieve_table(connect, 'Completed')
    for i in content:
        if i['PID'] == PID:
            print('Your observation is completed with obsIDs:\n', i['obsIDs'])
            return 0
    #Check Observations database
    content = sqlite_retrieve_table(connect, 'Observations')
    for i in content:
        if i['PID'] == PID:
            print('Your observation PID: {} is in progress with obsIDs:\n {}\nOf which obsIDs: {} are missing'.format(PID,','.join(i['obsIDs']), ','.join(i['missing_obsIDs'])))
            return 0
    print('Your PID could not be found in the database\nPlease check with an administrator')


def main():

    if 'PATH' in args:
        file_path = args['PATH']
    else:
        file_path = None
    if 'PID' in args:
        PID = args['PID']
    try:
        PID = int(PID)
    except:
        print('PID not recognized as an integer! Please rerun the script with the correct PID')
        return 0
    if 'STATUS' in args:
        get_status(PID)
    else:
        move_associated(file_path=file_path, submit_file = PID)
    return 0


if __name__=='__main__':
    sys.exit(main())