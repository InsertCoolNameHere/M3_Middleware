import utils.im_manipulation as ImageManipulator
import utils.quadhash_utils as QuadTile
from osgeo import gdal,ogr,osr
import numpy as np
import os
from os import walk
import time
import datetime
import json
import urllib
import pymongo
import data.mongo_loader as MongoLoader

#https://gis.stackexchange.com/questions/264793/crop-raster-in-memory-with-python-gdal-bindings
invalid_val = -7777
valid_ranges = {
    "ET":(-1,14),
    "OPENET": (-1, 14),
    "NDVI": (-1,1),
    "LST": (183,360)
}

username = urllib.parse.quote_plus('root')
password = urllib.parse.quote_plus('rootPass')
mongo_url = 'mongodb://%s:%s@lattice-100:27018/' % (username, password)

et_aggregates_collection = "et_aggregates"
sustain_db_name = "sustaindb"
file_ref_collection = "et_tiles"

sustainclient = pymongo.MongoClient(mongo_url)

sustain_db = sustainclient[sustain_db_name]
aggregates_collection = sustain_db[et_aggregates_collection]
fileref_collection = sustain_db[file_ref_collection]



def get_filetype(filepath):
    filename = os.path.basename(filepath)
    tokens = filename.split("_")
    filetype = tokens[0]
    return filetype

def get_valid_range(filepath):
    filetype = get_filetype(filepath)
    if filetype in valid_ranges.keys():
        return valid_ranges[filetype]

    return None

def extract_date_from_tiff(file_path):
    file_tokens = file_path.split(os.sep)

    date_string = file_tokens[-2]
    return time.mktime(datetime.datetime.strptime(date_string,"%Y_%m_%d").timetuple())

def find_valid_mean(cropped_data, rh, rl):
    # perform come calculations with ...
    if cropped_data is None:
        #print("MEAN: ", 0)
        return 0.0,0.0
    if cropped_data.any():
        cropped_data = cropped_data.astype('float64')
        data = cropped_data[(cropped_data <= rh) & (cropped_data>= rl)]
        if (not data is None) and (data.size > 0):
            mean = np.mean([x for x in data if x != None]), data.size
        else:
            mean = 0.0,0.0
    else:
        mean = 0.0,0.0
    #print("MEAN: ", mean)
    return mean

def summarise_individual_tiff(test_img, zoom, summary_dict, timestamp_info):
    datatype = get_filetype(test_img)

    (vl,vh) = get_valid_range(test_img)

    gdal_obj = ImageManipulator.get_gdal_obj(test_img)
    single_band = gdal_obj.GetRasterBand(1)

    #print(type(single_band))

    xmin, xpixel, _, ymax, _, ypixel = gdal_obj.GetGeoTransform()
    width, height = gdal_obj.RasterXSize, gdal_obj.RasterYSize
    xmax = xmin + width * xpixel
    ymin = ymax + height * ypixel

    tot_X = gdal_obj.RasterXSize
    tot_Y = gdal_obj.RasterYSize
    bands = gdal_obj.RasterCount

    ext = [(xmin, ymin), (xmax, ymax)]

    #print("MAIN BOUNDS:",ext, bands, tot_X, tot_Y)

    src_srs=osr.SpatialReference()
    src_srs.ImportFromWkt(gdal_obj.GetProjection())
    tgt_srs = osr.SpatialReference()
    tgt_srs.ImportFromEPSG(4326)

    trans_coords=[]
    transform = osr.CoordinateTransformation(src_srs, tgt_srs)
    #print("SRC TRANSFORM:", src_srs)
    for x,y in ext:
        x1,y1,z1 = transform.TransformPoint(x,y)
        trans_coords.append([x1,y1])
    #print(trans_coords)

    [(xmin1, ymin1), (xmax1, ymax1)] = trans_coords

    target_tiles, target_hashes = QuadTile.find_all_inside_box(xmin1, xmax1, ymin1, ymax1, zoom)
    #print("THHH", target_hashes)

    cnt = 0
    for tt in target_tiles:
        quadtile_hash = target_hashes[cnt]
        try:
            cropped_data, bound_latlons = ImageManipulator.image_chopper_gdal_new(gdal_obj, single_band, tt, xmin, ymax, xpixel, ypixel, tot_X, tot_Y)

            avg_val, count = find_valid_mean(cropped_data, vh, vl)

            if quadtile_hash in summary_dict.keys():
                quadtile_summary = summary_dict[quadtile_hash]
                if datatype in quadtile_summary.keys():
                    old_datatype_summary = quadtile_summary[datatype]
                    old_val = old_datatype_summary["val"]
                    old_cnt = old_datatype_summary["count"]

                    new_tot = old_val*old_cnt + avg_val*count
                    newcount = old_cnt + count

                    if newcount > 0:
                        datatype_summary = {"val": float(new_tot/newcount), "count": newcount}
                        quadtile_summary[datatype] = datatype_summary
                    else:
                        pass
                else:
                    datatype_summary = {"val": avg_val, "count": count}
                    quadtile_summary[datatype] = datatype_summary

            else:
                #Setting Up Quadtile
                quadtile_summary = {}
                quadtile_summary["type"] = "Feature"
                geometry_dict = {"type": "Polygon"}
                quadtile_summary["geometry"] = geometry_dict
                quadtile_summary["timestamp"] = timestamp_info
                quadtile_summary["zoom"] = zoom
                geometry_dict["coordinates"] = [bound_latlons]

                # Adding Attribute Values
                datatype_summary = {"val":avg_val, "count":count}
                quadtile_summary[datatype] = datatype_summary

            summary_dict[quadtile_hash] = quadtile_summary
            cnt += 1
        except Exception as e:
            print(">>>>>>>>>>>>>>>>>>>", e)

    #print(summary_dict)

