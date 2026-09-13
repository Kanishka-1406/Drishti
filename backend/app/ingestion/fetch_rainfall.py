import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.database import engine


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_region():
    query = text("""
        SELECT id, name, center_lat, center_lon
        FROM regions
        WHERE slug = :slug
        LIMIT 1
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"slug": "darjeeling"},
        ).mappings().first()

    if not row:
        raise RuntimeError(
            "Darjeeling region not found. "
            "Seed regions table before running ingestion."
        )

    return row


async def fetch_open_meteo(lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            OPEN_METEO_URL,
            params=params,
        )

        response.raise_for_status()

        return response.json()


def store_rainfall(region_id: int, payload: dict):
    daily = payload.get("daily")

    if not daily:
        raise RuntimeError("Open-Meteo returned no daily data.")

    dates = daily.get("time", [])
    precipitation = daily.get("precipitation_sum", [])

    if len(dates) != len(precipitation):
        raise RuntimeError(
            "Open-Meteo response has mismatched daily arrays."
        )

    query = text("""
        INSERT INTO rainfall_observations (
            region_id,
            obs_date,
            precipitation_mm,
            source,
            fetched_at
        )
        VALUES (
            :region_id,
            :obs_date,
            :precipitation_mm,
            :source,
            :fetched_at
        )
        ON CONFLICT (region_id, obs_date, source)
        DO UPDATE SET
            precipitation_mm = EXCLUDED.precipitation_mm,
            fetched_at = EXCLUDED.fetched_at
    """)

    inserted = 0

    with engine.begin() as connection:
        for date, rainfall in zip(dates, precipitation):
            # occasionally APIs may contain null values
            if rainfall is None:
                continue

            connection.execute(
                query,
                {
                    "region_id": region_id,
                    "obs_date": date,
                    "precipitation_mm": float(rainfall),
                    "source": "open-meteo",
                    "fetched_at": datetime.now(timezone.utc),
                },
            )

            inserted += 1

    return inserted


async def main():
    region = get_region()

    print(
        f"Fetching rainfall for "
        f"{region['name']} "
        f"({region['center_lat']}, {region['center_lon']})"
    )

    payload = await fetch_open_meteo(
        float(region["center_lat"]),
        float(region["center_lon"]),
    )

    rows = store_rainfall(
        region["id"],
        payload,
    )

    print(f"Stored/updated {rows} rainfall observations.")

    print(
        "Open-Meteo timezone:",
        payload.get("timezone"),
    )


if __name__ == "__main__":
    asyncio.run(main())