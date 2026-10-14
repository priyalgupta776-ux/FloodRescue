
package com.FloodRescue.FloodRescue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.LocalDate;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@CrossOrigin(origins = "http://localhost:5173")
@RestController
@RequestMapping("/api/analysis")
public class AnalysisController {

    private final ObjectMapper mapper = new ObjectMapper();
    private volatile boolean running = false;
    private volatile String status = "idle";
    private volatile String message = "Enter an area and flood date.";
    private volatile String lastOutput = "";

    @PostMapping("/run")
    public synchronized ResponseEntity<?> runAnalysis(
            @RequestBody AnalysisRequest request) {

        if (running) {
            return ResponseEntity.status(409)
                    .body(Map.of("message", "An analysis is already running."));
        }

        if (request.areaName() == null || request.areaName().isBlank()
                || request.floodDate() == null) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Enter an area name and flood date."));
        }


        final LocalDate date;

        try {
            date = LocalDate.parse(request.floodDate());

            if (date.getYear() < 2000 || date.isAfter(LocalDate.now())) {
                return ResponseEntity.badRequest()
                        .body(Map.of(
                                "message",
                                "Enter a flood date between 2000 and today."
                        ));
            }
        } catch (Exception e) {
            return ResponseEntity.badRequest()
                    .body(Map.of(
                            "message",
                            "Enter the date in YYYY-MM-DD format."
                    ));
        }

        final String validatedFloodDate = date.toString();


        final double[] bounds;

        try {
            bounds = getBounds(request.areaName().trim());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "message", "Could not find that area. Try a more specific place name.",
                    "details", e.getMessage() == null ? "Location lookup failed." : e.getMessage()
            ));
        }

        running = true;
        status = "running";
        message = "Location found. Starting satellite and infrastructure analysis.";
        lastOutput = "Resolved area: " + request.areaName()
                + "\nBounds (west, south, east, north): "
                + bounds[0] + ", " + bounds[1] + ", "
                + bounds[2] + ", " + bounds[3] + "\n";

        CompletableFuture.runAsync(() -> {
            try {
                File root = new File(System.getProperty("user.dir"));

                ProcessBuilder builder = new ProcessBuilder(
                        "/opt/anaconda3/bin/python",
                        "processing/run_analysis.py",
                        request.areaName().trim(),
                        validatedFloodDate,
                        String.valueOf(bounds[0]),
                        String.valueOf(bounds[1]),
                        String.valueOf(bounds[2]),
                        String.valueOf(bounds[3])
                );

                builder.directory(root);
                builder.redirectErrorStream(true);

                Process process = builder.start();
                StringBuilder output = new StringBuilder(lastOutput);

                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        output.append(line).append("\n");
                        lastOutput = output.toString();
                    }
                }

                int exitCode = process.waitFor();

                if (exitCode == 0) {
                    status = "completed";
                    message = "Analysis completed successfully.";
                } else {
                    status = "failed";
                    message = "Analysis failed. Check the log for the exact error.";
                }

                lastOutput = output.toString();

            } catch (Exception e) {
                status = "failed";
                message = "Could not run Python: "
                        + (e.getMessage() == null ? "Unknown error" : e.getMessage());
            } finally {
                running = false;
            }
        });

        return ResponseEntity.accepted().body(Map.of(
                "status", "running",
                "message", "Location resolved. Analysis started."
        ));
    }

    private double[] getBounds(String areaName) throws Exception {
        String query = URLEncoder.encode(areaName, StandardCharsets.UTF_8);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(
                        "https://nominatim.openstreetmap.org/search?q="
                                + query + "&format=jsonv2&limit=1"))
                .header("User-Agent", "FloodRescue-Hackathon/1.0")
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpClient client = HttpClient.newHttpClient();

        HttpResponse<String> response = client.send(
                request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new Exception("Location service returned HTTP "
                    + response.statusCode());
        }

        JsonNode results = mapper.readTree(response.body());

        if (!results.isArray() || results.isEmpty()) {
            throw new Exception("No matching location was found.");
        }

        JsonNode place = results.get(0);
        JsonNode box = place.path("boundingbox");

        if (!box.isArray() || box.size() < 4) {
            throw new Exception("The location has no usable bounding box.");
        }

        // Nominatim order: south, north, west, east.
        double south = Double.parseDouble(box.get(0).asText());
        double north = Double.parseDouble(box.get(1).asText());
        double west = Double.parseDouble(box.get(2).asText());
        double east = Double.parseDouble(box.get(3).asText());

        // Keep the analysis extent within the existing pipeline's size limit.
        double centerLat = (south + north) / 2.0;
        double centerLon = (west + east) / 2.0;
        double height = Math.min(north - south, 0.4);
        double width = Math.min(east - west, 0.4);

        south = centerLat - height / 2.0;
        north = centerLat + height / 2.0;
        west = centerLon - width / 2.0;
        east = centerLon + width / 2.0;

        if (!(west < east && south < north)) {
            throw new Exception("Invalid coordinates returned for this area.");
        }

        return new double[]{west, south, east, north};
    }

    @GetMapping("/status")
    public Map<String, String> getStatus() {
        return Map.of(
                "status", status,
                "message", message,
                "log", lastOutput
        );
    }


    @GetMapping("/results")
    public ResponseEntity<String> getResults() throws Exception {
        File file = new File("data/outputs/results.json");

        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }

        String json = java.nio.file.Files.readString(file.toPath());
        return ResponseEntity.ok()
                .header("Content-Type", "application/json")
                .body(json);
    }


    @GetMapping(value = "/flood-mask",
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> getFloodMask() throws Exception {
        File file = new File("data/outputs/flood_extent.geojson");
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Files.readString(file.toPath()));
    }

    @GetMapping(value = "/affected-roads",
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> getAffectedRoads() throws Exception {
        File file = new File("data/processed/affected_roads.geojson");
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Files.readString(file.toPath()));
    }

    public record AnalysisRequest(String areaName, String floodDate) {}
}
