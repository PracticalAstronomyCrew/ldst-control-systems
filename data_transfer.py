


"""
Using SFTP protocoll to transfer files using ssh, with the python client fabric
"""


from fabric import Connection
import os

#The below contain several folders, one for each observation, and maybe some more subfolders for each filter or config file
local_dir = r'/path/to/image_dir'
remote_dir = r'/path/to/rep'

login_params = {'user':'observer','password':''} #TODO: User must have default access to directory!

def send_results():#TODO: Enable ssh keys
    """Creates ssh connection to kapteyn and sends files from and to above specified filepaths"""
    c = Connection(host='kapteyn.astro.rug.nl', user=login_params['user'],password=login_params['password'])
    send_dir(local_dir,remote_dir,c)


def send_dir(dir,fin_dir, connection):
    """ In its essence this simply copies a directory over sftp
    Sends contents of directory dir to fin_dir on station,
    First creates directories
    then sends files
    """
    #TODO: Overwrite existing files? Remove from local device after sending? Skip if top directory exists or iterate through all?
    os.chdir(local_dir) #Moves current operating directory
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

if __name__ == "__main__":
    send_results()

