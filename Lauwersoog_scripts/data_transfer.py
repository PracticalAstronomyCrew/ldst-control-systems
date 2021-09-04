


"""
Using SFTP protocoll to transfer files using ssh, with the python client fabric
"""
import os
from threading import local
import logger
from fabric import Connection, config
import datetime as dt
import logging
import json
import sqlite3

from Helper_funcs import sqlite_get_tables,sqlite_retrieve_table
#The below contain several folders, one for each observation, and maybe some more subfolders for each filter or config file

logger = logging.getLogger('main.data')
logger.debug("starting data logger")

def backup_config(local_dir):
    """Move the config and Database to a backup folder to see daily difference"""
    logger.info('Moving config and database file to backups')
    os.rename(os.path.join(local_dir, 'config', 'config'),os.path.join(local_dir, 'backups', 'configs','{}'.format(dt.date.today().strftime('%Y%m%d'))))
    os.rename(os.path.join(local_dir, 'config', 'Database.db'),os.path.join(local_dir, 'backups','Databases', '{}.db'.format(dt.date.today().strftime('%Y%m%d'))))
    if not os.path.isfile(os.path.join(local_dir, 'backups','Interpolation_Data.csv')):
        logger.warning('No backup for Interpolation_Data.csv found, writing now')
        if os.path.isfile(os.path.join(local_dir, 'sky_bright','Interpolation_Data.csv')):
            f = open(os.path.join(local_dir, 'sky_bright','Interpolation_Data.csv'),'r')
            cont = f.read()
            f.close()
            with open(os.path.join(local_dir, 'backups','Interpolation_Data.csv')) as f:
                f.write(cont)
        else:
            logger.warning("No Interpolation Data present!")

def get_config_database(file_path, remote_path):
    """Retrieve new config and Database"""
    gate = Connection(host='kapteyn.astro.rug.nl', user='telescoop', forward_agent = True, connect_kwargs = {'allow_agent':True})
    c = Connection(host='virgo11', user='telescoop',gateway=gate, forward_agent = True, connect_kwargs = {'allow_agent':True})
    c.open()
    c.get(os.path.join(remote_path, 'config','config'), os.path.join(file_path, 'config','config'))
    c.get(os.path.join(remote_path, 'config','Databse.db'), os.path.join(file_path, 'config','Database.db'))
    c.close()



def update_config(local_dir,content):
    """Updates config file with new parameters"""
    with open(os.path.join(local_dir, 'config','config'), 'w') as file:
        json.dump(content, file)

def send_results(local_dir,remote_dir):
    """Creates ssh connection to kapteyn and sends files from and to above specified filepaths"""
    gate = Connection(host='kapteyn.astro.rug.nl', user='telescoop', forward_agent = True, connect_kwargs = {'allow_agent':True})
    c = Connection(host='virgo11', user='telescoop',gateway=gate, forward_agent = True, connect_kwargs = {'allow_agent':True})
    c.open()
    send_dir(local_dir,remote_dir,c)
    send_config(local_dir,remote_dir,c)
    c.close()


def send_dir(local_dir,remote_dir, connection):
    """ In its essence this simply copies a directory over sftp
    Sends contents of directory local_dir to remote_dir on station,
    First creates directories
    then sends files

    It skips all existing files as they would otherwise be overwritten so things like config and Database need to be passed seperately
    """
    os.chdir(local_dir) #Moves current operating directory
    logger.debug('Moved effective directory to {}'.format(local_dir))
    for root, dirs, files in os.walk(".", topdown = False): #Walks the directory top down
        #Root refers to the currently listed dir in root, local dir corresponds to its first character '.'
        remote_root = os.path.join(remote_dir, root[1::]) 
        #First directories
        files_written = 0
        directories_created = 0
        for name in dirs:
            #Here we will issue mkdir commands
            #Check if directory exists using quick script which takes as arguments the dir path
            res = connection.run('{} {}'.format(os.path.join(remote_dir,'check_dir.sh'),os.path.join(remote_dir,name)))
            if str(res.stdout).strip('\n') == '0': #returns 0 if doesnt exist
                connection.run('mkdir {}'.format(os.path.join(remote_dir,name)))
                files_written+=1
            else:
                #If the folder exists, pass on
                pass
        
        for name in files:
            #Here we will issue send commands
            #Below checks if the file already exists
            res = connection.run('{} {}'.format(os.path.join(remote_dir,'check_file.sh'),os.path.join(remote_dir,name)))
            if str(res.stdout).strip('\n') == '0': #returns 0 if doesnt exist
                connection.put(local=os.path.join(root, name),remote=os.path.join(remote_dir,name))
                directories_created+=1
            else:
                #If the file already exists pass over
                pass
    logger.info('Moved {} files, in the process {} directories were created'.format(files_written, directories_created))

