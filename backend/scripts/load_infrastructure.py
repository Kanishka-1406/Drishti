import json

import httpx
from sqlalchemy import text

from app.database import engine


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Darjeeling center
CENTER_LAT = 27.041
CENTER_LON = 88.2663

# Roughly ~7 km search radius
RADIUS_METERS = 7000

REGION_ID = 1


OVERPASS_QUERY = f"""
[out:json][timeout:60];

(
  node(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="hospital"];
  way(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="hospital"];
  relation(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="hospital"];

  node(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="school"];
  way(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="school"];
  relation(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="school"];

  node(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="police"];
  way(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="police"];

  node(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="fire_station"];
  way(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["amenity"="fire_station"];

  node(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["highway"="bus_stop"];

  way(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["bridge"];
  way(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["highway"~"primary|secondary|tertiary"];

  node(around:{RADIUS_METERS},{CENTER_LAT},{CENTER_LON})["railway"="station"];
);

out center;
"""


def get_category(tags: dict) -> str:
    amenity = tags.get("amenity")

    if amenity == "hospital":
        return "hospital"

    if amenity == "school":
        return "school"

    if amenity == "police":
        return "police"

    if amenity == "fire_station":
        return "fire_station"

    if tags.get("highway") == "bus_stop":
        return "bus_stop"

    if "bridge" in tags:
        return "bridge"

    if tags.get("railway") == "station":
        return "railway_station"

    if tags.get("highway"):
        return "road"

    return "other"


def get_coordinates(element: dict):
    if element["type"] == "node":
        lat = element.get("lat")
        lon = element.get("lon")

        if lat is None or lon is None:
            return None

        return lon, lat

    center = element.get("center")

    if center:
        lat = center.get("lat")
        lon = center.get("lon")

        if lat is not None and lon is not None:
            return lon, lat

    return None


def make_osm_id(element: dict) -> int:
    """
    OSM IDs can overlap between node/way/relation types.

    Prefix them numerically so our DB UNIQUE constraint remains safe.
    """
    element_id = int(element["id"])

    if element["type"] == "node":
        return 1_000_000_000_000 + element_id

    if element["type"] == "way":
        return 2_000_000_000_000 + element_id

    if element["type"] == "relation":
        return 3_000_000_000_000 + element_id

    return element_id


def fetch_osm_data():
    print("Fetching infrastructure from OpenStreetMap...")

    headers = {
        "User-Agent": "Drishti-Landslide-Risk-MVP/1.0",
        "Referer": "http://127.0.0.1:5173/",
        "Accept": "application/json",
    }

    response = httpx.post(
        OVERPASS_URL,
        data={
            "data": OVERPASS_QUERY,
        },
        headers=headers,
        timeout=90.0,
    )

    print(
        "Overpass status:",
        response.status_code,
    )

    if response.status_code != 200:
        print(
            "Overpass response:",
            response.text[:1000],
        )

    response.raise_for_status()

    return response.json()

def insert_features(elements):
    inserted = 0
    skipped = 0

    query = text("""
        INSERT INTO infrastructure (
            region_id,
            osm_id,
            category,
            name,
            geom
        )
        VALUES (
            :region_id,
            :osm_id,
            :category,
            :name,
            ST_SetSRID(
                ST_MakePoint(
                    :longitude,
                    :latitude
                ),
                4326
            )
        )
        ON CONFLICT (osm_id)
        DO UPDATE SET
            region_id = EXCLUDED.region_id,
            category = EXCLUDED.category,
            name = EXCLUDED.name,
            geom = EXCLUDED.geom,
            fetched_at = NOW()
    """)

    with engine.begin() as connection:
        for element in elements:
            coordinates = get_coordinates(element)

            if coordinates is None:
                skipped += 1
                continue

            longitude, latitude = coordinates

            tags = element.get("tags", {})

            connection.execute(
                query,
                {
                    "region_id": REGION_ID,
                    "osm_id": make_osm_id(element),
                    "category": get_category(tags),
                    "name": (
                        tags.get("name")
                        or tags.get("ref")
                        or None
                    ),
                    "longitude": longitude,
                    "latitude": latitude,
                },
            )

            inserted += 1

    return inserted, skipped


def main():
    data = fetch_osm_data()

    elements = data.get("elements", [])

    print(
        f"Received {len(elements)} OSM elements."
    )

    inserted, skipped = insert_features(elements)

    print(
        f"Inserted/updated: {inserted}"
    )

    print(
        f"Skipped: {skipped}"
    )


if __name__ == "__main__":
    main()