# DRISHTI — See the Risk. Act Before.

## Run now without Docker

PostgreSQL is already installed and running on this computer. Open PowerShell in this folder and run:

```powershell
.\scripts\run_dev.ps1
```

Two terminal windows will open. Keep both open, then visit:
- Frontend: http://127.0.0.1:5173
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

The backend virtual environment and dependencies have already been installed in `backend/.venv`.

## Sensor demo

In another PowerShell window:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\simulate_sensor.py
```

## Optional Docker route

After installing Docker Desktop with WSL 2 support:

```powershell
docker compose up --build
```

Docker URLs are frontend http://localhost:8080, API http://localhost:8000, and Swagger http://localhost:8000/docs.

## Deploy

Push this directory to GitHub. Create a Render Blueprint using root `render.yaml`. Deploy `frontend/` on Vercel as a Vite project, set `VITE_API_URL` to the Render backend URL, and set backend `CORS_ORIGINS` to the Vercel frontend URL.