def summary_dict_to_features(summary_dict, features_array):

    for qt in summary_dict.keys():
        quadtile_summary = summary_dict[qt]
        feature = {}
        feature["type"] = quadtile_summary["type"]
        feature["geometry"] = quadtile_summary["geometry"]
        prop_dict = {}
        feature["properties"] = prop_dict

        prop_dict["quadtile"] = qt
        prop_dict["timestamp"] = quadtile_summary["timestamp"]
        prop_dict["zoom"] = quadtile_summary["zoom"]

        for k in valid_ranges.keys():
            summ = quadtile_summary[k]
            if summ['count'] > 0:
                prop_dict[k] = summ['val']
            else:
                prop_dict[k] = invalid_val

        features_array.append(feature)


def summarise_all_tifs(folder_path, zoom, first_time):
    features_array = []
    #full_summary_json = { "type": "FeatureCollection", "features": features_array}
    full_summary_json = features_array

    #THIS WILL BE CONVERTED INTO the features_array
    summary_dict = {}

    all_tifs = []
    for (dirpath, dirnames, filenames) in walk(folder_path):
        for fn in filenames:
            #print(fn)
            if fn.endswith(".tif") or fn.endswith(".tiff"):
                all_tifs.append(os.path.join(dirpath,fn))
    print(all_tifs)
    for tf in all_tifs:
        timestamp_info = extract_date_from_tiff(tf)
        # AGGREGATING A TIFF FILE
        summarise_individual_tiff(tf, zoom, summary_dict, timestamp_info)

        if first_time:
            # ACTUAL SAVING THE TIFF OBJECT AND KEY TO MONGODB
            bandtype = get_filetype(tf)
            file_features = MongoLoader.load_and_save_tif(tf, timestamp_info, bandtype)
            print("TIFF FILE SUCCESSFULLY SAVED TO GRIDFS")
            fileref_collection.insert_many(file_features)
            print("TIFF FILE INFORMATION SAVED TO MONGODB")

    if len(summary_dict) > 0:
        summary_dict_to_features(summary_dict, features_array)
    else:
        return

    # DATA INSERTION INTO MONGODB
    print(">>>>>>>>>>>>>>\n",full_summary_json)

    # ACTUAL SAVING OF AGGREGATED DATA INTO MONGODB
    file_data = full_summary_json

    aggregates_collection.insert_many(file_data)

if __name__=='__main__':
    zoom_levels = [14,15,16]
    first_time = True
    for z in zoom_levels:
        summarise_all_tifs("/s/chopin/b/others/sustain/sapmitra/M3/tiles/actuals/",z, first_time)
        first_time = False