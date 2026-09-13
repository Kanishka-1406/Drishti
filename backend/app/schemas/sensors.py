from datetime import datetime

from pydantic import BaseModel, Field


class SensorReadingCreate(BaseModel):
    node_id: str

    tilt_x: float
    tilt_y: float

    soil_moisture: float | None = None
    rain_wetness: float | None = None
    rain_active: bool | None = None
    battery: float | None = Field(
        default=None,
        ge=0,
    )

    recorded_at: datetime | None = None


class SensorCalibration(BaseModel):
    baseline_tilt_x: float
    baseline_tilt_y: float
