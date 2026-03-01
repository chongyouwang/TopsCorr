import coinsar.cores.utils as ut
import datetime as dt
import os
from urllib.request import urlretrieve
import numpy as np
import json
# Author:   Chong-You (Kevin) Wang, 2024-05, OSU
"""
    Functions for downloading GPS data and basic data processing. Copy from CoInSAR
"""

### Change log
""" 
2025-02, Chong-You (Kevin) Wang, OSU
    - bugfix for searching available stations in time.
"""

def download_site_list(output_path=os.path.abspath('./gnss_ngl'), url='https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt'):
    """download DataHoldings.txt.
    Parameters: output_path : string, path to the output file

    Returns:    output_file : string, Path of the output file. Default is ./gsp_data/   DataHoldings.txt
    """
    # revised from mintpy
    os.makedirs(output_path,exist_ok=True)
    output_file = os.path.join(output_path, os.path.basename(url))
    print(f'Downloading site list from Nevada Geodetic Lab: {url} to {output_path}')
    urlretrieve(url, output_file)
    return output_file


def search_gnss(SNWE, start_date=None, end_date=None, site_list_file=None, min_num_solution=100,output_path=None):
    """Search available GPS sites within the geo bounding box from UNR website.
    Parameters: SNWE             : tuple of 4 float, indicating (South, North, West, East) in degrees
                start_date       : str in YYYYMMDD format
                end_date         : str in YYYYMMDD format
                site_list_file   : str.
                min_num_solution : int
    Returns:    site_names       : 1D np.array of string for GPS station names
                site_lats        : 1D np.array for lat
                site_lons        : 1D np.array for lon
    """
    # revised from mintpy
    if site_list_file is None:
        site_list_file = download_site_list(output_path=output_path)

    site_info = np.loadtxt(site_list_file,
                          dtype=bytes,
                          skiprows=1,
                          usecols=(0,1,2,3,4,5,6,7,8,9,10)).astype(str)
    
    site_names = site_info[:, 0]
    site_lats, site_lons = site_info[:, 1:3].astype(np.float32).T
    site_lons -= np.round(site_lons / (360.)) * 360.
    
    time_st = np.array([dt.datetime.strptime(i, "%Y-%m-%d") for i in site_info[:, 7].astype(str)])

    time_ed = np.array([dt.datetime.strptime(i, "%Y-%m-%d") for i in site_info[:, 8].astype(str)])
    num_solution = site_info[:,10].astype(np.int16)
    
    # limit in space
    idx = ((site_lats >= SNWE[0]) * (site_lats <= SNWE[1]) *
           (site_lons >= SNWE[2]) * (site_lons <= SNWE[3]))

    # limit in time find stations that have data during given period
    if start_date:
        if not ut.check_datetime(start_date):
            start_date = ut.yyyymmdd2datetime(start_date)
        idx *= time_ed >= start_date
    if end_date:
        if not ut.check_datetime(end_date): 
            end_date = ut.yyyymmdd2datetime(end_date)
        idx *= time_st <= end_date
    if min_num_solution is not None:
        idx *= num_solution >= min_num_solution
        
    return site_names[idx], site_lons[idx], site_lats[idx]

def find_close_sta(gnss_list,insar_lon,insar_lat,start_date,end_date,radius=1000,time_st_match=True,completion_thres=0.3):
    gnss_lon = []
    gnss_lat = []
    gnss_sta = []
    gnss_want = []
    ind_space_list = []
    if not ut.check_datetime(start_date):
        start_date = ut.yyyymmdd2datetime(start_date)[0]
    if not ut.check_datetime(end_date):
        end_date = ut.yyyymmdd2datetime(end_date)[0]
