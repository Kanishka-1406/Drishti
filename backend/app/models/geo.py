from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    boundary: Mapped[object | None] = mapped_column(
        Geometry("POLYGON", srid=4326),
        nullable=True,
    )
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lon: Mapped[float] = mapped_column(Float, nullable=False)
    default_zoom: Mapped[int | None] = mapped_column(Integer, default=12)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("idx_locations_geom", "geom", postgresql_using="gist"),
        Index("idx_locations_region", "region_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[object] = mapped_column(
        Geometry("POINT", srid=4326),
        nullable=False,
    )
    slope_deg: Mapped[float | None] = mapped_column(Float)
    soil_class: Mapped[str | None] = mapped_column(Text)
    soil_retention_score: Mapped[float | None] = mapped_column(Float)
    elevation_m: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
