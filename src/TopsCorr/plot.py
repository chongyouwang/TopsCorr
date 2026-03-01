import pygmt
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_gmt(data,lon,lat,region=None,ref_lonlat=None,title=None,fig_name='tmp',output_path=os.getcwd(),cmap=None,unit='m'):
    """ Plot the scatters 
    
    Parameters: data        : 1D np.ndarray, data
                lon         : 1D np.ndarray, longitude of the data
                lat         : 1D np.ndarray, latitude of the data
                ref_lonlat  : 2D np.ndarray in the size of (2,1), longitude and latitude of the reference point
    """
    if title is None:
        title = os.path.basename(fig_name)
    
    os.makedirs(output_path,exist_ok=True)
    if region is None:
        region = [lon.min(),
         lon.max(),
         lat.min(),
         lat.max()]
    #projection = 'B158/55/53/58/7C' # ise equil-area conic for high latitude regions
    projection = 'M7C'


    style = 'c0.03c'
    pen = ['0.015c'+','
        'black'
    ]
    ref_style = 'a0.40c' 
    pygmt.config(COLOR_FOREGROUND='black', COLOR_BACKGROUND='#FF00FF',COLOR_NAN='blue',MAP_FRAME_TYPE='plain',FONT_ANNOT_PRIMARY='12p',FONT_ANNOT_SECONDARY='12p',FONT_TITLE='18p')

    disp_cpt = 'tmp.cpt'
    color_min = data.min()
    color_max = data.max()
    #color_min = np.nanpercentile(data,0.01)
    #color_max = np.nanpercentile(data,99.99)
        
    if cmap is None:
        cmap = 'SCM/roma'
    pygmt.makecpt(cmap=cmap,
            series=[color_min,color_max,(color_max - color_min) / 20],
            reverse=True,
            overrule_bg=True,
            continuous=True,
            output=disp_cpt
            )

    frame = [
        'xa1f0.5',
        'ya1f0.5',
        f"WSne+t{title}"
        ]
    
    fig = pygmt.Figure()
    fig.basemap(region=region,projection=projection,frame=frame)
    fig.plot(data=np.vstack((lon,lat,data)).T,style=style,cmap=disp_cpt)
    if ref_lonlat is not None:
        fig.plot(x=ref_lonlat[0],y=ref_lonlat[1],style=ref_style,pen=pen,fill='red')
    fig.coast(region=region,frame=frame,resolution='f',shorelines='0.2p,black',area_thresh=2000,water='lightblue')
    fig.colorbar(position='JCB+w7c/0.3h+ebf',frame=f"af+l[{unit}]",cmap=disp_cpt)
    fig.psconvert(dpi=300,fmt='j',prefix=os.path.join(output_path,fig_name))
    
    
def plot_gmt_subplot(data1,data2,lon,lat,region=None,ref_lonlat=None,sub_title=None,fig_name='tmp',output_path=os.getcwd(),cmap=None,unit='m'):
    """ Plot the scatters 
    
    Parameters: data        : 1D np.ndarray, data
                lon         : 1D np.ndarray, longitude of the data
                lat         : 1D np.ndarray, latitude of the data
                ref_lonlat  : 2D np.ndarray in the size of (2,1), longitude and latitude of the reference point
    """
    if sub_title is None:
        sub_title = ['data1','data2']
    os.makedirs(output_path,exist_ok=True)
    region = [lon.min(),
         lon.max(),
         lat.min(),
         lat.max()]
    projection = 'M'


    style = 'c0.03c'
    pygmt.config(COLOR_FOREGROUND='black', COLOR_BACKGROUND='#FF00FF',COLOR_NAN='blue',MAP_FRAME_TYPE='plain',FONT_ANNOT_PRIMARY='12p',FONT_ANNOT_SECONDARY='12p',FONT_TITLE='18p')

    color_min = np.min(np.vstack((data1.min(),data2.min())))
    
    color_max = np.max(np.vstack((data1.max(),data2.max())))

    data_cpt = 'subplot.cpt'
    if cmap is None:
        data_cmap = 'SCM/roma'
    pygmt.makecpt(cmap=data_cmap,
            series=[color_min,color_max,'+n20'],
            reverse=True,
            overrule_bg=True,
            continuous=True,
            output=data_cpt
            )
    
    fig = pygmt.Figure()
    with fig.subplot(nrows=1,ncols=2,figsize=("25c", "10c"),autolabel='+JTC+o0p/5p',title=fig_name,frame='lrtb',sharex=True,sharey=True):
        with fig.set_panel(panel=0,fixedlabel=sub_title[0]):
            frame = [
                    'xa1f0.5',
                    'ya1f0.5',
                    'WSne'
                    ]
            fig.basemap(region=region,projection=projection,frame=frame)
            fig.plot(data=np.vstack((lon,lat,data1)).T,style=style,cmap=data_cpt)
            fig.coast(region=region,frame=frame,resolution='f',shorelines='0.2p,black',area_thresh=2000,water='lightblue')
            fig.colorbar(position=pygmt.params.Position('CB',cstype='outside'),length='5c',width='0.3c',frame=f"xaf+l[m]",cmap=data_cpt)
            
        with fig.set_panel(panel=1,fixedlabel=sub_title[1]):
            frame = [
                    'xa1f0.5',
                    'ya1f0.5',
                    'wsne'
                    ]
            fig.basemap(region=region,projection=projection,frame=frame)
            fig.plot(data=np.vstack((lon,lat,data2)).T,style=style,cmap=data_cpt)
            fig.coast(region=region,frame=frame,resolution='f',shorelines='0.2p,black',area_thresh=2000,water='lightblue')
            fig.colorbar(position=pygmt.params.Position('CB',cstype='outside'),length='5c',width='0.3c',frame=f"xaf+l[m]",cmap=data_cpt)
    fig.psconvert(dpi=300,fmt='j',prefix=os.path.join(output_path,fig_name))    
    

def plot_matlab(data, extent,
             title=None,colormap='gray',
             aspect=1, background=None,
             datamin=None, datamax=None,
             nodata = None,
             draw_colorbar=True, colorbar_orientation="horizontal"):
    try:
        if nodata is not None:
            data[data == nodata] = np.nan
    except:
        pass
    
    if background is None:
        try:
            data[data==0]=np.nan
        except:
            pass
    
    fig = plt.figure(figsize=(18, 16))
    ax = fig.add_subplot(111)
    cax = ax.imshow(data, vmin = datamin, vmax=datamax,
                    cmap=colormap, extent=extent)
    ax.set_title(title)
    if draw_colorbar is not None:
        cbar = fig.colorbar(cax,orientation=colorbar_orientation)
    ax.set_aspect(aspect)    
    plt.show()