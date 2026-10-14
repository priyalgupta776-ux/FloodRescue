import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape

mask_file = "data/processed/flood_mask.tif"
buildings_file = "data/processed/buildings.geojson"

with rasterio.open(mask_file) as src:
    mask = src.read(1)
    transform = src.transform
    crs = src.crs

flood_shapes = []

for geom, value in shapes(mask, transform=transform):
    if value == 1:
        flood_shapes.append(shape(geom))

print("Flood polygons created:", len(flood_shapes))

flood_gdf = gpd.GeoDataFrame(
    geometry=flood_shapes,
    crs=crs
)

flood_area = flood_gdf.union_all()

print("Flood geometry created.")

buildings = gpd.read_file(buildings_file)
buildings = buildings.to_crs(crs)

print("Total buildings:", len(buildings))

affected_buildings = buildings[
    buildings.geometry.intersects(flood_area)
].copy()

print("Potentially affected buildings:", len(affected_buildings))

affected_buildings.to_file(
    "data/processed/affected_buildings.geojson",
    driver="GeoJSON"
)

print("Saved: data/processed/affected_buildings.geojson")
