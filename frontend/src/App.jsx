
import { useEffect, useState} from "react";
import "leaflet/dist/leaflet.css";
import "./App.css";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  LayersControl,
  useMap,
} from "react-leaflet";


const API = "http://localhost:8080/api/analysis";

function MapController({ position, zoom }) {
  const map = useMap();

  useEffect(() => {
    if (position) {
      map.flyTo(position, zoom, {
        duration: 1.5,
      });
    }
  }, [map, position, zoom]);

  return null;
}

function App() {
  const [stats, setStats] = useState(null);
  const [flood, setFlood] = useState(null);
  const [roads, setRoads] = useState(null);
  const [error, setError] = useState("");
  const [areaName, setAreaName] = useState("");
  const [floodDate, setFloodDate] = useState("");
const [analysisStatus, setAnalysisStatus] = useState("idle");
const [analysisMessage, setAnalysisMessage] = useState("");
const [mapPosition, setMapPosition] = useState([27.68, 85.32]);
const [mapZoom, setMapZoom] = useState(11);
const [locationStatus, setLocationStatus] = useState("");
const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/results`).then((r) => {
        if (!r.ok) throw new Error("Could not load analysis results");
        return r.json();
      }),
      fetch(`${API}/flood-mask`).then((r) => {
        if (!r.ok) throw new Error("Could not load flood map");
        return r.json();
      }),
      fetch(`${API}/affected-roads`).then((r) => {
        if (!r.ok) throw new Error("Could not load affected roads");
        return r.json();
      }),
    ])
      .then(([results, floodData, roadData]) => {
        setStats(results);
        setFlood(floodData);
        setRoads(roadData);
      })
      .catch((e) => setError(e.message + ". Check that Spring Boot is running."));
  }, []);

  const findLocation = async () => {
  if (!areaName.trim()) {
    setLocationStatus("Please enter a place name.");
    return;
  }

  try {
    setIsSearching(true);
    setLocationStatus("Finding location...");

    const url = new URL(
      "https://nominatim.openstreetmap.org/search"
    );

    url.searchParams.set("q", areaName.trim());
    url.searchParams.set("format", "jsonv2");
    url.searchParams.set("limit", "1");

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error("Location search service is unavailable.");
    }

    const results = await response.json();

    if (results.length === 0) {
      setLocationStatus("Location not found. Try a more specific place name.");
      return;
    }

    const latitude = Number(results[0].lat);
    const longitude = Number(results[0].lon);

    setMapPosition([latitude, longitude]);
    setMapZoom(13);
    setLocationStatus(
      `Found: ${results[0].display_name}\nCoordinates: ${latitude}, ${longitude}`
    );
  } catch (err) {
    setLocationStatus(err.message || "Could not resolve this location.");
  } finally {
    setIsSearching(false);
  }
};

const runAnalysis = async () => {
  if (!areaName.trim() || !floodDate) {
  setAnalysisMessage("Enter an area name and flood date.");
  return;
}

if (!/^\d{4}-\d{2}-\d{2}$/.test(floodDate) ||
    Number(floodDate.slice(0, 4)) < 2000) {
  setAnalysisMessage("Please select a valid flood date.");
  return;
}

  try {
    setError("");
    setAnalysisStatus("running");
    setAnalysisMessage("Resolving location and starting analysis...");

    const response = await fetch(`${API}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        areaName: areaName.trim(),
        floodDate
      })
    });

    const startData = await response.json();

    if (!response.ok) {
      throw new Error(startData.message || "Could not start analysis.");
    }

    let currentStatus = "running";

    while (currentStatus === "running") {
      await new Promise((resolve) => setTimeout(resolve, 3000));

      const statusResponse = await fetch(`${API}/status`);
      const statusData = await statusResponse.json();

      currentStatus = statusData.status;

      setAnalysisMessage(
        `${statusData.message || ""}\n${(statusData.log || "").slice(-1800)}`
      );
    }

    if (currentStatus !== "completed") {
      throw new Error("Analysis failed. Check the progress log above.");
    }

    const [resultsResponse, floodResponse, roadsResponse] =
      await Promise.all([
        fetch(`${API}/results`),
        fetch(`${API}/flood-mask`),
        fetch(`${API}/affected-roads`)
      ]);

    if (!resultsResponse.ok || !floodResponse.ok || !roadsResponse.ok) {
      throw new Error("Analysis finished, but some results could not be loaded.");
    }

    const [results, floodData, roadData] = await Promise.all([
      resultsResponse.json(),
      floodResponse.json(),
      roadsResponse.json()
    ]);

    setStats(results);
    setFlood(floodData);
    setRoads(roadData);
    setAnalysisStatus("completed");
    setAnalysisMessage("Analysis completed. Results and map refreshed.");
  }  catch (err) {
  setAnalysisStatus("failed");
  setAnalysisMessage((previous) =>
    `${previous}\n\nERROR: ${err.message || "Unknown error"}`
  );
  console.error("FloodRescue analysis failed:", err);
}

};




  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <div className="eyebrow">FLOOD RESPONSE INTELLIGENCE</div>
          <h1>FloodRescue</h1>
          <p>Satellite-based flood assessment</p>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