def send_config(local_dir,remote_dir, connection):
    """Sends content of config directory, the difference here to the script above is that this overwrites the config and database"""
    config_dir = os.path.join(local_dir, 'config')
    for root, dirs, files in os.walk(config_dir, topdown = False):
        for name in files:
            connection.put(local=os.path.join(root, name),remote=os.path.join(remote_dir,'config', name))
    logger.info('Moved configs and Database to kapteyn')


def get_config(local_dir,remote_dir):
    """Retrieve config from kapteyn, run prior to scheduling"""
    if os.path.isfile(os.path.join(local_dir,'config.conf')): #Move last days config to backup file
        if os.path.isdir(os.path.join(local_dir, 'backup')): #Check that backup directory exists
            #Move config file with YYYYMMDD naimg format to backup folder
            os.rename(os.path.join(local_dir,'config.conf'), os.path.join(local_dir,'backup','config_{}.conf'.format((dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))))
        else:
            os.mkdir(os.path.join(local_dir, 'backup'))
            os.rename(os.path.join(local_dir,'config.conf'), os.path.join(local_dir,'backup','config_{}.conf'.format((dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))))
    gate = Connection(host='kapteyn.astro.rug.nl', user='telescoop', forward_agent = True, connect_kwargs = {'allow_agent':True})
    c = Connection(host='virgo11', user='telescoop',gateway=gate, forward_agent = True, connect_kwargs = {'allow_agent':True})
    c.open()
    c.get(os.path.join(remote_dir, 'config.conf'), os.path.join(local_dir,'config.conf'))
    c.close()


    #FIXME: The name of the below function was missing, was something else?
