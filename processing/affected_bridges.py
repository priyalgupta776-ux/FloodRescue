import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape

mask_file = "data/processed/flood_mask.tif"
bridges_file = "data/processed/bridges.geojson"

# Read flood mask
with rasterio.open(mask_file) as src:
    mask = src.read(1)
    transform = src.transform
    crs = src.crs

# Convert flood mask to polygons
flood_shapes = []

for geom, value in shapes(mask, transform=transform):
    if value == 1:
        flood_shapes.append(shape(geom))

flood_gdf = gpd.GeoDataFrame(
    geometry=flood_shapes,
    crs=crs
)

flood_area = flood_gdf.union_all()

print("Flood geometry created.")

# Read bridges
bridges = gpd.read_file(bridges_file)

bridges = bridges.to_crs(crs)

print("Total bridges:", len(bridges))

# Find bridges intersecting flood extent
affected_bridges = bridges[
    bridges.geometry.intersects(flood_area)
].copy()

print("Potentially affected bridges:", len(affected_bridges))

affected_bridges.to_file(
    "data/processed/affected_bridges.geojson",
    driver="GeoJSON"
)

print("Saved: data/processed/affected_bridges.geojson")