# Get gnss stations that have InSAR measurements nearby
    #pdb.set_trace()
    for i in range(len(gnss_list)):
    #for i in [5]:
        sta_tmp, lon_tmp, lat_tmp,time_tmp, h_tmp, data_completion = read_data_info(gnss_list[i],start_date=start_date,end_date=end_date)
        if sta_tmp is None:
            continue
        else:
    # Search insar pixels near gnss stations. unit is meter
            ind_space = ut.gc_distance_lonlat(np.deg2rad(np.vstack((insar_lon,insar_lat)).T),np.deg2rad(np.vstack((lon_tmp,lat_tmp)).T)) < radius 
     # filter gnss stations with starting time
            if time_st_match:
                ind_time = time_tmp == start_date
            else:
                ind_time = True
            if (~ind_space).all() or (not ind_time) or (data_completion < completion_thres):
                continue
            else:
                gnss_want.append(gnss_list[i])
                ind_space_list.append(ind_space)
                gnss_lon.append(lon_tmp)
                gnss_lat.append(lat_tmp)
                gnss_sta.append(sta_tmp)
    return gnss_want, gnss_lon, gnss_lat, gnss_sta, ind_space_list


def download_site(site,output_path=os.path.abspath('./gnss_ngl'),version='IGS14'):
    """ Download GPS daily solution from NGL
    """
    os.makedirs(output_path,exist_ok=True)
    file = os.path.join(output_path, f'{site}.tenv3')
    file_url = f"https://geodesy.unr.edu/gps_timeseries/{version}/tenv3/{version}/{os.path.basename(file)}"
    print(f'Downloading {site} from {file_url}')
    
    plot_file = os.path.join(output_path, f'pic/{site}.png')
    os.makedirs(os.path.dirname(plot_file),exist_ok=True)
    #https://geodesy.unr.edu/tsplots/IGS14/IGS14/TimeSeries/
    url_prefix = f'https://geodesy.unr.edu/tsplots/{version}/{version}'
    plot_file_url = os.path.join(url_prefix, f'TimeSeries/{site}.png')
    try:
        urlretrieve(file_url, file)
    except:
        print(f"Don't find {site} data")
    try:
        urlretrieve(plot_file_url, plot_file)
    except:
        print(f"Don't find {site}.png")
    return file

def read_data_info(filepath,start_date=None,end_date=None):
    """ Read GNSS coordinates
    """
    with open(filepath,'r') as file:
        data = file.readlines()
    station = os.path.basename(filepath).split('.')[0]
    time = []
    lon = []
    lat = []
    h = []
        
    for i in range(1,len(data)):
        tmp = data[i].split()
        time.append(dt.datetime.strptime(tmp[1],"%y%b%d"))
        lat.append(float(tmp[-3]))
        lon.append(float(tmp[-2]))
        h.append(float(tmp[-1]))
    
    time = np.array(time)
    lat = np.array(lat)
    lon = np.array(lon)
    h = np.array(h)
    # did not consider there is no data in the file
    if (start_date is None) and (end_date is None):
        ind_first = 0
        delta_t = (time[-1] - time[ind_first]).days
        data_completion = time.shape[0] / delta_t
        return station, lon[ind_first],lat[ind_first],time[ind_first], h[ind_first], data_completion
    elif (start_date is None) and (end_date is not None):
        ind_list = np.where(time <= end_date)[0]
        ind_first = ind_list[0]
        delta_t = (end_date - time[0]).days
        data_completion = ind_list.shape[0] / delta_t
        return station, lon[ind_first],lat[ind_first],time[ind_first], h[ind_first], data_completion 
    elif (start_date is not None) and (end_date is None):
        ind_list = np.where(time >= start_date)[0]
        ind_first = ind_list[0]
        delta_t = (time[-1] - start_date).days
        data_completion = ind_list.shape[0] / delta_t
        return station, lon[ind_first],lat[ind_first],time[ind_first], h[ind_first], data_completion
    else:
        ind_list = np.where((time >= start_date) & (time <= end_date))[0]
        if ind_list.sum() == 0:
            return None, None, None, None, None, None
        else:
            ind_first = ind_list[0]
            delta_t = (end_date - start_date).days
            data_completion = ind_list.shape[0] / delta_t
            return station, lon[ind_first],lat[ind_first],time[ind_first], h[ind_first], data_completion
    
    
