from app.services.risk_engine import (
    RiskInput,
    compute_risk,
)


def simulate_scenario(
    rainfall_mm: float,
    slope_deg: float,
    soil_retention_score: float,
    historical_count_2km: int,
    sensor_adjustment: float = 0.0,
):
    risk_input = RiskInput(
        rainfall_7d_mm=rainfall_mm,
        slope_deg=slope_deg,
        soil_retention_score=soil_retention_score,
        historical_count_2km=historical_count_2km,
        sensor_adjustment=sensor_adjustment,
    )

    return compute_risk(
        risk_input
    )