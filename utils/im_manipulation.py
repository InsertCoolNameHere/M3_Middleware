import os
from numpy import random
from PIL import Image
from utils.crop_utils import *
from utils.gdal_utils import *
import operator
import utils.quadhash_utils as QuadTile
import numpy as np
from rasterio import mask as msk
import rasterio as rio

# RETURNS ALL FILENAMES IN THE GIVEN DIRECTORY IN AN ARRAY
def get_filenames(source, ext):
    img_paths = []
    for roots, dir, files in os.walk(source):
        for file in files:
            if file.endswith(ext):
                file_abs_path = os.path.join(roots, file)

                img_paths.append(file_abs_path)
    #print("RETURNING...",len(img_paths))
    return img_paths

def is_image_file(filename, ext):
    return any(filename.lower().endswith(ext))

# RETURNING A TILE FROM $ INTERNAL GEOHASHES
def get_candidate_tiles(base_hash, length):
    internal_geohashes = get_internal_quad_hashes(base_hash, length)

    tot_tiles = len(internal_geohashes)

    if tot_tiles > 1:
        tile_selected = random.sample(range(0, tot_tiles), 1)[0]
        res_list = internal_geohashes[tile_selected]
        return res_list
    else:
        return internal_geohashes[0]


# GET INTERNAL TILES, ARRANGED ROW BY ROW
def get_sorted_internal_tiles(base_hash, length):
    quad_hashes_list = get_internal_quad_hashes(base_hash, length)
    # SORTING THE CHILDREN ROW BY ROW
    tiles = []
    for l in quad_hashes_list:
        tl = get_tile_from_key(l)
        tiles.append(tl)

    internal_geohashes = []
    for tile in sorted(tiles, key=operator.itemgetter(1)):
        internal_geohashes.append(get_quad_key_from_tile(tile.x, tile.y, tile.z))

    return internal_geohashes

#RANDOMLY PICKING THE PYRAMID TIP FOR THIS BATCH
def get_random_tip(numberList):
    #numberList = [0, 1, 2]
    return random.choices(numberList, weights=(1, 2, 4), k=1)[0]


def get_internal_quad_hashes(base_hash, length):
    internal_hashes = [base_hash]
    subfixes = ['0','1','2','3']
    incr = length-len(base_hash)
    tmp_list = []

    for i in range(0, incr):
        #print(i,"=========")
        for ap in internal_hashes:
            for s in subfixes:
                tmp_list.append(ap+s)
        internal_hashes = tmp_list
        #print("HERE", internal_hashes)
        tmp_list=[]
    return internal_hashes

def image_loader_gdal(filename):
    gdal_obj = get_gdal_obj(filename)
    return gdal_obj

def image_chopper_gdal_new(gdal_obj, band, target_tile, xmin, ymax, xpixel, ypixel, tot_X, tot_Y):
    north, south, east, west = QuadTile.get_bounds_from_tile_obj(target_tile)
    #print(north, south, east, west)

    latlons = []
    latlons.append((west, north))
    latlons.append((east, north))
    latlons.append((east, south))
    latlons.append((west, south))

    ret_latlons = []
    ret_latlons.append([west, north])
    ret_latlons.append([east, north])
    ret_latlons.append([east, south])
    ret_latlons.append([west, south])
    ret_latlons.append([west, north])

    #pixels = get_pixel_from_lat_lon(latlons, gdal_obj)

    source = osr.SpatialReference()
    source.ImportFromWkt(gdal_obj.GetProjection())
    # print(source)
    # The target projection
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    # Create the transform - this can be used repeatedly
    transform = osr.CoordinateTransformation(target, source)

    pixels = []
    for lat, lon in latlons:
        x, y, z = transform.TransformPoint(lon, lat)

        x_index = (x - xmin) / xpixel

        # and the same as the y
        y_index = (y - ymax) / ypixel

        if x_index<0:
            x_index = 0
        if y_index<0:
            y_index = 0

        if x_index>=tot_X:
            x_index = tot_X-1
        if y_index>=tot_Y:
            y_index = tot_Y-1

        #print("TRANSFORMED:", x, y, (x_index,y_index))
        pixels.append((int(x_index),int(y_index)))

    #print("PIXELS:", pixels)
    #(231, 148), (262, 148), (262, 178), (231, 178)
    row1 = pixels[0][0]
    col1 = pixels[0][1]

    row2 = pixels[2][0]
    col2 = pixels[2][1]


    #print(row1, col1, row2 - row1 + 1, col2 - col1 + 1)
    data = band.ReadAsArray(row1, col1, row2 - row1 + 1, col2 - col1 + 1)

    return data, ret_latlons

