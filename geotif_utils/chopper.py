from contextlib import contextmanager
import sys, os


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


# with suppress_stdout():
from sentinelsat import SentinelAPI
import geopandas as gpd
import folium
import pandas as pd
import numpy as np
import fiona
import geopandas as gpd
import shapely
from shapely import geometry
from shapely.geometry import MultiPolygon, Polygon
import rasterio as rio
import re

shapely.speedups.disable()
import glob
import re
import zipfile
from affine import Affine
from pyproj import Proj, transform, CRS
import socket
import shutil
from datetime import date, timedelta
import time
import subprocess
from rasterio import mask as msk

# print("STARTED")
current_date = str(date.today() - timedelta(days=1)).replace("-", "")
tomorrow_date = str(date.today() + timedelta(days=1)).replace("-", "")
# pd.set_option('display.max_colwidth', None)
os.makedirs("coords", exist_ok=True)
os.makedirs("zips", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("county", exist_ok=True)
os.makedirs("tiffs", exist_ok=True)
counties = gpd.read_file('Colorado_Counties/Colorado_Counties.shp').to_crs(32613)
for ind, row in counties.iterrows():
    if row["lattice"] == socket.gethostname():
        os.makedirs(row["COUNTY"].upper().replace(" ", "_"), exist_ok=True)
for f in glob.glob('data/*'):
    os.remove(f)

if not os.path.exists('coords/Colorado.shp'):
    lat_point_list = [41.002439, 36.993060, 36.993060, 41.002439, 41.002439]
    lat_point_list = [41.002439, 37.3, 37.3, 41.002439, 41.002439]
    lon_point_list = [-102.042051, -102.042051, -109.045247, -109.045247, -102.042051]
    polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
    crs = CRS('EPSG:4326')
    polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
    #         polygon.to_file(filename='coords/' + str(x) + '_' + str(y) + '.geojson', driver='GeoJSON')
    polygon.to_file(filename='coords/Colorado.shp', driver="ESRI Shapefile")

user = 'sarmst'
password = 'Ellieis2crazy!!!'
api = SentinelAPI(user, password, 'https://scihub.copernicus.eu/dhus')
nReserve = gpd.read_file('coords/Colorado.shp')
footprint = None
for i in nReserve['geometry']:
    footprint = i

products = api.query(footprint,
                     date=(current_date, tomorrow_date),
                     platformname='Sentinel-2',
                     processinglevel='Level-2A',
                     #                      cloudcoverpercentage = (0,10)
                     )

products_gdf = api.to_geodataframe(products)
while products_gdf.empty:
    time.sleep(1800)
    products = api.query(footprint,
                         date=(str(date.today()).replace("-", ""), str(date.today()).replace("-", "")),
                         platformname='Sentinel-2',
                         processinglevel='Level-2A',
                         #                      cloudcoverpercentage = (0,10)
                         )
    products_gdf = api.to_geodataframe(products)

products_gdf_sorted = products_gdf.sort_values(['generationdate'], ascending=[False])

lattices = ['lattice-178',
            'lattice-179',
            'lattice-180',
            'lattice-181',
            'lattice-182',
            'lattice-183',
            'lattice-184',
            'lattice-185',
            'lattice-186',
            'lattice-187',
            'lattice-188',
            'lattice-189',
            'lattice-190',
            'lattice-191',
            'lattice-192',
            'lattice-193',
            'lattice-194',
            'lattice-195',
            'lattice-196',
            'lattice-197',
            'lattice-198',
            'lattice-199',
            'lattice-200',
            'lattice-201',
            'lattice-202',
            'lattice-203',
            'lattice-204',
            'lattice-205',
            'lattice-206',
            'lattice-207',
            'lattice-208',
            'lattice-209',
            'lattice-210',
            'lattice-211',
            'lattice-212',
            'lattice-213',
            'lattice-214',
            'lattice-215',
            'lattice-216',
            'lattice-217',
            'lattice-218',
            'lattice-219',
            'lattice-220',
            'lattice-221',
            'lattice-222',
            'lattice-223',
            'lattice-224',
            'lattice-225',
            ]

titles_dict = {}
index_dict = {}
lattice_dict = {}

for f in glob.glob('coords/lattice*'):
    os.remove(f)

for ind, poly in enumerate(products_gdf_sorted["geometry"]):
    lat_point_list = []
    lon_point_list = []
    for i in str(poly).replace('MULTIPOLYGON ', '').replace('(((', "").replace(')))', "").replace(", ", ",").split(','):
        lon_point_list.append(float(i.split(" ")[0]))
        lat_point_list.append(float(i.split(" ")[1]))
    polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
    crs = CRS('EPSG:4326')
    polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
    polygon.to_file(filename='coords/' + lattices[ind % 48] + "__" + products_gdf_sorted.index[ind] + "__" +
                             products_gdf_sorted["title"][ind] + '.shp', driver="ESRI Shapefile")
    index_dict[products_gdf.index[ind]] = lattices[ind % 48] + "__" + products_gdf_sorted.index[ind] + "__" + \
                                          products_gdf_sorted["title"][ind]
    titles_dict[products_gdf["title"][ind]] = lattices[ind % 48] + "__" + products_gdf_sorted.index[ind] + "__" + \
                                              products_gdf_sorted["title"][ind]

    if lattices[ind % 48] in lattice_dict.keys():
        lattice_dict[lattices[ind % 48]] = lattice_dict[lattices[ind % 48]].append(
            lattices[ind % 48] + "__" + products_gdf_sorted.index[ind] + "__" + products_gdf_sorted["title"][ind])
    else:
        lattice_dict[lattices[ind % 48]] = [
            lattices[ind % 48] + "__" + products_gdf_sorted.index[ind] + "__" + products_gdf_sorted["title"][ind]]

# listy = glob.glob("coords/lattice-*.shp")
listy = glob.glob("coords/" + socket.gethostname() + "*.shp")

for element in listy:

    if not os.path.exists("images/" + index_dict[re.search(r'__(.*?)__', element).group(1)]):

        api.download(re.search(r'__(.*?)__', element).group(1), directory_path="zips/")

        zip_files = glob.glob("zips/*")
        for zip_file in zip_files:
            with zipfile.ZipFile(zip_file) as zip_ref:
                zip_ref.extractall("images/")
            os.rename(zip_file.replace("zips/", "images/").replace(".zip", ".SAFE"),
                      "images/" + titles_dict[zip_file.replace("zips/", "").replace(".zip", "")])
        os.remove(zip_file)

for i in glob.glob("images/*"):
    B1_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R60m/*B01*")[0]
    B2_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R10m/*B02*")[0]
    B3_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R10m/*B03*")[0]
    B4_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R10m/*B04*")[0]
    B5_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R20m/*B05*")[0]
    B6_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R20m/*B06*")[0]
    B7_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R20m/*B07*")[0]
    B8_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R10m/*B08*")[0]
    B8a_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R20m/*B8A*")[0]
    B9_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R60m/*B09*")[0]
    # B10_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R60m/*B10*")[0]
    B11_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R20m/*B11*")[0]
    B12_file = glob.glob(i + "/GRANULE/*/IMG_DATA/R20m/*B12*")[0]

    b4 = rio.open(B4_file)
    with rio.open(i.replace("images", "data") + '_holder.tiff', 'w', driver='Gtiff', width=b4.width, height=b4.height,
                  count=12, crs=b4.crs, transform=b4.transform, dtype=b4.dtypes[0]) as img:
        img.write(rio.open(B1_file).read(1), 1)
        img.write(rio.open(B2_file).read(1), 2)
        img.write(rio.open(B3_file).read(1), 3)
        img.write(rio.open(B4_file).read(1), 4)
        img.write(rio.open(B5_file).read(1), 5)
        img.write(rio.open(B6_file).read(1), 6)
        img.write(rio.open(B7_file).read(1), 7)
        img.write(rio.open(B8_file).read(1), 8)
        img.write(rio.open(B8a_file).read(1), 9)
        img.write(rio.open(B9_file).read(1), 10)
        #     img.write(rio.open(B10_file).read(1),1)
        img.write(rio.open(B11_file).read(1), 11)
        img.write(rio.open(B12_file).read(1), 12)
        img.close()

    shutil.rmtree(i)

for fname in glob.glob("data/*_holder.tiff"):
    with rio.open(fname) as r:
        T0 = r.transform  # upper-left pixel corner affine transform
        p1 = Proj(r.crs)
        A = r.read()  # pixel values

    cols, rows = np.meshgrid(np.arange(A.shape[2]), np.arange(A.shape[1]))

    T1 = T0 * Affine.translation(0.5, 0.5)

    x, y = (rows, cols) * T1

    eastings, northings = x.T, y.T

    p2 = Proj(proj='latlong', datum='WGS84')

    longs, lats = transform(p1, p2, eastings, northings)

    b4 = rio.open(fname)
    with rio.open(fname.replace("_holder", ""), 'w', driver='Gtiff', width=b4.width, height=b4.height,
                  count=14, crs=b4.crs, transform=b4.transform, dtype=b4.dtypes[0]) as img:
        img.write(A[0], 1)
        img.write(A[1], 2)
        img.write(A[2], 3)
        img.write(A[3], 4)
        img.write(A[4], 5)
        img.write(A[5], 6)
        img.write(A[6], 7)
        img.write(A[7], 8)
        img.write(A[8], 9)
        img.write(A[9], 10)
        #     img.write(rio.open(B10_file).read(1),1)
        img.write(A[10], 11)
        img.write(A[11], 12)
        img.write(longs, 13)
        img.write(lats, 14)

        img.close()
    os.remove(fname)

for fname in glob.glob("data/*.tiff"):
    with rio.open(fname) as src:
        for ind, row in counties.iterrows():
            lattice1, poly1, county1 = row["lattice"], row["geometry"], row["COUNTY"].upper().replace(" ", "_")
            #             print(lattice1, county1, fname.replace("_holder", ""))
            try:
                #                 print("TRY")
                out_image, out_transform = msk.mask(src, [poly1], crop=True)
                out_meta = src.meta.copy()
                out_meta.update({"driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2],
                                 "transform": out_transform})

                with rio.open(fname.replace("data", "county"), "w", **out_meta) as dest:
                    dest.write(out_image)
                    dest.close()
                subprocess.run(["scp", fname.replace("data", "county"), "sarmst@" + lattice1 + ":" + county1 + "/"])

            except ValueError:
                #                 print("EXCEPT")
                continue
    os.remove(fname)

# print("DONE")