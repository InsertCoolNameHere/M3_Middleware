import pymongo
import pickle
import gridfs
import datetime
import os
import gdal
from osgeo import gdal_array

import urllib.parse
"""
db['fs.chunks'].remove({files_id:my_id});
db['fs.files'].remove({_id:my_id});
"""

username = urllib.parse.quote_plus('root')
password = urllib.parse.quote_plus('rootPass')

mongo_url = 'mongodb://%s:%s@lattice-100:27018/' % (username, password)

query_collection = "et_tiles"
mongo_db_name = "sustaindb"
spahash_field = "spa_hash"
time_field = "gen_time"
gridfs_key = "tif_fs_id"

sustainclient = pymongo.MongoClient(mongo_url)
sustain_db = sustainclient[mongo_db_name]
fs = gridfs.GridFS(sustain_db)
sustain_collection = sustain_db[query_collection]

def get_gdal_obj(filename):
    return gdal.Open(filename)

def image_loader_gdal(filename):
    go1 = get_gdal_obj(filename)
    print(type(go1))
    gdal_obj = go1.ReadAsArray()#[0,2,1]
    return gdal_obj

def load_and_save_tif(tif_path):
    head, tail = os.path.split(tif_path)
    spahash = tail.replace(".tiff","")
    tifobj = image_loader_gdal(tif_path)
    print(tifobj.shape, spahash)
    return

    save_model(tifobj, spahash)

# SAVING TRAINED MODEL IN MONGODB
# ALSO SAVES IT IN IN-MEMORY MAP
def save_model(tif_image, tifs_hash):
    # LOCALLY SAVE IN-MEMORY ONLY FOR CENTROID MODELS
    # SAVE OTHERS IN MONGO-DB
    timestamp = datetime.datetime(2015, 7, 8)
    print(timestamp)

    ser_model = pickle.dumps(tif_image)
    fs_key = fs.put(ser_model)
    print("INSERTED TO GRIDFS...", fs_key)

    info = sustain_collection.update_one({"$and": [{spahash_field : tifs_hash}, {time_field: timestamp}]}, {"$set":{spahash_field:tifs_hash, gridfs_key: fs_key, time_field: timestamp}}, upsert=True)
    print("SAVED TRAINED_MODEL:", info)

def fetch_image(quadtile_key):
    client_query = {spahash_field: quadtile_key}
    query_results = list(sustain_collection.find(client_query))

    img_ser = fs.get(query_results[0]['tif_fs_id']).read()
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
    outdata.FlushCache()  ##saves to disk!!

load_and_save_tif("/s/parsons/b/others/sustain/sapmitra/M3/tiles/9x5n.tiff")
#fetch_image('9x5n')
