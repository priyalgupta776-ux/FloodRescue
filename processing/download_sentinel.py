
import os
import sys
import requests
from datetime import datetime, timedelta
import rasterio
import numpy as np

# Usage:
# python processing/download_sentinel.py west south east north flood_date before
# python processing/download_sentinel.py west south east north flood_date after

if len(sys.argv) != 7:
    print("Usage: download_sentinel.py west south east north YYYY-MM-DD before|after")
    sys.exit(1)

west, south, east, north = map(float, sys.argv[1:5])
flood_date = sys.argv[5]
period = sys.argv[6].lower()

if period not in ("before", "after"):
    print("Period must be 'before' or 'after'.")
    sys.exit(1)


try:
    event_date = datetime.strptime(flood_date, "%Y-%m-%d")
    if event_date.year < 2000 or event_date.date() > datetime.now().date():
        print("Invalid flood date. Use a date between 2000 and today.")
        sys.exit(1)
except ValueError:
    print("Flood date must use YYYY-MM-DD.")
    sys.exit(1)


if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
    print("Invalid bounding box.")
    sys.exit(1)

client_id = os.environ.get("CDSE_CLIENT_ID")
client_secret = os.environ.get("CDSE_CLIENT_SECRET")

if not client_id or not client_secret:
    print("Missing CDSE_CLIENT_ID or CDSE_CLIENT_SECRET environment variables.")
    sys.exit(1)

if period == "before":
    start_date = event_date - timedelta(days=27)
    end_date = event_date - timedelta(days=1)
    output_file = "data/raw/before_vv.tif"
else:
    start_date = event_date
    end_date = event_date + timedelta(days=7)
    output_file = "data/raw/after_vv.tif"

token_url = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)
process_url = "https://sh.dataspace.copernicus.eu/process/v1"

print("Authenticating with Copernicus Data Space...")

token_response = requests.post(
    token_url,
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    },
    timeout=60
)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]

evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["VV"],
        output: {
            bands: 1,
            sampleType: SampleType.FLOAT32
        }
    };
}
function evaluatePixel(samples) {
    return [samples.VV];
}
"""

request_body = {
    "input": {
        "bounds": {
            "bbox": [west, south, east, north],
            "properties": {
                "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
            }
        },
        "data": [{
            "type": "sentinel-1-grd",
            "dataFilter": {
                "timeRange": {
                    "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    "to": end_date.strftime("%Y-%m-%dT23:59:59Z")
                },
                "acquisitionMode": "IW"
            },
            "processing": {
                "orthorectify": True,
                "demInstance": "COPERNICUS_30"
            }
        }]
    },
    "output": {
        "width": 1000,
        "height": 1000,
        "responses": [{
            "identifier": "default",
            "format": {"type": "image/tiff"}
        }]
    },
    "evalscript": evalscript
}

print(f"Requesting Sentinel-1 VV data ({period})...")
print(f"Area bounds: {[west, south, east, north]}")
print(f"Date range: {start_date.date()} to {end_date.date()}")

response = requests.post(
    process_url,
    headers={
        "Authorization": "Bearer " + access_token,
        "Accept": "image/tiff"
    },
    json=request_body,
    timeout=300
)

print("HTTP status:", response.status_code)


if response.status_code != 200:
    print(response.text)
    sys.exit(1)

if len(response.content) < 100_000:
    print(
        "Error: Satellite response is unexpectedly small:",
        len(response.content),
        "bytes. Not saving it as valid imagery."
    )
    sys.exit(1)

os.makedirs("data/raw", exist_ok=True)

with open(output_file, "wb") as file:
    file.write(response.content)

try:
    with rasterio.open(output_file) as src:
        image = src.read(1, masked=True)
        valid_pixels = int(
            np.count_nonzero(
                np.isfinite(image.filled(np.nan))
            )
        )

    print("Saved:", output_file)
    print("Size:", len(response.content), "bytes")
    print("Valid pixels:", valid_pixels)

    if valid_pixels == 0:
        os.remove(output_file)
        print("Error: TIFF contains no valid pixels.")
        sys.exit(1)

except Exception as error:
    if os.path.exists(output_file):
        os.remove(output_file)
    print("Error: Downloaded file is not a valid readable TIFF:", error)
    sys.exit(1)