'''def image_chopper_gdal_XX(gdal_obj, target_tile, target_hash, filename):
    north, south, east, west = QuadTile.get_bounds_from_tile_obj(target_tile)
    print(north, south, east, west)

    latlons = []
    latlons.append((west, north))
    latlons.append((east, north))
    latlons.append((east, south))
    latlons.append((west, south))

    pixels = get_pixel_from_lat_lon(latlons, gdal_obj)

    print("PIXELS:", pixels)
    cropped = crop_irregular_polygon(pixels, filename)
    #cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)

    op = cropped
    print("NUMPY AVERAGE: ", target_hash, np.average(op))
    return Image.fromarray(op)
'''

def image_loader(path, mode='RGB'):
    # open path as file to avoid ResourceWarning
    # (https://github.com/python-pillow/Pillow/issues/835)
    with open(path, 'rb') as f:
        with Image.open(f) as img:
            return img.convert(mode)


def imageResize(image, pixel_res):
    new_image = image.resize((pixel_res, pixel_res))
    return new_image

# IMAGE DOWNGRADING
    # img: PIL image
    # DECREASE RESOLUTION OF IMAGE BY FACTOR OF 2^pow
def downscaleImage(img, scale, method=Image.BICUBIC):
    ow, oh = img.size

    h = int(round(oh / scale))
    w = int(round(ow / scale))
    return img.resize((w, h), method)

def crop_boundaries(im, cs):
    if cs > 1:
        return im[cs:-cs, cs:-cs, ...]
    else:
        return im

def mod_crop(im, scale):
    h, w = im.shape[:2]
    # return im[(h % scale):, (w % scale):, ...]
    return im[:h - (h % scale), :w - (w % scale), ...]

# GIVEN AN IMAGE, CROP OUT A CENTER SQUARE SECTION FROM IT
def center_crop(crop_size, hr):
    oh_hr = ow_hr = crop_size
    w_hr, h_hr = hr.size
    offx_hr = (w_hr - crop_size) // 2
    offy_hr = (h_hr - crop_size) // 2

    return hr.crop((offx_hr, offy_hr, offx_hr + ow_hr, offy_hr + oh_hr)), offy_hr, offx_hr

# GIVEN AN IMAGE, CROP OUT A RANDOM SQUARE SECTION FROM IT
def random_crop(crop_size, hr):
    oh_hr = ow_hr = crop_size
    imw_hr, imh_hr = hr.size

    x0 = 0
    x1 = imw_hr - ow_hr + 1

    y0 = 0
    y1 = imh_hr - oh_hr + 1

    # RANDOM CROP OFFSET NW
    offy_hr = random.randint(y0, y1)
    offx_hr = random.randint(x0, x1)

    return hr.crop((offx_hr, offy_hr, offx_hr + ow_hr, offy_hr + oh_hr)), offy_hr, offx_hr

#GIVEN A GxG GRID, RANDOMLY PICK AN OFFSET FOR A CxC SUB-GRID
def random_tile_offset(grid_size, cut_size):
    #print("BOUND:",grid_size-cut_size+1)
    offy_hr = random.randint(0, grid_size-cut_size)
    offx_hr = random.randint(0, grid_size-cut_size)
    return offx_hr,offy_hr

def crop_image_tiles(hr, gen, offset, tile_wh, tile_size):
    x,y = offset
    off_x_1 = tile_wh*x
    off_x_2 = tile_wh*(x+tile_size)
    off_y_1 = tile_wh * y
    off_y_2 = tile_wh * (y + tile_size)
    return hr[:,:,off_y_1:off_y_2,off_x_1:off_x_2], gen[:,:,off_y_1:off_y_2,off_x_1:off_x_2]

def crop_image_tiles_alt(hr, gen, offset, tile_wh, tile_size):
    x,y = offset
    off_x_1 = tile_wh*x
    off_x_2 = tile_wh*(x+tile_size)
    off_y_1 = tile_wh * y
    off_y_2 = tile_wh * (y + tile_size)
    return hr[:,off_y_1:off_y_2,off_x_1:off_x_2], gen[:,off_y_1:off_y_2,off_x_1:off_x_2]

