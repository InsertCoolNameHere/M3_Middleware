import geohash2
import spatial_hash_utils.quadtree as quadtree
import mercantile

#print(geohash2.encode(42.6, -5.6))
#pip3.6 install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}') --user

# GET QUADHASH TILE OF A GIVEN COORDINATE
def get_quad_tile(lat, lon, precision):
    ret = mercantile.tile(lon,lat,precision)
    return ret

def get_quad_key_from_tile(x, y, zoom):
    return mercantile.quadkey(x, y, zoom)

# GET QUADHASH STRING OF A GIVEN COORDINATE
def get_quad_key(lat, lon, zoom):
    tile = get_quad_tile(lat, lon, precision=zoom)
    print(tile)
    return get_quad_key_from_tile(tile.x, tile.y, tile.z)

#GIVEN A ZOOM LEVEL, WHAT IS THE MAX POSSIBLE TILE INDEX NUMBER HERE?
def get_max_possible_xy(zoom):
    if zoom == 0:
        return 0
    return 2**zoom-1


# GIVEN A TILE, VERIFY IT IS VALID
def validate_tile(tile):
    max_xy = get_max_possible_xy(tile.z)

    if tile.x > max_xy or tile.x < 0 or tile.y > max_xy or tile.y < 0:
        return False

    return True


# GIVEN A BOX, FIND ALL TILES THAT LIE INSIDE THAT COORDINATE BOX
def find_all_inside_box(lat1, lat2, lon1, lon2, zoom):
    all_tiles = []
    top_left_quad_tile = get_quad_tile(lat2, lon1, zoom)
    bottom_right_quad_tile = get_quad_tile(lat1, lon2, zoom)

    print("TOP_LEFT & BOTTOM_RIGHT: ",top_left_quad_tile, bottom_right_quad_tile)

    x1 = top_left_quad_tile.x
    x2 = bottom_right_quad_tile.x

    y1 = top_left_quad_tile.y
    y2 = bottom_right_quad_tile.y

    for i in range(x1, x2+1):
        for j in range(y1,y2+1):
            all_tiles.append(mercantile.Tile(x=i,y=j,z=zoom))

    return all_tiles

#GIVEN A QUAD_TILE, GET ITS LAT-LNG BOUNDS
def get_bounding_lng_lat(tile):
    return (mercantile.bounds(tile))

if __name__ == '__main__':

    lat2 = 42.002207
    lat1 = 35.001857
    lon1 = -120.005746
    lon2 = - 114.039648
    tile = get_quad_tile(39.751913, -104.968066, 11)
    print("TILE",tile)

    print("BOUNDS",get_bounding_lng_lat(tile))
    print (lat1,lon1)
    print(get_quad_key(39.751913, -104.968066, 11))

    all_tiles = find_all_inside_box(lat1,lat2,lon1,lon2,11)
    print(all_tiles)
    print(len(all_tiles))

