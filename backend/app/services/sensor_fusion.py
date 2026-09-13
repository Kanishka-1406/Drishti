"""Fuse recent physical soil and rain readings into one saturation signal."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import engine

SOIL_WEIGHT = 0.70
RAIN_WEIGHT = 0.30
WINDOW_MINUTES = 30
MAX_SAMPLES = 24


@dataclass(frozen=True)
class SoilSaturation:
    index: float
    soil_moisture_percent: float
    rain_wetness_percent: float
    sample_count: int
    latest_recorded_at: datetime
    source_mode: str = "LIVE"


def normalize_percent(value: float) -> float:
    """Normalize firmware percentage values to 0..1."""
    return max(0.0, min(float(value), 100.0)) / 100.0


def compute_soil_saturation_index(soil_values: list[float], rain_values: list[float]) -> float | None:
    if not soil_values and not rain_values:
        return None
    soil = sum(normalize_percent(value) for value in soil_values) / len(soil_values) if soil_values else 0.0
    rain = sum(normalize_percent(value) for value in rain_values) / len(rain_values) if rain_values else 0.0
    if not soil_values:
        return round(rain, 4)
    if not rain_values:
        return round(soil, 4)
    return round(SOIL_WEIGHT * soil + RAIN_WEIGHT * rain, 4)


def get_region_soil_saturation(region_id: int) -> SoilSaturation | None:
    query = text("""
        SELECT r.soil_moisture, r.rain_wetness, r.rain_active, r.recorded_at
        FROM sensor_readings r
        JOIN sensor_nodes n ON n.node_id=r.node_id
        WHERE n.region_id=:region_id AND n.status='active'
          AND r.source_mode='LIVE'
          AND r.recorded_at >= NOW() - (:window * INTERVAL '1 minute')
        ORDER BY r.recorded_at DESC LIMIT :limit
    """)
    with engine.connect() as connection:
        rows = connection.execute(query, {"region_id": region_id, "window": WINDOW_MINUTES, "limit": MAX_SAMPLES}).mappings().all()
    if not rows:
        return None
    soil_values = [float(row["soil_moisture"]) for row in rows if row["soil_moisture"] is not None]
    rain_values = [max(float(row["rain_wetness"]), 100.0 if row["rain_active"] else 0.0) for row in rows if row["rain_wetness"] is not None]
    index = compute_soil_saturation_index(soil_values, rain_values)
    if index is None:
        return None
    return SoilSaturation(index=index, soil_moisture_percent=round(sum(soil_values)/len(soil_values), 2) if soil_values else 0.0, rain_wetness_percent=round(sum(rain_values)/len(rain_values), 2) if rain_values else 0.0, sample_count=len(rows), latest_recorded_at=rows[0]["recorded_at"])


def modulate_soil_retention(baseline_retention: float, saturation_index: float | None) -> float:
    baseline = max(0.0, min(float(baseline_retention), 1.0))
    if saturation_index is None:
        return baseline
    return round(baseline * (1.0 - max(0.0, min(saturation_index, 1.0))), 4)
