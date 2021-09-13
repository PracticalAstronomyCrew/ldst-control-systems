
# Scripts dedicated to retrieve extra observations
import requests
from requests_html import HTMLSession
import urllib
import pandas as pd
from astropy.time import Time, TimeDelta
import astropy.units as u
import json
'''
#Getting the list of Near Earth Objects
url = 'https://asteroid.lowell.edu/upobjs/'
url = 'https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TransitView/nph-visibletbls?dataset=transits'
html = requests.get(url).content
print(html)
df_list = pd.read_html(html)
print(df_list)''' #Maybe can make progress using selenium but seems unlikely given that most other tools failed




def get_observations():
    #TODO: Implement code here so that a list with possible observations gets created (its order will be interpreted as priority)
    # These observations will be assigned a daily tempID, these will be written to a extraObs file containing the images and a json file of the list containing tempID:{dict of params}
    # The list should contain dictionary items with the following keys:
    # {'tempID':x,'Filter':x, 'object':x,'exposure':x,'number_of_exposures':x}


    return [] #FOr now dummy return