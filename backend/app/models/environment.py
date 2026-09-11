from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    desc,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RainfallObservation(Base):
    __tablename__ = "rainfall_observations"
    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "obs_date",
            "source",
            name="uq_rainfall_region_date_source",
        ),
        Index(
            "idx_rainfall_region_date",
            "region_id",
            desc("obs_date"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
    )
    obs_date: Mapped[date] = mapped_column(Date, nullable=False)
    precipitation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="open-meteo",
        server_default="open-meteo",
    )
    fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class HistoricalLandslide(Base):
    __tablename__ = "historical_landslides"
    __table_args__ = (
        Index("idx_historical_geom", "geom", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"))
    geom: Mapped[object] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=False),
        nullable=False,
    )
    event_date: Mapped[date | None] = mapped_column(Date)
    severity: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str | None] = mapped_column(
        Text,
        default="reported",
        server_default="reported",
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Infrastructure(Base):
    __tablename__ = "infrastructure"
    __table_args__ = (
        UniqueConstraint("osm_id", name="uq_infrastructure_osm_id"),
        Index("idx_infra_geom", "geom", postgresql_using="gist"),
        Index("idx_infra_region_cat", "region_id", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"))
    osm_id: Mapped[int | None] = mapped_column(BigInteger)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[object] = mapped_column(
        Geometry("GEOMETRY", srid=4326, spatial_index=False),
        nullable=False,
    )
    fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