def update_config_after_run(local_dir):
    """Updates config with results of past night, 
    Updates Database 
    run prior to sending data to kapteyn (this will be part of data)"""
    
    config_path = os.path.join(local_dir, 'config','config')
    f= open(config_path,'r')
    config= json.load(f)
    f.close()
    #Create list of PIDs and obsIDs directories created with the number of files inside
    obs_IDs = {}
    #List of tupples to remove empty directories at the end
    not_completed = []
    connect = sqlite3.connect('Database.db')
    table_names = sqlite_get_tables(connect)
    tables = {}
    for i in table_names:
        tables[i]=sqlite_retrieve_table(connect, i)
    im_path = os.path.join(local_dir, (dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))
    PIDs = os.listdir(im_path) #Returns list of files/folders in dir
    for i in PIDs:
        #Get PID row in database
        for k in range(len(tables['Observations'])):
            if tables['Observations'][k]['PID'] == i: #All PIDs loaded as strings
                break #Row index k
        obsID_path = os.path.join(im_path, i)
        ObsIDs = os.listdir(obsID_path) #List of obsID's that got scheduled
        for j in ObsIDs:
            obsID_path = os.path.join(obsID_path, j) #Get list of individual images in directory
            nr_of_images = os.listdir(obsID_path)
            nr_expected = check_obs(j,tables) 
            if len(nr_of_images)==nr_expected:#obsID completed
                #Modify config
                config['Completed_obsID'].append(j)
                config['To_be_completed_obsID'].remove(j)
                #Modify Databse 
                tables['Observations'][k]['missing_obsIDs'].remove(str(j)) #Append log sheet and so on
                tables['Observations'][k]['Obs_days'].append((dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))
                log_file = (dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d')
                log_file = log_file[0:2]+log_file[4:]+'_LOGS.pdf'
                tables['Observations'][k]['logsheet'].append(log_file)
                change_sqlite_row(connect, 'Observations', 'PID', i, 'missing_obsIDs', '['+','.join(tables['Observations'][k]['missing_obsIDs'])+']')
                change_sqlite_row(connect, 'Observations', 'PID', i, 'Obs_days', '['+','.join(tables['Observations'][k]['Obs_days'])+']')
                change_sqlite_row(connect, 'Observations', 'PID', i, 'logsheet', '['+','.join(tables['Observations'][k]['logsheet'])+']')
                if len(tables['Observations'][k]['missing_obsIDs'])==0: #Check if no more missing obsIDs
                    move_from_Obs_to_completed(connect,tables, k) #Remove PID entry
                #Remove obsID from schedule
                connect.execute("DELETE from {} where {}={}".format('Schedule', 'obsID', j))
            if len(nr_of_images) == 0: #obsID didnt start
                not_completed.append((i, j)) #(PID, obsID)
            else: #obsID partially completed
                #Add log file and obsday to sqlite
                tables['Observations'][k]['Obs_days'].append((dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))
                log_file = (dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d')
                log_file = log_file[0:2]+log_file[4:]+'_LOGS.pdf'
                tables['Observations'][k]['logsheet'].append(log_file)
                change_sqlite_row(connect, 'Observations', 'PID', i, 'Obs_days', '['+','.join(tables['Observations'][k]['Obs_days'])+']')
                change_sqlite_row(connect, 'Observations', 'PID', i, 'logsheet', '['+','.join(tables['Observations'][k]['logsheet'])+']')
                #Subtract completed exposures from obsID
                for x in range(len(tables['Schedule'])):
                    if tables['Schedule'][x]['obsID'] == j:
                        #Remove images already taken from obsID
                        if len(nr_of_images) > 0:
                            tables['Schedule'][x]['exposure'] -= len(nr_of_images)
                            change_sqlite_row(connect, 'Schedule', 'obsID', j,'exposure', tables['Schedule'][x]['exposure'])
                            break
    for i in not_completed: #Removes all contentless folders
        os.rmdir(os.path.join(im_path, i[0], i[1]))

    update_config(local_dir,config)



def move_from_Obs_to_completed(connect,tables, index):
    """Database - dict of database content
    k - row index of Observations with PID to be moved from table Observations to Completed"""
    connect.execute("DELETE from {} where {}={}".format('Observations', 'PID', tables['Observations'][index]['PID']))
    #Create ordered list for the Completed table
    to_add = [tables['Observations'][index][key] for key in ['PID', 'Name', 'E-Mail', 'Phone', 'Completed_by', 'Submission_Date', 'Observer_type', 'time_sensitive', 'obsIDs', 'total_length', 'logsheet', 'Obs_days']]
    connect.execute("INSERT INTO {}  VALUES ({})".format('Completed', ','.join(to_add)))

def change_sqlite_row(connect, table,row_identifier,row_identifier_value,value_identifiers, values):
    """connect --> connection object
    table --> table name
    value_identifiers --> comma seperated heads
    values ---> values to be placed"""
    connect.execute("UPDATE {} SET {} = {} WHERE {} = {};".format(table, value_identifiers, values,row_identifier,row_identifier_value))




def check_obs(obsID,tables):
    """Function to check the number of images that are suppose to be in obsID"""
    for x in range(len(tables['Schedule'])):
        if tables['Schedule'][x]['obsID'] == obsID:
            nr_of_light = tables['Schedule'][x]['exposures']
    return nr_of_light


if __name__=='__main__':
    print('This is intended to be run only to set up the directory Structure!')
    file_path = os.path.abspath('C:\LDST')
    remote_path = '/net/vega/data/users/observatory/LDST/'
    send_results(file_path,remote_path)