from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SensorNode(Base):
    __tablename__ = "sensor_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    label: Mapped[str | None] = mapped_column(Text)
    baseline_tilt_x: Mapped[float | None] = mapped_column(
        Float,
        default=0,
        server_default="0",
    )
    baseline_tilt_y: Mapped[float | None] = mapped_column(
        Float,
        default=0,
        server_default="0",
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(
        Text,
        default="offline",
        server_default="offline",
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        Index("idx_readings_node_time", "node_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    node_id: Mapped[str] = mapped_column(
        ForeignKey("sensor_nodes.node_id"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    soil_moisture: Mapped[float | None] = mapped_column(Float)
    rain_wetness: Mapped[float | None] = mapped_column(Float)
    rain_active: Mapped[bool | None] = mapped_column(Boolean)
    tilt_x: Mapped[float | None] = mapped_column(Float)
    tilt_y: Mapped[float | None] = mapped_column(Float)
    tilt_magnitude: Mapped[float | None] = mapped_column(Float)
    battery: Mapped[float | None] = mapped_column(Float)
    source_mode: Mapped[str] = mapped_column(Text, default="LIVE", server_default="LIVE")
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class SensorAnomaly(Base):
    __tablename__ = "sensor_anomalies"
    __table_args__ = (
        Index("idx_anomalies_node", "node_id", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[str] = mapped_column(
        ForeignKey("sensor_nodes.node_id"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anomaly_type: Mapped[str] = mapped_column(Text, nullable=False)
    peak_magnitude: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(
        Text,
        default="active",
        server_default="active",
    )
