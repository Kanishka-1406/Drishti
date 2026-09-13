from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    region_id: int = Field(gt=0)

    rainfall_mm: float = Field(
        ge=0,
        le=400,
    )

    slope_deg: float = Field(
        ge=0,
        le=60,
    )

    soil_retention_score: float = Field(
        ge=0,
        le=1,
    )

    historical_count_2km: int = Field(
        ge=0,
        le=20,
    )

    sensor_adjustment: float = Field(
        default=0,
        ge=0,
        le=20,
    )