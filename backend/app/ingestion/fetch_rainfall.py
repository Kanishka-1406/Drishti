import argparse
import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.database import engine


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_regions(slug: str | None = None):
    query = text("""
        SELECT id, name, slug, center_lat, center_lon
        FROM regions
        WHERE (:slug IS NULL OR slug = :slug)
        ORDER BY name
    """)
    with engine.connect() as connection:
        rows = connection.execute(query, {"slug": slug}).mappings().all()

    if not rows:
        target = f"slug '{slug}'" if slug else "the regions table"
        raise RuntimeError(f"No regions found for {target}. Seed the regions table first.")
    return rows


async def fetch_open_meteo(client: httpx.AsyncClient, lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "auto",
    }
    response = await client.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    return response.json()


def store_rainfall(region_id: int, payload: dict):
    daily = payload.get("daily") or {}
    dates = daily.get("time", [])
    precipitation = daily.get("precipitation_sum", [])

    if not dates or len(dates) != len(precipitation):
        raise RuntimeError("Open-Meteo returned missing or mismatched daily arrays.")

    query = text("""
        INSERT INTO rainfall_observations (
            region_id, obs_date, precipitation_mm, source, fetched_at
        )
        VALUES (
            :region_id, :obs_date, :precipitation_mm, :source, :fetched_at
        )
        ON CONFLICT (region_id, obs_date, source)
        DO UPDATE SET
            precipitation_mm = EXCLUDED.precipitation_mm,
            fetched_at = EXCLUDED.fetched_at
    """)

    fetched_at = datetime.now(timezone.utc)
    rows = [
        {
            "region_id": region_id,
            "obs_date": date,
            "precipitation_mm": float(value),
            "source": "open-meteo",
            "fetched_at": fetched_at,
        }
        for date, value in zip(dates, precipitation)
        if value is not None
    ]

    if not rows:
        raise RuntimeError("Open-Meteo returned no usable precipitation values.")

    with engine.begin() as connection:
        connection.execute(query, rows)
    return len(rows)


async def ingest_region(client: httpx.AsyncClient, region):
    print(
        f"Fetching rainfall: {region['name']} "
        f"({region['center_lat']}, {region['center_lon']})"
    )
    payload = await fetch_open_meteo(
        client,
        float(region["center_lat"]),
        float(region["center_lon"]),
    )
    count = store_rainfall(region["id"], payload)
    print(f"  Stored/updated {count} observations; timezone={payload.get('timezone')}")


async def main():
    parser = argparse.ArgumentParser(description="Fetch Open-Meteo rainfall for DRISHTI regions.")
    parser.add_argument("--region", help="Fetch one region by slug, e.g. darjeeling.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch every configured region. This makes one API request per region.",
    )
    args = parser.parse_args()

    if args.region and args.all:
        parser.error("Use either --region or --all, not both.")

    # Preserve the original safe default; nationwide ingestion is explicit.
    regions = get_regions(None if args.all else (args.region or "darjeeling"))

    async with httpx.AsyncClient(timeout=20.0) as client:
        for region in regions:
            try:
                await ingest_region(client, region)
            except Exception as exc:
                print(f"  ERROR for {region['name']}: {exc}")

    print(f"Rainfall ingestion finished for {len(regions)} selected region(s).")


if __name__ == "__main__":
    asyncio.run(main())
