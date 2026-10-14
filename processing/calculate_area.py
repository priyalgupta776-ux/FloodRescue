import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np

mask_file = "data/processed/flood_mask.tif"

with rasterio.open(mask_file) as src:

    # Equal-area projection
    target_crs = "EPSG:6933"

    transform, width, height = calculate_default_transform(
        src.crs,
        target_crs,
        src.width,
        src.height,
        *src.bounds
    )

    reprojected = np.zeros((height, width), dtype=np.uint8)

    reproject(
        source=rasterio.band(src, 1),
        destination=reprojected,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=target_crs,
        resampling=Resampling.nearest
    )

    # Pixel dimensions are now in metres
    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)

    flooded_pixels = np.sum(reprojected == 1)

    area_m2 = flooded_pixels * pixel_width * pixel_height
    area_km2 = area_m2 / 1_000_000

print("Flood candidate pixels:", flooded_pixels)
print("Pixel width:", pixel_width, "metres")
print("Pixel height:", pixel_height, "metres")
print("Estimated flooded area:", area_km2, "km²")