<section className="selection-panel">
  <h2>Analyze a flood event</h2>

  <label htmlFor="areaName">Location / area name</label>
  <input
    id="areaName"
    value={areaName}
    onChange={(e) => setAreaName(e.target.value)}
    placeholder="e.g. Kathmandu Valley, Nepal"
  />
  <button onClick={findLocation} disabled={isSearching}>
  {isSearching ? "Finding location..." : "Find Location on Map"}
</button>

{locationStatus && (
  <p style={{ whiteSpace: "pre-wrap" }}>{locationStatus}</p>
)}

  <label htmlFor="floodDate">Flood event date</label>
  <input
    id="floodDate"
    type="date"
    value={floodDate}
    max="2026-10-14"
    onChange={(e) => setFloodDate(e.target.value)}
  />

  
  <button
  onClick={runAnalysis}
  disabled={analysisStatus === "running"}
>
  {analysisStatus === "running" ? "Analyzing..." : "Run Flood Analysis"}
</button>

{analysisMessage && (
  <p style={{ whiteSpace: "pre-wrap" }}>{analysisMessage}</p>
)}

  


</section>


      <section className="stats">
        {[
          ["Estimated flood area", stats?.flooded_area_km2, "km²"],
          ["Potentially affected roads", stats?.potentially_affected_roads, "segments"],
          ["Potentially affected bridges", stats?.potentially_affected_bridges, "bridges"],
          ["Potentially affected buildings", stats?.potentially_affected_buildings, "buildings"],
          ["Potentially cut-off settlements", stats?.settlements_potentially_cut_off, "settlements"],
        ].map(([label, value, unit]) => (
          <article className="stat" key={label}>
            <span>{label}</span>
            <strong>{value ?? "—"}</strong>
            <small>{unit}</small>
          </article>
        ))}
      </section>

      <section className="map-section">
        <div className="map-heading">
          <div>
            <h2>Impact overview</h2>
            <p>Toggle map layers using the control on the map.</p>
          </div>
          <span className="live-label">PRELIMINARY ANALYSIS</span>
        </div>

        <MapContainer
        
        
          center={[27.68, 85.32]}
          zoom={11}
          scrollWheelZoom
          className="map"
        >
        <MapController
    position={mapPosition}
    zoom={mapZoom}
    />
    
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <LayersControl position="topright">
            {flood && (
              <LayersControl.Overlay checked name="Potential flood extent">
                <GeoJSON
                  data={flood}
                  style={{
                    color: "#dc2626",
                    weight: 1,
                    fillColor: "#ef4444",
                    fillOpacity: 0.35,
                  }}
                />
              </LayersControl.Overlay>
            )}
            {roads && (
              <LayersControl.Overlay checked name="Potentially affected roads">
                <GeoJSON
                  data={roads}
                  style={{
                    color: "#f59e0b",
                    weight: 2,
                    opacity: 0.85,
                  }}
                />
              </LayersControl.Overlay>
            )}
          </LayersControl>
        </MapContainer>
      </section>

      <footer>
        FloodRescue · Decision support, not confirmed damage reporting.
        Satellite estimates and network connectivity require field verification.
      </footer>
    </main>
  );
}

export default App;
