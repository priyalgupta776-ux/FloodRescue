import rasterio
import numpy as np
import os

before_file = "data/raw/before_vv.tif"
after_file = "data/raw/after_vv.tif"

output_file = "data/processed/flood_mask.tif"

with rasterio.open(before_file) as before_src:
    before = before_src.read(1)
    profile = before_src.profile

with rasterio.open(after_file) as after_src:
    after = after_src.read(1)

print("Before image loaded:", before.shape)
print("After image loaded:", after.shape)

# Calculate change between before and after images
change = before - after

print("Change calculated.")
print("Minimum change:", np.nanmin(change))
print("Maximum change:", np.nanmax(change))

# Initial flood detection threshold
threshold = 3.0

flood_mask = (change > threshold).astype(np.uint8)

# Save flood mask
os.makedirs("data/processed", exist_ok=True)

profile.update(
    dtype=rasterio.uint8,
    count=1,
    nodata=0
)

with rasterio.open(output_file, "w", **profile) as dst:
    dst.write(flood_mask, 1)

flood_pixels = np.sum(flood_mask)

print("Flood detection completed.")
print("Flood candidate pixels:", flood_pixels)
print("Saved:", output_file)
