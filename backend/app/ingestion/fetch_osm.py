"""Populate infrastructure from the public OpenStreetMap Overpass API.

The ingestion is region-driven and idempotent. Point amenities are stored as points;
primary/secondary/trunk roads are stored as LineStrings when Overpass supplies geometry.
A failure in one region is reported and does not erase cached rows or stop other regions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx
from sqlalchemy import text

from app.database import engine

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "DRISHTI-Terrain-Intelligence/1.0 (hackathon decision-support prototype)"


@dataclass(frozen=True)
class RegionBounds:
    region_id: int
    name: str
    south: float
    west: float
    north: float
    east: float


def build_overpass_query(bounds: RegionBounds) -> str:
    bbox = f"{bounds.south},{bounds.west},{bounds.north},{bounds.east}"
    return f"""[out:json][timeout:60];
(
  nwr[\"amenity\"~\"^(hospital|school|police|fire_station)$\"]({bbox});
  way[\"highway\"~\"^(primary|secondary|trunk)$\"]({bbox});
);
out center geom;"""


def classify(tags: dict) -> str | None:
    amenity = tags.get("amenity")
    if amenity in {"hospital", "school", "police", "fire_station"}:
        return amenity
    if tags.get("highway") in {"primary", "secondary", "trunk"}:
        return "road"
    return None


def make_osm_id(element: dict) -> int:
    prefixes = {"node": 1_000_000_000_000, "way": 2_000_000_000_000, "relation": 3_000_000_000_000}
    return prefixes.get(element.get("type"), 4_000_000_000_000) + int(element["id"])


def element_geojson(element: dict) -> dict | None:
    if element.get("type") == "node" and element.get("lat") is not None and element.get("lon") is not None:
        return {"type": "Point", "coordinates": [element["lon"], element["lat"]]}
    geometry = element.get("geometry") or []
    coordinates = [[point["lon"], point["lat"]] for point in geometry if point.get("lat") is not None and point.get("lon") is not None]
    if len(coordinates) >= 2:
        return {"type": "LineString", "coordinates": coordinates}
    center = element.get("center") or {}
    if center.get("lat") is not None and center.get("lon") is not None:
        return {"type": "Point", "coordinates": [center["lon"], center["lat"]]}
    return None


def list_region_bounds() -> list[RegionBounds]:
    query = text("""
        SELECT id,name,
          COALESCE(ST_YMin(Box2D(boundary)),center_lat-0.08) south,
          COALESCE(ST_XMin(Box2D(boundary)),center_lon-0.08) west,
          COALESCE(ST_YMax(Box2D(boundary)),center_lat+0.08) north,
          COALESCE(ST_XMax(Box2D(boundary)),center_lon+0.08) east
        FROM regions ORDER BY id
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()
    return [RegionBounds(row["id"], row["name"], float(row["south"]), float(row["west"]), float(row["north"]), float(row["east"])) for row in rows]


def fetch_overpass(bounds: RegionBounds, client: httpx.Client | None = None) -> dict:
    owned = client is None
    client = client or httpx.Client(timeout=90, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        response = client.post(OVERPASS_URL, data={"data": build_overpass_query(bounds)})
        response.raise_for_status()
        return {"status": "ok", "elements": response.json().get("elements", [])}
    except Exception as exc:
        return {"status": "unavailable", "reason": f"Overpass request failed: {type(exc).__name__}", "elements": []}
    finally:
        if owned:
            client.close()


def upsert_elements(region_id: int, elements: list[dict]) -> dict:
    statement = text("""
        INSERT INTO infrastructure(region_id,osm_id,category,name,geom,fetched_at)
        VALUES(:region_id,:osm_id,:category,:name,ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326),NOW())
        ON CONFLICT(osm_id) DO UPDATE SET region_id=EXCLUDED.region_id,
          category=EXCLUDED.category,name=EXCLUDED.name,geom=EXCLUDED.geom,fetched_at=NOW()
    """)
    written = skipped = 0
    with engine.begin() as connection:
        for element in elements:
            category, geometry = classify(element.get("tags", {})), element_geojson(element)
            if not category or not geometry:
                skipped += 1
                continue
            tags = element.get("tags", {})
            connection.execute(statement, {"region_id": region_id, "osm_id": make_osm_id(element), "category": category, "name": tags.get("name") or tags.get("ref") or (f"{tags.get('highway','')} road" if category == "road" else category.replace("_", " ").title()), "geometry": json.dumps(geometry)})
            written += 1
    return {"written": written, "skipped": skipped}


def ingest_all_regions(client: httpx.Client | None = None) -> dict:
    results = []
    for bounds in list_region_bounds():
        fetched = fetch_overpass(bounds, client)
        if fetched["status"] != "ok":
            results.append({"region_id": bounds.region_id, "region": bounds.name, **fetched})
            continue
        counts = upsert_elements(bounds.region_id, fetched["elements"])
        results.append({"region_id": bounds.region_id, "region": bounds.name, "status": "ok", **counts})
    ok = sum(item["status"] == "ok" for item in results)
    return {"status": "ok" if ok == len(results) else "partial" if ok else "unavailable", "regions": results, "region_count": len(results), "successful_regions": ok}


def main() -> None:
    print(json.dumps(ingest_all_regions(), indent=2))


if __name__ == "__main__":
    main()
