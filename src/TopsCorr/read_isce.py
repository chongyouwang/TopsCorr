from osgeo import gdal
import xml.etree.ElementTree as ET
import datetime as dt

def gdal_crop(infile,outfile,crop_region):
    # crop_region=[ulx,uly,lrx,lry]
    #gdal_crop(dem_file,[transform['x0'],transform['y0'],transform['x_end'],transform['y_end']],'dem/crop_dem.vrt')
    gdal.Translate(outfile,infile,projWin=crop_region,format='VRT')
    
def gdal_detum_switch(infile,outfile,datum_in,datum_out):
    gdal.Warp(
        outfile,
        infile,
        srcSRS=datum_in,
        dstSRS=datum_out,
        format='VRT'
    )   
    
def gdal_downsample(infile,outfile,resolution):    
    options = gdal.TranslateOptions(
    format="VRT",
    xRes=resolution,  # Target resolution X
    yRes=resolution,  # Target resolution Y
    resampleAlg="nearest"
)
    gdal.Translate(outfile,infile,options=options)
    
def get_sensing_time(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()   
    t_st = []
    t_ed = []
    
    for t in root.findall(".//property[@name='sensingstart']/value"):
        t_st.append(dt.datetime.strptime(t.text, '%Y-%m-%d %H:%M:%S.%f'))
        
    for t in root.findall(".//property[@name='sensingstop']/value"):
        t_ed.append(dt.datetime.strptime(t.text, '%Y-%m-%d %H:%M:%S.%f'))
        
    t_start = t_st[0] + (t_st[-1] - t_st[0]) /2
    t_end = t_ed[0] + (t_ed[-1] - t_ed[0]) /2
    t_avg = t_start + (t_end - t_start)/2
    return t_avg

def get_looks(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()   
    range_looks = int(root.find(".//property[@name='range looks']").text)
    azi_looks = int(root.find(".//property[@name='azimuth looks']").text)
    return range_looks,azi_looks

def read_data(data,band=1):
    ds = gdal.Open(data,gdal.GA_ReadOnly)
    data = ds.GetRasterBand(band).ReadAsArray()
    transform = ds.GetGeoTransform()
    del ds
    x0 = transform[0]
    dx = transform[1]
    y0 = transform[3]
    dy = transform[5]
    x_size = data.shape[1]
    y_size = data.shape[0]
    x_end = x0 + dx * x_size
    y_end = y0 + dy * y_size
    transform = {'x0':x0,'y0':y0,'dx':dx,'dy':dy,'x_size':x_size,'y_size':y_size,'x_end':x_end,'y_end':y_end}
    return data,transform