
"""





The below can most likely be removed

Wait for now




"""


#FUNction definitionass
def night_schedule(obj):
    """
    Function determining which observations will occure to maximize observing time per night
    -------------
    obj ---> Priority Sorted list of dict returned from func: assign_priority or otherwise sorted

    https://clearoutside.com/forecast/53.38/6.23
    """

    weather_data = get_predicted_conditions()

    #Create Coordinate System
    location = EarthLocation(53.3845258962902, 6.23475766593151) #Lon Lat of observatory (currently guessed)
    t = Time([(weather_data['Sunset']+i*dt.timedelta(seconds=600)).strftime('%Y-%m-%dT%H:%M:%S') for i in range(24) if ((weather_data['Sunset']+i*dt.timedelta(seconds=600))<weather_data['Sunrise'])])
    altaz = coord.AltAz(location=location, obstime=t)
    #Below filtering is done for wheter or not observation is actually possible and within which timeframe
    for i in range(len(obj)):
        obj[i] = check_min_conditions(obj[i],weather_data) #TODO: Since now all obsID's are split save data and reassign to all
        if obj[i]['Possible']:
            obj[i] = check_visible(obj[i],altaz)
        else:
            pass
    #Assigning an observational schedule
    schedule = {(weather_data['Sunset']+dt.timedelta(seconds=600*i)):0 for i in range(84) if (weather_data['Sunset']+dt.timedelta(seconds=600*i)<weather_data['Sunrise'])}
    for i in obj: #i is dict object for each observation
        if i['Possible']: #Previous functions will have established this
            count = 0 
            obs_length = i['total_length'] 
            if int(obs_length) != float(obs_length): obs_length = int(obs_length)+1 #TODO: For now 10 minute indeces, see if and how to split it
            for key in schedule: #Keys are datetime objects 10 minutes seperated from each other
                if i['Obs_time'][0].to_datetime()<=key and schedule[key]==0 and key < i['Obs_time'][1].to_datetime() and count != obs_length: #Check start time onward, that nothing is assigned yet, and that entry is less than end time, and that the needed timeslots haven't all been assigned yet
                    schedule[key] = i['obsID'] #Assign obs_id
                    count += 1
                elif key == i['Obs_time'][1].to_datetime() and schedule[key]==0: #Check end time, and that nothing is assigned yet
                    schedule[key] = i['obsID']
                    count+=1
                    break
                elif count == obs_length:
                    break
    return obj, schedule





def check_visible(obj,altaz):
    """
    Checks if object is visible during the night
    ---------
    obj --> dict: object containing scheduling information
    altaz --> Coordinate Frame of observatory
    location --> EarthLocation: Location of Observatory
    """
    #base coordinate system
    res = SkyCoord.from_name(obj['object'])
    res = res.transform_to(altaz)
    observing_points = [[res[i], i] for i in range(len(res)) if (res[i].alt>0)] #Check min angle
    if len(observing_points)==0:
        obj['Possible'] = False
        return obj
    else:
        if observing_points[0][0].obstime.to_datetime()+dt.timedelta(seconds=obj['total_length']*60)<observing_points[-1][0].obstime.to_datetime():
            obj['Possible'] = True
            obj['Obs_time'] = [observing_points[0][0], observing_points[-1][0]]
        else:
            obj['Possible'] = False
            return obj
    if 'airmass' in obj['min_cond']:
        res = res[observing_points[0][1]:observing_points[-1][1]] #Getting visible time range
        airmass = res.secz
        observing_times = [t[i] for i in range(len(airmass)) if airmass[i]<objects[0]['min_cond']['airmass']]
        if len(observing_times)==0:
            obj['Possible'] = False
            return obj
        else:
            objects[0]['Obs_time'] = [observing_times[0].obstime,observing_times[-1].obstime]
            obj['Possible'] = True
    else: 
        obj['Obs_time'] = [obj['Obs_time'][0].obstime, obj['Obs_time'][-1].obstime]

    return obj

    







def make_plot(objects, schedule,weather,print_out=True, save_dir = ''):
    """Makes standardized graphs of objects planned for observation and the weather conditions"""
    keys = {'Temperature', 'Pressure', 'Humidity', 'Dew_Point', 'Cloud_cover', 'Visibility', 'Wind_Speed', 'Wind_direction', 'Rain_Prob', 'Time', 'Moon', 'Sunset', 'Sunrise'}
    fig = plt.figure(figsize=(12,12))
    fig,ax = plt.subplots(nrows=2,ncols=2,figsize=(24,12))
    ax[0,0].plot(weather['Time'],np.array(weather['Temperature'])-273.15,label='Temperature C')
    ax[0,0].plot(weather['Time'],np.array(weather['Dew_Point'])-273.15,label='Dew Point C')
    ax[0,1].plot(weather['Time'],np.array(weather['Pressure']),label='Pressure kPa')
    ax[0,1].plot(weather['Time'],np.array(weather['Visibility'])/10,label='Visibility 10*m')
    ax[1,0].plot(weather['Time'],np.array(weather['Humidity']),label='Humidity %')
    ax[1,0].plot(weather['Time'],np.array(weather['Cloud_cover']),label='Cloud Cover %')
    ax[1,0].plot(weather['Time'],np.array(weather['Rain_Prob']),label='Rain Probability %')
    ax[1,1].plot(weather['Time'],np.array(weather['Wind_Speed']),label='Wind Speed m/s')
    observing = False
    for key in schedule:
        if schedule[key]!=0 and not observing:
            name = [i['object'] for i in objects if i['obs_id']==schedule[key]]
            ax[0,0].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            ax[1,0].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            ax[0,1].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            ax[1,1].axvline(key, c='g',label=name[0]+', obs_id='+str(schedule[key]))
            observing = True
            obs_id = str(schedule[key])
        elif int(schedule[key])!=int(obs_id) and observing:
            observing = False
            ax[0,0].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            ax[1,0].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            ax[0,1].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            ax[1,1].axvline(key, c='r',label='end '+name[0]+', obs_id='+obs_id)
            if schedule[key]!=0: #In case new observation is started here
                name = [i['object'] for i in objects if i['obs_id']==schedule[key]]
                ax[0,0].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                ax[1,0].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                ax[0,1].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                ax[1,1].axvline(key+dt.timedelta(seconds=60), c='g',label=name[0]+', obs_id='+str(schedule[key]))
                observing = True
                obs_id = str(schedule[key])


    for j in range(len(ax)):
        for i in range(len(ax[j])):
            ax[j][i].set_xlim(weather['Sunset']-dt.timedelta(seconds=5*60),weather['Sunrise']-dt.timedelta(seconds=5*60))
            ax[j][i].legend()
    if print_out:
        plt.show()
    else:
        plt.savefig(os.path.join(save_dir,'{}_pred_plot.png'.format(dt.date.today().strftime('%d_%m_%Y'))))


