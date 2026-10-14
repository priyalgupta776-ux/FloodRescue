import os
import sys
import subprocess
from datetime import date

import numpy as np
import rasterio


if len(sys.argv) != 7:
    print(
        "Usage: python processing/run_analysis.py "
        "<area_name> <flood_date> <west> <south> <east> <north>"
    )
    sys.exit(1)

area_name = sys.argv[1]
flood_date = sys.argv[2]

try:
    event_date = date.fromisoformat(flood_date)
    west, south, east, north = map(float, sys.argv[3:7])
except ValueError:
    print("Error: Invalid date or bounding-box coordinates.")
    sys.exit(1)

if event_date.year < 2000 or event_date > date.today():
    print(f"Error: Invalid flood event date: {flood_date}")
    print("Use a date between 2000 and today.")
    sys.exit(1)

if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
    print("Error: Invalid bounding box.")
    sys.exit(1)

if east - west > 0.5 or north - south > 0.5:
    print("Error: Selected area is too large. Choose a smaller area.")
    sys.exit(1)

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)


def run_script(script, *args):
    command = [
        sys.executable,
        f"processing/{script}",
        *map(str, args)
    ]

    print(f"\nRunning: {' '.join(command)}", flush=True)

    result = subprocess.run(
        command,
        text=True,
        capture_output=True
    )

    if result.stdout:
        print(result.stdout, flush=True)

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, flush=True)

        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr
        )

    return result


def validate_satellite_image(path):
    if not os.path.exists(path):
        raise RuntimeError(f"Satellite image is missing: {path}")

    with rasterio.open(path) as src:
        image = src.read(1, masked=True)
        valid_pixels = int(
            np.count_nonzero(~np.ma.getmaskarray(image))
        )
        valid_pixels = min(
            valid_pixels,
            int(np.count_nonzero(np.isfinite(image.filled(np.nan))))
        )

    print(f"{path}: {valid_pixels} valid pixels", flush=True)

    if valid_pixels == 0:
        raise RuntimeError(
            f"{path} contains no valid pixels. "
            "Stopping to avoid producing misleading flood results."
        )


try:
    print("\n=== FloodRescue Analysis ===", flush=True)
    print(f"Area: {area_name}", flush=True)
    print(f"Event date: {flood_date}", flush=True)
    print(
        f"Bounds: {west}, {south}, {east}, {north}",
        flush=True
    )

    # 1. Download before- and after-event satellite images.
    run_script(
        "download_sentinel.py",
        west, south, east, north, flood_date, "before"
    )
    run_script(
        "download_sentinel.py",
        west, south, east, north, flood_date, "after"
    )

    # 2. Validate both satellite images.
    validate_satellite_image("data/raw/before_vv.tif")
    validate_satellite_image("data/raw/after_vv.tif")

    # 3. Detect potential flooding.
    run_script("flood_detection.py")

    # 4. Download infrastructure for the selected area.

    # 4. Download infrastructure for the selected area.
    osm_steps = [
        (
            "osm_analysis.py",
            (west, south, east, north),
            [
                "data/processed/roads.geojson",
                "data/processed/bridges.geojson",
                "data/processed/buildings.geojson",
                "data/processed/road_network.graphml",
            ],
        ),
        (
            "osm_places.py",
            (west, south, east, north),
            ["data/processed/settlements.geojson"],
        ),
        (
            "osm_hospitals.py",
            (west, south, east, north),
            ["data/processed/hospitals.geojson"],
        ),
    ]

    for script, args, required_files in osm_steps:
        try:
            run_script(script, *args)
        except subprocess.CalledProcessError as error:
            missing = [
                path for path in required_files
                if not os.path.exists(path) or os.path.getsize(path) == 0
            ]

            if missing:
                raise RuntimeError(
                    f"{script} failed, and these required files are missing: {missing}"
                ) from error

            print(
                f"WARNING: {script} failed. Reusing existing infrastructure files. "
                "These files may be outdated or for a different area.",
                flush=True,
            )

        missing = [
            path for path in required_files
            if not os.path.exists(path) or os.path.getsize(path) == 0
        ]

        if missing:
            raise RuntimeError(
                f"{script} did not create required files: {missing}"
            )


    # 5. Calculate affected infrastructure.
    run_script("affected_roads.py")
    run_script("affected_bridges.py")
    run_script("affected_buildings.py")

    # 6. Generate flood extent and connectivity results.
    run_script("create_flood_geojson.py")
    run_script("connectivity.py")

    # 7. Generate the final report.
    run_script("create_results.py", area_name, flood_date)

    print("\nAnalysis completed successfully.", flush=True)

except (
        subprocess.CalledProcessError,
        RuntimeError,
        FileNotFoundError
) as error:
    print(f"\nAnalysis stopped: {error}", flush=True)
    sys.exit(1)
