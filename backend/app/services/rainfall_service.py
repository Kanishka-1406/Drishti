from datetime import datetime, timezone

from sqlalchemy import text

from app.database import engine

def classify_freshness(seconds: int | None) -> str:
    if seconds is None:
        return "missing"

    if seconds <= 3 * 3600:
        return "fresh"

    if seconds <= 12 * 3600:
        return "aging"

    return "stale"


def get_rainfall_summary(region_id: int) -> dict:
    query = text("""
        SELECT
            COALESCE(SUM(precipitation_mm), 0) AS rainfall_7d_mm,
            MAX(obs_date) AS latest_observation_date,
            MAX(fetched_at) AS latest_fetched_at
        FROM rainfall_observations
        WHERE region_id = :region_id
          AND obs_date >= CURRENT_DATE - INTERVAL '6 days'
          AND obs_date <= CURRENT_DATE
          AND source = 'open-meteo'
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"region_id": region_id},
        ).mappings().first()

    latest_fetched_at = row["latest_fetched_at"]

    freshness_seconds = None

    if latest_fetched_at:
        now = datetime.now(timezone.utc)

        # PostgreSQL timestamptz should already be timezone-aware
        freshness_seconds = int(
            (now - latest_fetched_at).total_seconds()
        )

    return {
    "region_id": region_id,
    "rainfall_7d_mm": round(
        float(row["rainfall_7d_mm"] or 0),
        2,
    ),
    "latest_observation_date": (
        row["latest_observation_date"].isoformat()
        if row["latest_observation_date"]
        else None
    ),
    "source": "open-meteo",
    "fetched_at": (
        latest_fetched_at.isoformat()
        if latest_fetched_at
        else None
    ),
    "freshness_seconds": freshness_seconds,
    "freshness_status": classify_freshness(
        freshness_seconds
    ),
}