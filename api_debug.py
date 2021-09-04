import requests
import datetime as dt
location = (53.3845258962902, 6.23475766593151)
api_key='52695aff81b7b6e5708ab0e924b859f2'
url= "http://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=[current,minutely,alerts]&appid={}".format(*location, api_key)
weather = requests.get(url).json()
keys = ['Temperature', 'Pressure', 'Humidity', 'Dew_Point', 'Cloud_cover', 'Visibility', 'Wind_Speed','Wind_direction','Rain_Prob']
key_return = ['temp','pressure','humidity','dew_point','clouds','visibility','wind_speed','wind_deg','pop']
weather_cond = {keys[i]:[weather['hourly'][j][key_return[i]] for j in range(len(weather['hourly']))] for i in range(len(keys))}
weather_cond['Time']=[dt.datetime.utcfromtimestamp(i['dt']) for i in weather['hourly']]
weather_cond['Moon']=weather['daily'][0]['moon_phase']
weather_cond['Sunset']=dt.datetime.utcfromtimestamp(weather['daily'][0]['sunset'])
weather_cond['Sunrise']=dt.datetime.utcfromtimestamp(weather['daily'][1]['sunrise'])
print(weather_cond)