from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    # The scenario engine is stateless and does not query the regions table.
    # Negative IDs are reserved by the frontend for explicitly labelled demo regions.
    region_id: int = Field(
        description="Region identifier echoed for traceability; no database lookup is performed."
    )

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
