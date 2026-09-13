from fastapi import APIRouter

from app.schemas.scenarios import ScenarioRequest
from app.services.scenario_engine import simulate_scenario


router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios"],
)


@router.post("/simulate")
def simulate(
    payload: ScenarioRequest,
):
    result = simulate_scenario(
        rainfall_mm=payload.rainfall_mm,
        slope_deg=payload.slope_deg,
        soil_retention_score=payload.soil_retention_score,
        historical_count_2km=payload.historical_count_2km,
        sensor_adjustment=payload.sensor_adjustment,
    )

    return {
        "region_id": payload.region_id,
        "scenario": True,
        "label": "Scenario — exploratory, not a forecast",
        "risk_score": result.final_score,
        "base_score": result.base_score,
        "sensor_adjustment": result.sensor_adjustment,
        "risk_category": result.category,
        "factors": [
            {
                "name": factor.name,
                "raw_value": factor.raw_value,
                "normalized_value": factor.normalized_value,
                "weight": factor.weight,
                "contribution": factor.contribution,
            }
            for factor in result.factors
        ],
    }