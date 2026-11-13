import argparse
import asyncio
import math

import httpx
from sqlalchemy import text

from app.config import settings
from app.database import engine


POINT_ELEVATION_URL = "https://portal.opentopography.org/API/v1/elevation"
OFFSET = 0.001


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


async def fetch_elevation(client: httpx.AsyncClient, lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "dataset": "COP30",
        "API_Key": settings.opentopography_api_key,
    }
    response = await client.get(POINT_ELEVATION_URL, params=params)

    if response.status_code == 404:
        return None
    response.raise_for_status()

    elevation = response.json().get("Elevation")
    return float(elevation) if elevation is not None else None


def haversine_distance_m(lat1, lon1, lat2, lon2):
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def store_location(region, lat, lon, elevation_m, slope_deg):
    reference_name = f"{region['name']} Reference Point"
    delete_query = text("""
        DELETE FROM locations
        WHERE region_id = :region_id AND name = :reference_name
    """)
    insert_query = text("""
        INSERT INTO locations (
            region_id, name, geom, slope_deg, soil_class,
            soil_retention_score, elevation_m
        )
        VALUES (
            :region_id, :reference_name,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            :slope_deg, 'unknown', NULL, :elevation_m
        )
        RETURNING id
    """)

    with engine.begin() as connection:
        connection.execute(
            delete_query,
            {"region_id": region["id"], "reference_name": reference_name},
        )
        return connection.execute(
            insert_query,
            {
                "region_id": region["id"],
                "reference_name": reference_name,
                "lat": lat,
                "lon": lon,
                "slope_deg": slope_deg,
                "elevation_m": elevation_m,
            },
        ).scalar_one()


async def ingest_region(client: httpx.AsyncClient, region):
    lat, lon = float(region["center_lat"]), float(region["center_lon"])
    points = {
        "center": (lat, lon),
        "north": (lat + OFFSET, lon),
        "south": (lat - OFFSET, lon),
        "east": (lat, lon + OFFSET),
        "west": (lat, lon - OFFSET),
    }

    print(f"Fetching terrain: {region['name']} ({lat}, {lon})")
    elevations = {}
    for name, (point_lat, point_lon) in points.items():
        elevations[name] = await fetch_elevation(client, point_lat, point_lon)

    center_elevation = elevations["center"]
    if center_elevation is None:
        raise RuntimeError("No center elevation returned by OpenTopography.")

    slopes = []
    for direction in ("north", "south", "east", "west"):
        neighbor_elevation = elevations[direction]
        if neighbor_elevation is None:
            continue

        point_lat, point_lon = points[direction]
        distance = haversine_distance_m(lat, lon, point_lat, point_lon)
        if distance <= 0:
            continue
        slope = math.degrees(
            math.atan(abs(neighbor_elevation - center_elevation) / distance)
        )
        slopes.append(slope)

    if not slopes:
        raise RuntimeError("No surrounding elevations available to calculate slope.")

    # This is a coarse center-point directional slope proxy, not a DEM-derived
    # regional slope surface. Soil remains NULL until a sourced soil dataset is loaded.
    representative_slope = max(slopes)
    location_id = store_location(
        region, lat, lon, center_elevation, representative_slope
    )
    print(
        f"  Stored location {location_id}: elevation={center_elevation:.2f} m, "
        f"max directional slope={representative_slope:.2f}°; soil=UNAVAILABLE"
    )


async def main():
    parser = argparse.ArgumentParser(description="Fetch OpenTopography terrain reference points.")
    parser.add_argument("--region", help="Fetch one region by slug, e.g. darjeeling.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch every configured region. Uses up to five elevation requests per region.",
    )
    args = parser.parse_args()

    if args.region and args.all:
        parser.error("Use either --region or --all, not both.")
    if not settings.opentopography_api_key:
        raise RuntimeError("OPENTOPOGRAPHY_API_KEY missing from .env")

    regions = get_regions(None if args.all else (args.region or "darjeeling"))
    async with httpx.AsyncClient(timeout=30.0) as client:
        for region in regions:
            try:
                await ingest_region(client, region)
            except Exception as exc:
                print(f"  ERROR for {region['name']}: {exc}")

    print(f"Terrain ingestion finished for {len(regions)} selected region(s).")


if __name__ == "__main__":
    asyncio.run(main())
