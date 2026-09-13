import math
import asyncio

import httpx
from sqlalchemy import text

from app.config import settings
from app.database import engine


POINT_ELEVATION_URL = (
    "https://portal.opentopography.org/API/v1/elevation"
)

# Approx distance from center in degrees.
# ~0.001 degree latitude ≈ 111 m.
OFFSET = 0.001


def get_region():
    query = text("""
        SELECT
            id,
            name,
            center_lat,
            center_lon
        FROM regions
        WHERE slug = 'darjeeling'
        LIMIT 1
    """)

    with engine.connect() as connection:
        row = connection.execute(query).mappings().first()

    if not row:
        raise RuntimeError("Darjeeling region not found.")

    return row


async def fetch_elevation(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
) -> float | None:

    params = {
        "latitude": lat,
        "longitude": lon,
        "dataset": "COP30",
        "API_Key": settings.opentopography_api_key,
    }

    response = await client.get(
        POINT_ELEVATION_URL,
        params=params,
    )

    if response.status_code == 404:
        print(
            f"No COP30 elevation found for "
            f"{lat}, {lon}. Skipping."
        )
        return None

    if response.status_code != 200:
        print(
            "OpenTopography status:",
            response.status_code,
        )
        print(
            "OpenTopography response:",
            response.text,
        )

        raise RuntimeError(
            "OpenTopography API request failed."
        )

    payload = response.json()

    elevation = payload.get("Elevation")

    if elevation is None:
        print(
            f"No elevation returned for "
            f"{lat}, {lon}. Skipping."
        )
        return None

    return float(elevation)

def haversine_distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    radius = 6_371_000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(d_lambda / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return radius * c


def calculate_slope_deg(
    elevation_a: float,
    elevation_b: float,
    horizontal_distance_m: float,
) -> float:

    if horizontal_distance_m <= 0:
        return 0.0

    rise = abs(elevation_b - elevation_a)

    slope_radians = math.atan(
        rise / horizontal_distance_m
    )

    return math.degrees(slope_radians)


def store_location(
    region_id: int,
    lat: float,
    lon: float,
    elevation_m: float,
    slope_deg: float,
):
    delete_query = text("""
        DELETE FROM locations
        WHERE region_id = :region_id
          AND name = 'Darjeeling Reference Point'
    """)

    insert_query = text("""
        INSERT INTO locations (
            region_id,
            name,
            geom,
            slope_deg,
            soil_class,
            soil_retention_score,
            elevation_m
        )
        VALUES (
            :region_id,
            'Darjeeling Reference Point',
            ST_SetSRID(
                ST_MakePoint(:lon, :lat),
                4326
            ),
            :slope_deg,
            'unknown',
            0.5,
            :elevation_m
        )
        RETURNING id
    """)

    with engine.begin() as connection:
        connection.execute(
            delete_query,
            {"region_id": region_id},
        )

        location_id = connection.execute(
            insert_query,
            {
                "region_id": region_id,
                "lat": lat,
                "lon": lon,
                "slope_deg": slope_deg,
                "elevation_m": elevation_m,
            },
        ).scalar_one()

    return location_id


async def main():
    if not settings.opentopography_api_key:
        raise RuntimeError(
            "OPENTOPOGRAPHY_API_KEY missing from .env"
        )

    region = get_region()

    lat = float(region["center_lat"])
    lon = float(region["center_lon"])

    points = {
        "center": (lat, lon),
        "north": (lat + OFFSET, lon),
        "south": (lat - OFFSET, lon),
        "east": (lat, lon + OFFSET),
        "west": (lat, lon - OFFSET),
    }

    elevations: dict[str, float | None] = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = {
            name: asyncio.create_task(
                fetch_elevation(
                    client,
                    point_lat,
                    point_lon,
                )
            )
            for name, (point_lat, point_lon) in points.items()
        }

        for name, task in tasks.items():
            elevations[name] = await task

    print()
    print("Fetched elevations:")

    for name, elevation in elevations.items():
        print(f"  {name}: {elevation}")

    center_elevation = elevations["center"]

    if center_elevation is None:
        raise RuntimeError(
            "No COP30 elevation available for "
            "Darjeeling center point."
        )

    slopes = []

    for direction in [
        "north",
        "south",
        "east",
        "west",
    ]:
        direction_elevation = elevations[direction]

        if direction_elevation is None:
            print(
                f"Skipping {direction}: "
                f"no elevation available."
            )
            continue

        point_lat, point_lon = points[direction]

        distance = haversine_distance_m(
            lat,
            lon,
            point_lat,
            point_lon,
        )

        slope = calculate_slope_deg(
            center_elevation,
            direction_elevation,
            distance,
        )

        slopes.append(
            (direction, slope)
        )

    if not slopes:
        raise RuntimeError(
            "Could not calculate terrain slope. "
            "No surrounding elevations were available."
        )

    representative_slope = max(
        slope
        for _, slope in slopes
    )

    location_id = store_location(
        region["id"],
        lat,
        lon,
        center_elevation,
        representative_slope,
    )

    print()
    print("Terrain ingestion complete")
    print("--------------------------")
    print(f"Location ID: {location_id}")
    print(
        f"Elevation: "
        f"{center_elevation:.2f} m"
    )
    print(
        f"Representative slope: "
        f"{representative_slope:.2f} degrees"
    )

    print()
    print("Directional slopes:")

    for direction, slope in slopes:
        print(
            f"  {direction}: "
            f"{slope:.2f}°"
        )


if __name__ == "__main__":
    asyncio.run(main())