from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_database
from app.services.rainfall_service import get_rainfall_summary
from app.services.risk_service import calculate_region_risk
from app.routers.regions import router as regions_router
from app.routers.risk import router as risk_router
from app.routers.scenarios import router as scenarios_router
from app.routers.historical import router as historical_router
from app.routers.infrastructure import router as infrastructure_router
from app.routers.sensors import router as sensors_router
from app.routers.ws import (router as ws_router,)
from app.routers.map_experience import router as map_experience_router
from app.routers.assistant import router as assistant_router


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Backend API for DRISHTI — explainable landslide "
        "risk decision-support and scenario exploration."
    ),
)

app.include_router(regions_router)
app.include_router(risk_router)
app.include_router(scenarios_router)
app.include_router(historical_router)
app.include_router(infrastructure_router)
app.include_router(sensors_router)
app.include_router(ws_router)
app.include_router(map_experience_router)
app.include_router(assistant_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "DRISHTI API",
        "status": "running",
        "message": "See the Risk. Act Before.",
    }


@app.get("/health")
def health():
    try:
        check_database()

        return {
            "status": "healthy",
            "api": "online",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "degraded",
            "api": "online",
            "database": "unavailable",
        }
