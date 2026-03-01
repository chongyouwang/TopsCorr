import numpy as np


def ismember(A, B):
    """ Find the index of the same elements between two data
        This function emulate the ismember function in MATLAB
        
    Parameters: A   :   1D list or np.ndarray, data 1
                B   :   1D list or np.ndarray, data 2
                
    Returns:    lia :   1D list, index of the same elements for data 1
                locb:   1D list, index of the same elements for data 2
    """
    
    #lia = list(filter(lambda i: A[i] in B ,range(len(A))))  # speed rank :2
    #lia = [i for i,a in enumerate(A) if a in B]   # speed rank:3 >>> extreme slow
    loc_a_dict =  {elt:i for (i,elt) in enumerate(A)}   # speed rank:1 >> the fastest version using dict
    lia = [loc_a_dict.get(itm) for itm in B]
    #lia_1 = [a for a in lia if a is not None] # slower than the version below
    lia = list(filter(lambda x: x is not None,lia))
    loc_b_dict = {elt:i for (i,elt) in enumerate(B)}
    locb = [loc_b_dict.get(itm) for itm in A]
    locb = list(filter(lambda x: x is not None,locb))
    return lia,locb




def enu2los(e,n,u,inc,azi):
    """ Transform east, north and up components to LOS direction by given incidence and azimuth angles
    Note that azimuth angle from ISCE is counter-clockwise and is for los measurement from target to satellite (Not the heading angle of the satellite). So, the formula is different from one which azimuth angle is clockwise and for satellite (-e * np.sin(inc) * np.cos(azi) + n * np.sin(inc) * np.sin(azi) + u * np.cos(inc)) .
    Note: since normal sin and cos given counter-clockwise angles results in postive in west direction. Adding negative sign to make it towards east.
    """
    return -e * np.sin(inc) * np.sin(azi) + n * np.sin(inc) * np.cos(azi) + u * np.cos(inc)

def enu2los_std(e_std,n_std,u_std,inc,azi):
    """ Transform the standard deviations of east, north and up components to that of LOS direction by given incidence and azimuth angles
        Note that azimuth angle from ISCE is counter-clockwise and is for los measurement (Not the heading angle of the satellite). So, the formula is different from one which azimuth angle is clockwise and for satellite (-e * np.sin(inc) * np.cos(azi) + n * np.sin(inc) * np.sin(azi) + u * np.cos(inc)) .
    """
    return np.sqrt((e_std * np.sin(inc) * np.sin(azi))**2 + (n_std * np.sin(inc) * np.cos(azi))**2 + (u_std * np.cos(inc))**2)

def get_unit(inc,azi):
    # the unit vector in east north up direction. from target to satellite. Note the azimuth angle is counter clockwise provided by ISCE
    e_unit = -np.sin(inc) * np.sin(azi)
    n_unit = np.sin(inc) * np.cos(azi)
    u_unit = np.cos(inc)
    return e_unit,n_unit,u_unit

def rad2disp(data,wavelength):
    return -data * wavelength / 4 / np.pi

def disp2rad(data,wavelength):
    return -data / wavelength * 4 * np.pi

def gc_distance_lonlat(A,B):
    """ Calcalate the great circle distance between two geodetic coordinates
    
    Parameters: A       : 2D np.ndarray, group 1 of points [lon,lat] in the size of (num_points, 2), radian
                B       : 2D np.ndarray, group 2 of points [lon,lat] in the size of (num_points, 2), radian
                
    Returns:    g_dis   :  2D np.ndarray, great circle distance between two groups, meter
    """

    R = 6371000 # meter
    A_tmp = np.sqrt(np.square(np.cos(B[:,1])*np.sin(A[:,0]-B[:,0])) +
    np.square(np.cos(A[:,1])*np.sin(B[:,1]) - np.sin(A[:,1])*np.cos(B[:,1])*np.cos(A[:,0]-B[:,0])))
    B_tmp = np.sin(A[:,1])*np.sin(B[:,1]) + np.cos(A[:,1])*np.cos(B[:,1])*np.cos(A[:,0]-B[:,0])
    radian = np.arctan2(A_tmp,B_tmp)
    g_dis = R*radian
    return g_dis

def ref2reference(data,lon,lat,ref_lon,ref_lat,radius=1000):
    """ reference values to the reference point
    
    Parameters: data    :   2D np.ndarray in size of (num_date,num_pixels), InSAR data
                lon     :   1D np.ndarray in size of (num_pixels,), Longitude
                lat     :   1D np.ndarray in size of (num_pixels,), Latitude
                ref_lon :   float, longitude of the reference point
                ref_lat :   float, latitude of the reference point
                radius  :   int or float, searching radius for the neighboring pixels from the reference point
    
    Returns:    data    :   2D np.ndarray in size of (num_date,num_pixels), referenced InSAR data
    """
    ind = gc_distance_lonlat(np.deg2rad(np.vstack((lon,lat)).T),np.deg2rad(np.vstack((ref_lon,ref_lat)).T)) < radius 
    data = data - data[ind].mean()
    return data

def Coh2phaseVar(coh,num_looks):
    coh_tmp = coh.copy() # avoid changing the original values
    coh_tmp[coh_tmp < 0.01] = 0.01 # avoid infinite variance
    coh_tmp[coh_tmp > 0.99] = 0.99 # avoid 0 variance
    return (1 - coh_tmp**2) / (2 * coh_tmp**2 * num_looks)