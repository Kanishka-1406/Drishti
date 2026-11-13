# DRISHTI — See the Risk. Act Before.

**Explainable geospatial landslide-risk intelligence and scenario exploration for disaster preparedness.**

DRISHTI is an India-wide decision-support prototype that brings terrain context, environmental indicators, historical-event information and mapped response infrastructure into one geospatial workflow. It helps users inspect contributing factors and explore hypothetical changes in conditions.

> **Important:** DRISHTI is a research and demonstration prototype. It is not an operational early-warning system, a validated landslide-prediction model, or a replacement for official alerts and field assessment.

## What it does

- **India Explorer:** Explore nationwide geography, with emphasis on the Himalayan belt and Northeast India.
- **Evidence layers:** Inspect terrain, risk assessment, rainfall, recorded landslides, ground nodes and response assets where data is available.
- **Explainable assessment:** Review the contextual risk index and factor contributions instead of relying on an unexplained score.
- **What-if scenarios:** Adjust rainfall-intensification assumptions and inspect the resulting scenario assessment.
- **Regional context:** Explore historical-event markers and mapped hospitals, schools, police stations and fire stations.
- **Hardware proof of concept:** Demonstrate the physical terrain-monitoring direction using a microcontroller, sensor circuitry and display.
- **DRISHTI Assistant:** Ask questions about dashboard indicators, scores and evidence layers.

## Assessment approach

The current prototype uses a transparent factor-weight configuration:

| Factor | Weight |
|---|---:|
| Rainfall | 40% |
| Slope | 25% |
| Soil | 20% |
| Historical context | 15% |

These are prototype configuration weights, not universally calibrated scientific coefficients. The displayed index is a contextual decision-support indicator, **not a probability of a landslide**. If rainfall has no stored observation timestamp, its 40% weight is excluded and the remaining available factor weights are normalized to 100%; missing rainfall is never interpreted as 0 mm.

## Data integrity

The interface is designed to distinguish source types and availability:

| Label | Meaning |
|---|---|
| LIVE / EDGE SENSOR | Reading received from a connected physical sensor |
| NRT / SATELLITE | Near-real-time satellite or environmental data, when successfully retrieved |
| GOVT VERIFIED | Record checked against an authoritative government source |
| MODEL INFERENCE | Output from implemented assessment logic or a model |
| STATIC TERRAIN | Static or externally sourced terrain context |
| SIMULATED | Demonstration values or hypothetical scenario inputs |
| UNAVAILABLE | No usable value returned by the source |

### Current limitations

- The current assessment is deterministic and explainable; it is **not a trained India-wide landslide ML model**.
- The prototype has not been validated for operational prediction or emergency-response decisions.
- External feeds can be unavailable. Missing values should remain unavailable rather than being presented as live observations.
- The physical hardware shown is a prototype; continuous field deployment or sensor connectivity should not be assumed.
- Historical-event and infrastructure coverage depends on the quality and geographic coverage of source datasets.

## Technology

| Layer | Stack / components |
|---|---|
| Frontend | React, Vite, JavaScript |
| Mapping | Leaflet, OpenStreetMap-based layers |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Terrain context | Digital elevation / terrain data services, including OpenTopography where available |
| Environmental context | Open-Meteo, subject to source availability |
| Exposure context | OpenStreetMap response-asset features |
| Hardware | Microcontroller-based sensor prototype and display module |

## Run locally (Windows)

### Prerequisites

- Node.js and npm
- Python (use the version supported by the backend dependencies)
- PostgreSQL, if running the database-backed backend locally

### Quick start

Open PowerShell in the repository root and run:

```powershell
.\scripts\run_dev.ps1
```

Two terminal windows will open. Keep both running, then visit:

- Frontend: http://127.0.0.1:5173
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

If the local virtual environment and dependencies are not already present, install the backend dependencies using the repository's backend setup files before launching.

### Sensor demo

In another PowerShell window:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\simulate_sensor.py
```

This runs the sensor simulator; it should not be described as a live physical sensor feed.

### Frontend only

```powershell
cd frontend
npm install
npm run dev
```

### Optional Docker route

After installing Docker Desktop with WSL 2 support:

```powershell
docker compose up --build
```

Docker URLs are frontend http://localhost:8080, API http://localhost:8000, and Swagger http://localhost:8000/docs.

## Deployment

- Push the repository to GitHub.
- Create a Render Blueprint using `render.yaml`.
- Deploy `frontend/` on Vercel as a Vite project.
- Set `VITE_API_URL` to the Render backend URL.
- Set backend `CORS_ORIGINS` to the deployed frontend URL.

Never commit API keys, database passwords, or other secrets.

## Intended use

DRISHTI is intended for exploration and human review by disaster-management teams, local administrations, researchers and preparedness groups. It can help users examine regional context and mapped exposure, but it does not replace expert assessment, field verification, official warnings or established emergency protocols.

## Roadmap

- [ ] Improve coverage and provenance of authoritative landslide inventories.
- [ ] Expand reliable terrain and environmental data availability.
- [ ] Train and validate a regionally appropriate landslide susceptibility model.
- [ ] Connect and test physical ground sensors with authenticated data ingestion.
- [ ] Improve infrastructure completeness and evacuation-context analysis.
- [ ] Add systematic model evaluation, uncertainty communication and field validation.

---

**DRISHTI — See the Risk. Act Before.**


## Regional data ingestion

The ingestion scripts now accept a region slug or an explicit nationwide run. Run them from the backend directory with the backend virtual environment active and the required environment variables configured.

### Rainfall (Open-Meteo)

```powershell
python -m app.ingestion.fetch_rainfall --region darjeeling
python -m app.ingestion.fetch_rainfall --all
```

### Terrain reference points (OpenTopography)

```powershell
python -m app.ingestion.fetch_terrain --region darjeeling
python -m app.ingestion.fetch_terrain --all
```

The nationwide commands make external requests for every configured region. Terrain ingestion uses up to five point-elevation requests per region and stores a regional reference-point slope estimate; it is not a substitute for a full-resolution DEM-derived slope raster. Soil retention is intentionally left unset until a sourced soil dataset or documented regional baseline is loaded. Regions without complete terrain and soil inputs should remain unavailable for risk assessment rather than receiving invented values.

The default (no-argument) behavior remains Darjeeling-only for backward compatibility. Use `--all` deliberately and observe provider rate limits and API-key quotas.
