


"""
Using SFTP protocoll to transfer files using ssh, with the python client fabric
"""
import os
import logger
from fabric import Connection
import datetime as dt


#The below contain several folders, one for each observation, and maybe some more subfolders for each filter or config file
login_params = {'user':'observer','password':''} #TODO: User must have default access to directory!

logger = logging.getLogger('main.data')
logger.debug("starting data logger")

def send_results(local_dir,remote_dir):#TODO: Enable ssh keys
    """Creates ssh connection to kapteyn and sends files from and to above specified filepaths"""
    c = Connection(host='kapteyn.astro.rug.nl', user=login_params['user'],password=login_params['password'])
    send_dir(local_dir,remote_dir,c)


def send_dir(local_dir,remote_dir, connection):
    """ In its essence this simply copies a directory over sftp
    Sends contents of directory local_dir to remote_dir on station,
    First creates directories
    then sends files
    """
    #TODO: Overwrite existing files? Remove from local device after sending? Skip if top directory exists or iterate through all?
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
            #Check if directory exists
            res = connection.run('if [[ -d "{}" ]]; then echo "1"; else echo "0"; fi'.format(os.path.join(remote_dir,name)))
            #TODO: CHeck the below works reliably
            if str(res.stdout).strip('\n') == '0': #returns 0 if doesnt exist
                connection.run('mkdir {}'.format(os.path.join(remote_dir,name)))
                files_written+=1
            else:
                #If the folder exists, pass on
                pass
        
        for name in files:
            #Here we will issue send commands
            #Below checks if the file already exists
            res = connection.run('if [[ -f "{}" ]]; then echo "1"; else echo "0"; fi'.format(os.path.join(remote_dir,name)))
            #TODO: CHeck the below works reliably
            if str(res.stdout).strip('\n') == '0': #returns 0 if doesnt exist
                connection.put(local=os.path.join(root, name),remote=os.path.join(remote_dir,name))
                directories_created+=1
            else:
                #If the file already exists pass over
                pass
    logger.info('Moved {} files, in the process {} directories were created'.format(files_written, directories_created))


def get_config(local_dir,remote_dir):
    """Retrieve config from kapteyn, run prior to scheduling"""
    if os.path.isfile(os.path.join(local_dir,'config.conf')): #Move last days config to backup file
        if os.path.isdir(os.path.join(local_dir, 'backup')): #Check that backup directory exists
            #Move config file with YYYYMMDD naimg format to backup folder
            os.rename(os.path.join(local_dir,'config.conf'), os.path.join(local_dir,'backup','config_{}.conf'.format((dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))))
        else:
            os.mkdir(os.path.join(local_dir, 'backup'))
            os.rename(os.path.join(local_dir,'config.conf'), os.path.join(local_dir,'backup','config_{}.conf'.format((dt.date.today()-dt.timedelta(days=1)).strftime('%Y%m%d'))))
    c = Connection(host='kapteyn.astro.rug.nl', user=login_params['user'],password=login_params['password'])
    c.get(os.path.join(remote_dir, 'config.conf'), os.path.join(local_dir,'config.conf'))
    c.close()



def update_config(local_dir):
    """Updates config with results of past night, run prior to sending data to kapteyn (this will be part of data)"""
    #TODO: Make sure that the config file in kapteyn gets overriden
    for root, dirs, files in os.walk("{}", topdown = False): #TODO: Find dir name