from sqlalchemy import text

from app.database import engine
from app.services.history_service import get_nearby_history_count
from app.services.rainfall_service import get_rainfall_summary
from app.services.risk_engine import RiskInput, compute_risk
from app.services.anomaly_engine import get_region_sensor_state
from app.services.sensor_fusion import (
    get_region_soil_saturation,
    modulate_soil_retention,
)


def get_reference_location(region_id: int):
    """Return the best available terrain reference point for a region.

    Prefer the legacy Darjeeling reference-point label when it exists so the
    existing demonstration database remains compatible. New regions can use
    any named or unnamed location with complete terrain inputs.
    """
    query = text("""
        SELECT
            l.id,
            l.name,
            l.slope_deg,
            l.soil_retention_score
        FROM locations AS l
        JOIN regions AS r ON r.id = l.region_id
        WHERE l.region_id = :region_id
          AND l.slope_deg IS NOT NULL
          AND l.soil_retention_score IS NOT NULL
        ORDER BY
            CASE WHEN l.name = 'Darjeeling Reference Point' THEN 0 ELSE 1 END,
            l.created_at DESC NULLS LAST,
            l.id DESC
        LIMIT 1
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"region_id": region_id},
        ).mappings().first()

    if not row:
        raise RuntimeError(
            f"No terrain reference point with slope and soil data is available for region_id={region_id}. "
            "Import terrain data for this region before requesting a risk assessment."
        )

    return row


def calculate_region_risk(region_id: int):
    rainfall = get_rainfall_summary(region_id)
    location = get_reference_location(region_id)
    history_count = get_nearby_history_count(
        location_id=location["id"],
        radius_m=2000,
    )

    sensor_state = get_region_sensor_state(region_id)
    sensor_adjustment = sensor_state.sensor_adjustment if sensor_state else 0.0

    saturation = get_region_soil_saturation(region_id)
    baseline_retention = float(location["soil_retention_score"])
    effective_retention = modulate_soil_retention(
        baseline_retention,
        saturation.index if saturation else None,
    )

    risk_input = RiskInput(
        rainfall_7d_mm=rainfall["rainfall_7d_mm"],
        slope_deg=float(location["slope_deg"]),
        soil_retention_score=effective_retention,
        historical_count_2km=history_count,
        sensor_adjustment=sensor_adjustment,
    )
    result = compute_risk(risk_input)

    return {
        "region_id": region_id,
        "location_id": location["id"],
        "reference_location": location["name"],
        "risk_score": result.final_score,
        "base_score": result.base_score,
        "sensor_adjustment": result.sensor_adjustment,
        "risk_category": result.category,
        "assessment_status": (
            "PARTIAL_DATA"
            if not rainfall.get("fetched_at")
            else "ASSESSED"
        ),
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
        "data": {
            "rainfall": rainfall,
            "slope_deg": float(location["slope_deg"]),
            "soil_retention_score": effective_retention,
            "soil_retention_baseline": baseline_retention,
            "soil_saturation": (
                {
                    "index": saturation.index,
                    "soil_moisture_percent": saturation.soil_moisture_percent,
                    "rain_wetness_percent": saturation.rain_wetness_percent,
                    "sample_count": saturation.sample_count,
                    "latest_recorded_at": saturation.latest_recorded_at.isoformat(),
                    "source": "LIVE HARDWARE",
                    "window_minutes": 30,
                }
                if saturation
                else {
                    "index": None,
                    "source": "unavailable",
                    "reason": "No physical sensor readings received in the last 30 minutes; using the stored soil-retention baseline.",
                }
            ),
            "historical_count_2km": history_count,
        },
        "sensor": {
            "node_id": sensor_state.node_id if sensor_state else None,
            "state": sensor_state.state if sensor_state else "NO_NODE",
            "latest_tilt": sensor_state.latest_tilt if sensor_state else None,
            "consecutive_high_readings": (
                sensor_state.consecutive_high_readings if sensor_state else 0
            ),
            "adjustment": sensor_adjustment,
            "explanation": (
                sensor_state.explanation
                if sensor_state
                else "No active ground sensor node is linked to this region."
            ),
        },
    }
