# DRISHTI completion changes

## Delivered
- One dark navy/slate command-center theme with explicit low, moderate, high and severe colors.
- India Explorer loads configured database regions and computed scores; failed feeds render as unavailable. It retains MapLibre 3D terrain, Esri/OSM/CARTO basemaps, Survey of India reference, region search, historical records, OSM response assets and the planning scenario.
- Overview adds current evidence, infrastructure/exposure, response review and a visible score explanation.
- Formula: `score = 100 × (0.40 × min(rainfall_7d_mm/300,1) + 0.25 × min(slope_deg/45,1) + 0.20 × (1-soil_retention) + 0.15 × min(history_count_2km/5,1)) + verified_sensor_adjustment`, clamped to 0–100. Bands: LOW <25, MODERATE <50, HIGH <75, SEVERE otherwise.
- Sensor transport remains the repository's working `POST /sensors/readings`, `GET /sensors/{node_id}/latest`, and `/ws/sensors`. Physical authenticated WebSocket traffic is `SENSOR · LIVE`; the bundled simulator sends `X-Source-Mode: SIMULATED`; absent data is `OFFLINE / AWAITING DATA`.
- Assistant restored with structured-context grounding, Anthropic/OpenAI provider configuration, and deterministic offline fallback.
- Evidence register lists Open-Meteo, OpenTopography, OpenStreetMap/Overpass, GSI Bhusanket, ESP32 and scenarios.
- Dockerfiles, `docker-compose.yml`, Render blueprint, Vercel SPA configuration and environment examples added.

## Assumptions and honest limitations
- MapLibre is retained for the primary India Explorer because it already supplies the required 3D terrain; the existing detailed regional map continues to use React-Leaflet.
- The supplied historical CSV contains one attributed event and no rainfall/slope/soil labels. A defensible train/test split or AUC is impossible. No ML probability is displayed and no metric was fabricated. `train_model.py` remains TODO until a sufficiently large attributed feature dataset is added.
- Government WMS layers remain disabled. No reliable endpoint/configuration was supplied; `ENABLE_GOVT_LAYERS=false` prevents them from blocking the demo.
- A complete zero-internet run requires cached map tiles. The application data and rule-based assistant degrade safely, but third-party raster tiles cannot appear offline unless tiles are packaged separately.
- Deployment manifests are ready. Public URLs require the owner's Render/Vercel account authentication and environment values.

## Run
`docker compose up --build`

Frontend: http://localhost:8080 · API: http://localhost:8000 · Swagger: http://localhost:8000/docs
