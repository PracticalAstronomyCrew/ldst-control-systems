import sys
import os
import sqlite3
import shutil

from Helper_funcs import sqlite_retrieve_table

#TODO: Add status flag
info = """----------------------------------------------------------------------------------
    Usage of arguments
    --PID=int           : your observations PID
    --path=filepath     : absolute file path
    -h                  : Print this

    Usage:
    retrieve_PID.py --PID=1 --filepath='/net/this/dir'    : Loads all PID obs into filepath

    ----------------------------------------------------------------------------------"""
remote_path = '/net/vega/data/users/observatory/LDST/'

args = dict()

def add_to_args(key, value):
    if key == '':
        return
    global args
    if key in ('PATH', 'PID'):
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


def main():

    if 'PATH' in args:
        file_path = args['PATH']
    else:
        file_path = None
    if 'PID' in args:
        PID = args['PID']
    
    move_associated(file_path=file_path, submit_file = PID)


if __name__=='__main__':
    sys.exit(main())