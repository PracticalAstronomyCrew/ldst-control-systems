#!python
#!C:\Users\blaau\AppData\Local\Programs\Python\Python39
from fabric import Connection

gate = Connection(host='kapteyn.astro.rug.nl', user='telescoop', forward_agent = True, connect_kwargs = {'allow_agent':True})
c = Connection(host='virgo11', user='telescoop',gateway=gate, forward_agent = True, connect_kwargs = {'allow_agent':True})
c.open()
c.run('ls')