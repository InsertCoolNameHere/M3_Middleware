import pymongo
import pickle
import gridfs
import datetime
import os
import gdal
from osgeo import gdal_array
from utils.gdal_utils import get_gdal_bounds
import json
import urllib.parse
import ast
import time
import numpy as np
"""
db['fs.chunks'].remove({files_id:my_id});
db['fs.files'].remove({_id:my_id});
"""

'''
Reads a tiff file and creates an entry for it in a mongo collection and saves the actual tiff file into gridfs.
'''

username = urllib.parse.quote_plus('root')
password = urllib.parse.quote_plus('rootPass')

mongo_url = 'mongodb://%s:%s@lattice-100:27018/' % (username, password)

query_collection = "et_aggregates"
mongo_db_name = "sustaindb"

sustainclient = pymongo.MongoClient(mongo_url)
sustain_db = sustainclient[mongo_db_name]
fs = gridfs.GridFS(sustain_db)
sustain_collection = sustain_db[query_collection]

tile_collection_name = "et_tiles"
tile_collection = sustain_db[tile_collection_name]

def get_gdal_obj(filename):
    return gdal.Open(filename)

def image_loader_gdal(filename):
    go1 = get_gdal_obj(filename)
    print(type(go1))
    gdal_obj = go1.ReadAsArray()#[0,2,1]
    return go1,gdal_obj

def load_and_save_tif(tifpath, timestamp, bandtype):
    tifobj, tiffasarray = image_loader_gdal(tifpath)

    features_array = []
    feature = {}
    feature["type"] = "Feature"
    geometry_dict = {"type": "Polygon"}
    geometry_dict["coordinates"] = [get_gdal_bounds(tifobj)]
    feature["geometry"] = geometry_dict

    prop_dict = {}
    feature["properties"] = prop_dict
    prop_dict["timestamp"] = timestamp

    features_array.append(feature)
    fs_key = save_tiff_gdal(tiffasarray)
    prop_dict["fs_key"] = fs_key
    prop_dict["bandtype"] = bandtype

    return features_array

# SAVING TRAINED MODEL IN MONGODB
# ALSO SAVES IT IN IN-MEMORY MAP
def save_tiff_gdal(tif_image):
    ser_model = pickle.dumps(tif_image)
    fs_key = fs.put(ser_model)
    print("INSERTED TO GRIDFS...", fs_key)

    return fs_key

# Fetch Matching quadtiles
def fetch_aggregates(bounds_str, z, dateString, band):
    d_start = dateString+' 00:00:00'
    d_end = dateString+' 23:59:59'

    timestamp1 = time.mktime(datetime.datetime.strptime(d_start, "%Y/%m/%d %H:%M:%S").timetuple())
    timestamp2 = time.mktime(datetime.datetime.strptime(d_end, "%Y/%m/%d %H:%M:%S").timetuple())

    bounds = ast.literal_eval(bounds_str)

    poly1 = {"type": "Polygon", "coordinates": [bounds]}
    client_query = {"geometry": {"$geoIntersects": {"$geometry": poly1}}, "properties.zoom":z, "properties.timestamp":{"$gte":timestamp1,"$lte": timestamp2}}

    query_results = list(sustain_collection.find(client_query))

    print("RESULTS FOUND:", query_results)
    return query_results

# Fetching a tiff from mongodb
def fetch_image(bounds_str, z, dateString, band):
    d_start = dateString + ' 00:00:00'
    d_end = dateString + ' 23:59:59'

    timestamp1 = time.mktime(datetime.datetime.strptime(d_start, "%Y/%m/%d %H:%M:%S").timetuple())
    timestamp2 = time.mktime(datetime.datetime.strptime(d_end, "%Y/%m/%d %H:%M:%S").timetuple())
    bounds = ast.literal_eval(bounds_str)

    poly1 = {"type": "Polygon", "coordinates": [bounds]}
    client_query = {"geometry": {"$geoIntersects": {"$geometry": poly1}}, "properties.timestamp":{"$gte":timestamp1,"$lte": timestamp2}, "properties.bandtype":band}
    query_results = list(tile_collection.find(client_query))

    print(len(query_results))

    print(query_results)

    serialized_images = []
    for qr in query_results:
        img_ser = fs.get(qr['properties']['fs_key']).read()
        img_obj = pickle.loads(img_ser)
        ds = gdal_array.OpenArray(img_obj)
        serialized_images.append(ds)

    return serialized_images

    '''img_ser = fs.get(query_results[0]['tif_fs_id']).read()
    img_obj = pickle.loads(img_ser)

    print(type(img_obj), img_obj.shape)
    ds = gdal_array.OpenArray(img_obj)
    print(type(ds))

    driver = gdal.GetDriverByName("GTiff")
    (band, rows, cols) = img_obj.shape
    outdata = driver.Create("op.tiff", cols, rows, band, gdal.GDT_UInt16)
    outdata.SetGeoTransform(ds.GetGeoTransform())  ##sets same geotransform as input
    outdata.SetProjection(ds.GetProjection())  ##sets same projection as input
    #outdata.GetRasterBand(1).WriteArray(arr_out)
    #outdata.GetRasterBand(1).SetNoDataValue(10000)  ##if you want these values transparent
    outdata.FlushCache()  ##saves to disk!!'''

if __name__ == "__main__":
    #tifpath = "/s/parsons/b/others/sustain/sapmitra/M3/tiles/9x5n.tiff"
    #load_and_save_tif(tifpath)
    bounds = "[[-105.05126953125, 40.69729900863674], [-105.029296875, 40.69729900863674], [-105.029296875, 40.68063802521457], [-105.05126953125, 40.68063802521457], [-105.05126953125, 40.69729900863674]]"

    dateString = "2020/05/08"

    fetch_image(bounds, 14, dateString, "ET")
