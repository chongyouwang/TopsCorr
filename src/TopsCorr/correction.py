import pysolid
import pyaps3 as pa
import datetime as dt
import os
import numpy as np
def set_corr(time,x_size,y_size,x0,y0,dx,dy):
    meta = {
        'LENGTH' : y_size,                # number of data along latitude
        'WIDTH'  : x_size,                # number of data along lon
        'X_FIRST': x0,               # min longitude in degree (upper left corner of the upper left pixel)
        'Y_FIRST': y0,                 # max laitude   in degree (upper left corner of the upper left pixel)
        'X_STEP' :  dx,  # output resolution in degree
        'Y_STEP' :  dy,  # output resolution in degree
        }

    # compute SET via pysolid, unit is meter
    set_e, set_n, set_u = pysolid.calc_solid_earth_tides_grid(
            time, meta,
            display=False,
            verbose=False,
        )
    return set_e,set_n,set_u


def tropo_corr(time,dem,inc,lon,lat,mask=None,era5_path=os.path.join(os.getcwd(),'ERA5'),output_path=os.getcwd()):
    # the output delay is in meter
    os.makedirs(era5_path,exist_ok=True)
    t2 = (time + dt.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    hr1 = str(time.hour)
    hr2 = str(t2.hour)
    date1 = dt.datetime.strftime(time,"%Y%m%d")
    date2 = dt.datetime.strftime(t2,"%Y%m%d")
    ratio = (t2 - time).total_seconds() / 3600
    
    S = int(np.floor(lat.min()))
    N = int(np.ceil(lat.max()))
    W = int(np.floor(lon.min()))
    E = int(np.ceil(lon.max()))
    grb_file1 = os.path.join(era5_path,f"ERA5_N{S}_N{N}_E{W}_E{E}_{date1}_{hr1}.grb")
    grb_file2 = os.path.join(era5_path,f"ERA5_N{S}_N{N}_E{W}_E{E}_{date2}_{hr2}.grb")
    if not os.path.exists(grb_file1):
        pa.ECMWFdload([date1],hr1,era5_path,model='ERA5',snwe=(S,N,W,E))
    if not os.path.exists(grb_file2):
        pa.ECMWFdload([date2],hr2,era5_path,model='ERA5',snwe=(S,N,W,E))
        #pa.ECMWFdload(['20200601','20200901'], hr='14', filedir=filedir, model='ERA5', snwe=(30,40,120,140))
    obj = pa.PyAPS(grb_file1, dem=dem, inc=inc, lat=lat, lon=lon, grib='ERA5',mask=mask, verb=True)
    delay1 = obj.getdelay()
    obj = pa.PyAPS(grb_file2, dem=dem, inc=inc, lat=lat, lon=lon, grib='ERA5',mask=mask, verb=True)
    delay2 = obj.getdelay()
    delay = (1 - ratio) * delay1 + ratio * delay2
    return delay