import gdal
from affine import Affine
from osgeo import osr
from utils.quadhash_utils import *
from utils.im_manipulation import *


def get_gdal_bounds(gdal_obj):
    xmin, xpixel, _, ymax, _, ypixel = gdal_obj.GetGeoTransform()
    width, height = gdal_obj.RasterXSize, gdal_obj.RasterYSize
    xmax = xmin + width * xpixel
    ymin = ymax + height * ypixel

    ext = [(xmin, ymin), (xmax, ymax)]

    src_srs = osr.SpatialReference()
    src_srs.ImportFromWkt(gdal_obj.GetProjection())
    tgt_srs = osr.SpatialReference()
    tgt_srs.ImportFromEPSG(4326)

    trans_coords = []
    transform = osr.CoordinateTransformation(src_srs, tgt_srs)
    # print("SRC TRANSFORM:", src_srs)
    for x, y in ext:
        x1, y1, z1 = transform.TransformPoint(x, y)
        trans_coords.append([x1, y1])
    #print(trans_coords)

    [[xmin1, ymin1], [xmax1, ymax1]] = trans_coords

    bounds = [[ymin1, xmin1], [ymin1, xmax1], [ymax1, xmax1], [ymax1, xmin1], [ymin1, xmin1]]

    return bounds



def retrieve_pixel_value(x,y,data_source):

    forward_transform = Affine.from_gdal(*data_source.GetGeoTransform())
    reverse_transform = ~forward_transform
    px, py = reverse_transform * (x, y)
    px, py = int(px + 0.5), int(py + 0.5)
    pixel_coord = px, py

    return pixel_coord

def retrive_coord_from_pixel(x, y, data_source):
    forward_transform = Affine.from_gdal(*data_source.GetGeoTransform())
    px, py = forward_transform * (x, y)
    px, py = int(px + 0.5), int(py + 0.5)
    pixel_coord = px, py

    return pixel_coord

def get_gdal_obj(filename):
    return gdal.Open(filename)

# GIVEN A SINGLE EPSG LAT-LON CONVERT TO REGULAR SYSTEM
def convert_EPSG_to_latlon(src_lat, src_lon, dataset):
    source = osr.SpatialReference()
    source.ImportFromWkt(dataset.GetProjection())

    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    # Create the transform - this can be used repeatedly
    transform = osr.CoordinateTransformation(source, target)

    lon, lat, z = transform.TransformPoint(src_lat, src_lon)
    return lat, lon

def get_pixel_from_lat_lon(latlons, dataset):
    #converting coordinate systems
    # Setup the source projection
    source = osr.SpatialReference()
    source.ImportFromWkt(dataset.GetProjection())
    #print(source)
    # The target projection
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    # Create the transform - this can be used repeatedly
    transform = osr.CoordinateTransformation(target, source)

    pixels=[]
    for lat,lon in latlons:
        x, y, z = transform.TransformPoint(lon, lat)

        ret = retrieve_pixel_value(x, y, dataset)
        #print("TRANSFORMED:", x, y, ret)
        pixels.append(ret)
    return pixels

# CROPPING A RECTANGLE OUT OF AN IMAGE
def crop_section(lat1, lat2, lon1, lon2, datafile):
    latlons = []
    latlons.append((lat1, lon1))
    latlons.append((lat2, lon1))
    latlons.append((lat2, lon2))
    latlons.append((lat1, lon2))
    return get_pixel_from_lat_lon(latlons, datafile)

if __name__ == "__main__":
    gdal_obj = get_gdal_obj("/s/chopin/b/others/sustain/sapmitra/M3/tiles/actuals/2020_05_08/ET_LC08_033032_20200508.tif")
    b = get_gdal_bounds(gdal_obj)
    print(b)
