from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id"),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(Text)
    rainfall_mm: Mapped[float | None] = mapped_column(Float)
    slope_deg: Mapped[float | None] = mapped_column(Float)
    soil_score: Mapped[float | None] = mapped_column(Float)
    historical_score: Mapped[float | None] = mapped_column(Float)
    sensor_adjustment: Mapped[float | None] = mapped_column(
        Float,
        default=0,
        server_default="0",
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        Index("idx_risk_region_time", "region_id", "computed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id"),
        nullable=False,
    )
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    scenario_id: Mapped[int | None] = mapped_column(ForeignKey("scenarios.id"))
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class RiskFactor(Base):
    __tablename__ = "risk_factors"
    __table_args__ = (
        Index("idx_riskfactors_assessment", "risk_assessment_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    risk_assessment_id: Mapped[int] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    factor_name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[float | None] = mapped_column(Float)
    normalized_value: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)
    contribution: Mapped[float | None] = mapped_column(Float)
