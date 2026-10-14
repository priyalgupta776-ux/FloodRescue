# FloodRescue 
### Satellite-Based Flood Mapping and Emergency Accessibility Analysis

FloodRescue is a disaster-response prototype that combines Sentinel-1 radar imagery, OpenStreetMap infrastructure data, and road-network analysis to identify potential flood extent, investigate infrastructure exposure, and flag settlements that may lose connectivity to hospitals.

## 1. Problem Statement

During floods, responders need to understand not only where flooding may have occurred, but also which roads, bridges, buildings, and communities could be affected. FloodRescue explores how satellite imagery and geographic data can support preliminary impact assessment.

## 2. Key Features

- **Flood extent detection:** Derives a candidate flood mask from pre-event and post-event Sentinel-1 radar imagery.
- **Infrastructure exposure analysis:** Identifies roads, bridges, and buildings that intersect the candidate flood extent.
- **Accessibility analysis:** Models changes in settlement-to-hospital road connectivity when potentially affected road segments are removed from the network.
- **Geospatial visualization:** Produces GeoJSON and JSON outputs for viewing and reporting.
- **Reference comparison:** Supports visual comparison of the generated flood extent with an official reference delineation.

These outputs indicate potential exposure, not confirmed damage or guaranteed inaccessibility.

## 3. Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Java, Spring Boot, Maven |
| Geospatial processing | Python, Rasterio, GeoPandas, Shapely |
| Road-network analysis | NetworkX, OSMnx |
| Satellite imagery | Sentinel-1 SAR |
| Geographic data | OpenStreetMap |
| Data formats | GeoTIFF, GeoJSON, JSON |

## 4. Project Architecture

```text
FloodRescue/
│
├── src/
│   └── main/
│       ├── java/com/FloodRescue/FloodRescue/
│       │   ├── AnalysisController.java
│       │   └── FloodRescueApplication.java
│       └── resources/
│           └── application.properties
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── processing/
│   ├── download_sentinel.py
│   ├── flood_detection.py
│   ├── calculate_area.py
│   ├── create_flood_geojson.py
│   ├── osm_analysis.py
│   ├── osm_roads.py
│   ├── osm_buildings.py
│   ├── osm_places.py
│   ├── osm_hospitals.py
│   ├── affected_roads.py
│   ├── affected_bridges.py
│   ├── affected_buildings.py
│   ├── connectivity.py
│   ├── create_results.py
│   ├── run_analysis.py
│   └── test_connectivity.py
│
├── data/
│   └── outputs/
│       ├── flood_extent.geojson
│       ├── potentially_cut_off_settlements.geojson
│       └── results.json
│
├── .mvn/
├── mvnw
├── mvnw.cmd
├── pom.xml
├── .gitignore
└── README.md
```

**Folder responsibilities**

- `frontend/` — React user interface and map dashboard.
- `src/` — Spring Boot application and analysis controller.
- `processing/` — Python scripts for satellite processing, infrastructure analysis, and connectivity modelling.
- `data/outputs/` — Generated geospatial and analysis results.
- `data/raw/` and `data/processed/` — Local input imagery and intermediate processing products; these are not necessarily committed to GitHub.
- `pom.xml` — Java and Spring Boot build configuration.
- `frontend/package.json` — Frontend dependencies and available npm scripts.

## 5. Prerequisites

Install the following before running the project:

- Java version compatible with the project's Maven configuration.
- Python 3.
- Node.js and npm.
- Git.
- Internet access for data downloads, if running the complete processing workflow.

The Python workflow uses libraries such as Rasterio, GeoPandas, Shapely, NetworkX, and OSMnx. Check the imports in the scripts and install the required compatible versions.

## 6. Clone the Repository

```bash
git clone https://github.com/priyalgupta776-ux/FloodRescue.git
cd FloodRescue
```

## 7. Run the Application

### A. Start the Spring Boot backend

From the project root:

```bash
./mvnw spring-boot:run
```

On Windows, use:

```bat
mvnw.cmd spring-boot:run
```

The application uses the configuration in `src/main/resources/application.properties`. Check that file for the configured port, required environment variables, and any data paths.

### B. Start the React frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

If the frontend calls the backend, verify that its API URL and the backend's port match your configuration.

## 8. Run the Geospatial Processing Workflow