def read_tenv3(filepath,start_date=None,end_date=None):
    """ Read tenv3 file
    """
    with open(filepath,'r') as file:
        data = file.readlines()
    time = []
    e = []
    n = []
    u = []
    e_std = []
    n_std = []
    u_std = []
        
    for i in range(1,len(data)):
        tmp = data[i].split()
        time.append(dt.datetime.strptime(tmp[1],"%y%b%d"))
        e.append(float(tmp[7]) + float(tmp[8]))
        n.append(float(tmp[9]) + float(tmp[10]))
        u.append(float(tmp[11]) + float(tmp[12]))
        e_std.append(float(tmp[14]))
        n_std.append(float(tmp[15]))
        u_std.append(float(tmp[16]))
    
    time = np.array(time)
    e = np.array(e)
    n = np.array(n)
    u = np.array(u)
    e_std = np.array(e_std)
    n_std = np.array(n_std)
    u_std = np.array(u_std)
    
    if (start_date is None) and (end_date is None):
        return time, e, n , u, e_std, n_std, u_std
    else:
        if start_date is None:
            start_date = time[0]
        else:
            if not ut.check_datetime(start_date):
                start_date = ut.yyyymmdd2datetime(start_date)
        if end_date is None:
             end_date = time[-1]
        else:
            if  not ut.check_datetime(end_date):  
                end_date = ut.yyyymmdd2datetime(end_date)
            
        ind = np.where((time >= start_date) & (time <= end_date))
        return time[ind], e[ind], n[ind], u[ind], e_std[ind], n_std[ind], u_std[ind]

def get_metadata(station_name,output_path=os.path.abspath('./gnss_ngl')):
    
    os.makedirs(output_path,exist_ok=True)
    metadata_path = os.path.join(output_path,'metadata.txt')
    if isinstance(station_name, str):
        station_name = [station_name]
        
    if not os.path.exists(metadata_path):
        print("Downloading metadata...")
        try:
            urlretrieve('https://geodesy.unr.edu/NGLStationPages/steps.txt',metadata_path)
        except:
            raise Exception("Download failed")
             
    with open(metadata_path,'r') as f:
        data = f.readlines()

    station_container = {name:{'station':name,'equipment':[],'earthquake':[]} for name in station_name}

    for i in data:
        tmp = i.split()
        if not tmp:
            continue
        
        if tmp[0] in station_name:
            date = dt.datetime.strftime(dt.datetime.strptime(tmp[1],"%y%b%d"),'%Y%m%d')
            code = tmp[2]
            if code == '1':
                station_container[tmp[0]]['equipment'].append({
                    'time':date,
                    'description':tmp[3]})
                
            elif code == '2':
                station_container[tmp[0]]['earthquake'].append({
                    'time':date,
                    'distance':float(tmp[4]),
                    'mag':float(tmp[5]),
                    'USGS_id':tmp[6]})
            elif code == '3':
                station_container[tmp[0]]['system'].append({
                    'time':date,
                    'description':tmp[3]})
                
    for sta in station_container.keys():
        json_output = f"{sta}.json"
        print(f'Saving {sta} metadata to {output_path} as {json_output}')
        with open(os.path.join(output_path,json_output),'w') as file:
            json.dump(station_container[sta],file,indent=4)
    
    
def read_equipment_jump(json_path,time_obs_st,time_obs_ed):
    # only get the equipment change
    with open(json_path,'r') as f:
        data = json.load(f)
        
    if not data['equipment']:
        print('No equipment change')
        return None
    else:
        jump_time = []
        for event in data['equipment']:
            time = ut.yyyymmdd2datetime(event['time'])[0]
            if (time > time_obs_st and time < time_obs_ed) and (time not in jump_time):
                jump_time.append(time)
                
        if not jump_time:
            print('No equipment change')
            return None
        else:
            print(f"{len(jump_time)} equipment changes during {time_obs_st} and {time_obs_ed}")
            print(f"time: {jump_time}")
            return jump_time
    
    


    
