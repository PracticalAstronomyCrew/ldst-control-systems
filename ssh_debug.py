
from fabric import Connection
import os

gate = Connection(host='kapteyn.astro.rug.nl', user='telescoop', forward_agent = True, connect_kwargs = {'allow_agent':True})
c = Connection(host='virgo11', user='telescoop',gateway=gate, forward_agent = True, connect_kwargs = {'allow_agent':True})
c.open()
c.get(os.path.join(remote_path, 'config','config'), os.path.join(file_path, 'config','config'))
c.get(os.path.join(remote_path, 'config','Databse.db'), os.path.join(file_path, 'config','Database.db'))
c.close()