Run these commands from the project root. First, inspect `processing/run_analysis.py` to confirm whether it orchestrates the workflow or requires particular arguments.

### A. Install Python dependencies

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required libraries:

```bash
python -m pip install rasterio geopandas shapely networkx osmnx
```

Additional libraries may be required depending on the imports in the scripts.

### B. Download satellite imagery

```bash
python processing/download_sentinel.py
```

Configure any required data-provider credentials and study-area parameters as documented by the script. Never commit credentials to GitHub.

### C. Generate the candidate flood mask

```bash
python processing/flood_detection.py
python processing/calculate_area.py
python processing/create_flood_geojson.py
```

These stages process the imagery, calculate an estimated flooded area, and create a geospatial flood-extent output. Verify the input and output paths in each script before running.

### D. Analyze infrastructure and accessibility

The repository includes scripts for roads, bridges, buildings, settlements, hospitals, and connectivity analysis. Review `processing/run_analysis.py` and run the workflow in its intended order so every stage has the required input files.

For example, individual stages may include:

```bash
python processing/affected_roads.py
python processing/affected_bridges.py
python processing/affected_buildings.py
python processing/connectivity.py
python processing/create_results.py
```

**Note:** These are individual script entry points, not a guarantee that every script can run independently. Some require previously generated files, downloaded data, or configuration. Follow the actual dependencies in the code.

## 9. Generated Outputs

| File | Purpose |
|---|---|
| `data/outputs/flood_extent.geojson` | Candidate flood extent for map visualization |
| `data/outputs/potentially_cut_off_settlements.geojson` | Settlements flagged by the connectivity analysis |
| `data/outputs/results.json` | Generated analysis results |

The pipeline may also generate a raster flood mask and intermediate infrastructure layers locally. Outputs depend on the study area, event date, input data, and processing settings.

## 10. Flood Map Comparison

FloodRescue's candidate flood extent can be compared with the official Copernicus Emergency Management Service (EMS) EMSR927 reference delineation, provided both datasets represent a matching event and geographic area.
FloodRescue — local study area
We focused on a small area around Syapru Besi, Rasuwa, Nepal, using a bounding box approximately 4 km × 4.4 km.
This means we analysed a specific local region rather than the entire country.

The official EMSR927 reference layer contains flood delineations over a much broader disaster-affected region.
It may include areas far outside our selected study area.

<!-- After uploading the screenshot to GitHub, replace the path below. -->
1.FloodRescue Map of Syapru Besi,rasuwa,Nepal
<img width="1470" height="884" alt="Screenshot 2026-10-14 at 10 57 02 PM" src="https://github.com/user-attachments/assets/7e2d4923-f6c9-48ff-a66c-e418e6a42e44" />
2.EMSR927 Map of Nepal
<img width="1470" height="883" alt="Screenshot 2026-10-14 at 10 56 21 PM" src="https://github.com/user-attachments/assets/42aee0fc-9906-4e47-abcd-491ac3d86b72" />
3. Comparison
<img width="1470" height="874" alt="Screenshot 2026-10-14 at 10 54 59 PM" src="https://github.com/user-attachments/assets/38d89fb3-d743-4ccf-ab25-54a2a804814b" />

*The visual overlay helps inspect agreement and disagreement. It is not, by itself, a quantitative accuracy measurement.*

A rigorous comparison should use a common area of interest, compatible coordinate systems and spatial resolutions, and a documented method. IoU, precision, recall, and area difference should only be reported after they have been calculated from aligned data.

## 11. Limitations

- Sentinel-1 acquisitions are periodic rather than continuous real-time observations.
- Radar-based change detection may produce false positives due to surface changes, terrain, and other conditions.
- OpenStreetMap completeness varies by region.
- A road intersecting a candidate flood extent is not necessarily damaged or impassable.
- Connectivity analysis estimates the effect of removing selected road segments; it does not verify physical road conditions.
- Reference maps may differ in acquisition time, resolution, and mapping methodology.
- Results require further validation before use in operational decisions.

## 12. Data Sources and Attribution

- **Copernicus Sentinel-1:** Cite the specific satellite products, acquisition dates, and access service used.
- **OpenStreetMap contributors:** Geographic infrastructure data. © OpenStreetMap contributors; data is available under the Open Database License (ODbL).
- **Copernicus Emergency Management Service:** Cite the exact EMSR927 reference product and its URL for the case-study comparison.



