# DRISHTI Terrain Intelligence Upgrade

This build upgrades the India Explorer into a MapLibre GL based 3D terrain workspace with:

- pitch/rotate/zoom 3D terrain using a raster DEM;
- India-wide hotspot navigation;
- explainable `Why this risk?` cards;
- a deterministic what-if rainfall scenario control;
- provenance-first Government of India boundary handling;
- a Survey of India 2026 Political Map reference link;
- layer controls, search, quick insights, fallback mode, and a calmer dark teal interface.

## Important boundary integrity rule

The interactive OSM basemap is **not** labelled as the Government of India boundary. The UI links the authoritative Survey of India Political Map as the official reference. To render authoritative Government of India vectors directly, import a Survey of India Administrative Boundary Database / Political Map shapefile into the backend and expose it as GeoJSON. Do not silently substitute third-party country boundaries.

## Run

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

MapLibre GL is loaded from a CDN in `frontend/index.html` to avoid adding a heavy local dependency during the hackathon. Internet is therefore required for the interactive basemap/DEM; the rest of the app still falls back cleanly if the backend is offline.
