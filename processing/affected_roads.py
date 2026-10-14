import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape

mask_file = "data/processed/flood_mask.tif"
roads_file = "data/processed/roads.geojson"

# Read flood mask
with rasterio.open(mask_file) as src:
    mask = src.read(1)
    transform = src.transform
    crs = src.crs

# Convert flood pixels into polygons
flood_shapes = []

for geom, value in shapes(mask, transform=transform):
    if value == 1:
        flood_shapes.append(shape(geom))

print("Flood polygons created:", len(flood_shapes))

# Create GeoDataFrame
flood_gdf = gpd.GeoDataFrame(
    geometry=flood_shapes,
    crs=crs
)

# Merge flood polygons
flood_area = flood_gdf.union_all()

print("Flood geometry created.")

# Read roads
roads = gpd.read_file(roads_file)

# Convert roads to same CRS
roads = roads.to_crs(crs)

print("Total roads:", len(roads))

# Find roads that actually intersect flood extent
affected_roads = roads[
    roads.geometry.intersects(flood_area)
].copy()

print("Potentially affected road segments:", len(affected_roads))

# Save
affected_roads.to_file(
    "data/processed/affected_roads.geojson",
    driver="GeoJSON"
)

print("Saved: data/processed/affected_roads.geojson")
