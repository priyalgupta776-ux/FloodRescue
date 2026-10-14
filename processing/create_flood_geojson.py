
import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
import os

with rasterio.open("data/processed/flood_mask.tif") as src:
    mask = src.read(1)
    transform = src.transform
    crs = src.crs

polygons = [
    shape(geom)
    for geom, value in shapes(mask, transform=transform)
    if value == 1
]

flood = gpd.GeoDataFrame(geometry=polygons, crs=crs)
os.makedirs("data/outputs", exist_ok=True)

flood.to_file(
    "data/outputs/flood_extent.geojson",
    driver="GeoJSON"
)

print("Flood map saved. Polygons:", len(flood))

