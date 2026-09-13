from sqlalchemy import text

from app.database import engine
from app.services.history_service import get_nearby_history_count
from app.services.rainfall_service import get_rainfall_summary
from app.services.risk_engine import RiskInput, compute_risk
from app.services.anomaly_engine import (get_region_sensor_state,)
from app.services.sensor_fusion import get_region_soil_saturation, modulate_soil_retention


def get_reference_location(region_id: int):
    query = text("""
        SELECT
            id,
            slope_deg,
            soil_retention_score
        FROM locations
        WHERE region_id = :region_id
          AND name = 'Darjeeling Reference Point'
        LIMIT 1
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"region_id": region_id},
        ).mappings().first()

    if not row:
        raise RuntimeError(
            f"No reference location found for region_id={region_id}"
        )

    if row["slope_deg"] is None:
        raise RuntimeError(
            "Reference location has no slope_deg"
        )

    if row["soil_retention_score"] is None:
        raise RuntimeError(
            "Reference location has no soil_retention_score"
        )

    return row


def calculate_region_risk(
    region_id: int,
    sensor_adjustment: float = 0.0,
):
    rainfall = get_rainfall_summary(
        region_id
    )

    location = get_reference_location(
        region_id
    )

    history_count = get_nearby_history_count(
        location_id=location["id"],
        radius_m=2000,
    )

    # Get live sensor/anomaly state for this region
    sensor_state = (
        get_region_sensor_state(
            region_id
        )
    )

    sensor_adjustment = (
        sensor_state.sensor_adjustment
        if sensor_state
        else 0.0
    )

    saturation = get_region_soil_saturation(region_id)
    baseline_retention = float(location["soil_retention_score"])
    effective_retention = modulate_soil_retention(
        baseline_retention,
        saturation.index if saturation else None,
    )

    # Build risk input using the existing deterministic engine
    risk_input = RiskInput(
        rainfall_7d_mm=rainfall["rainfall_7d_mm"],
        slope_deg=float(
            location["slope_deg"]
        ),
        soil_retention_score=effective_retention,
        historical_count_2km=history_count,
        sensor_adjustment=sensor_adjustment,
    )

    result = compute_risk(
        risk_input
    )

    return {
        "region_id": region_id,
        "location_id": location["id"],
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

        "data": {
            "rainfall": rainfall,
            "slope_deg": float(
                location["slope_deg"]
            ),
            "soil_retention_score": effective_retention,
            "soil_retention_baseline": baseline_retention,
            "soil_saturation": ({
                "index": saturation.index,
                "soil_moisture_percent": saturation.soil_moisture_percent,
                "rain_wetness_percent": saturation.rain_wetness_percent,
                "sample_count": saturation.sample_count,
                "latest_recorded_at": saturation.latest_recorded_at.isoformat(),
                "source": "LIVE HARDWARE",
                "window_minutes": 30,
            } if saturation else {
                "index": None,
                "source": "unavailable",
                "reason": "No physical sensor readings received in the last 30 minutes; using the stored soil-retention baseline.",
            }),
            "historical_count_2km": history_count,
        },

        "sensor": {
            "node_id": (
                sensor_state.node_id
                if sensor_state
                else None
            ),
            "state": (
                sensor_state.state
                if sensor_state
                else "NO_NODE"
            ),
            "latest_tilt": (
                sensor_state.latest_tilt
                if sensor_state
                else None
            ),
            "consecutive_high_readings": (
                sensor_state.consecutive_high_readings
                if sensor_state
                else 0
            ),
            "adjustment": sensor_adjustment,
            "explanation": (
                sensor_state.explanation
                if sensor_state
                else (
                    "No active ground "
                    "sensor node is linked "
                    "to this region."
                )
            ),
        },
    }
