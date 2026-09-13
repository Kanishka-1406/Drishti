"""NASA FIRMS active-fire/thermal-anomaly context layer.

FIRMS offers a free, same-day self-registration MAP_KEY (no approval wait,
unlike ISRO Bhuvan / Bharat Maps / paid ArcGIS tiers). This module never
blocks app startup or the build on that key existing: if FIRMS_API_KEY is
unset or the request fails, it returns status="unavailable" so the frontend
can show the layer as an honest empty state instead of fabricated points.

This is a secondary context layer only -- it does not feed the landslide
risk score.
"""

import os

import httpx

FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def fetch_active_fires(bbox: str = "68,6,98,38", days: int = 1) -> dict:
    """Fetch active-fire points within a bounding box (default: India extent).

    bbox format matches FIRMS' expected "west,south,east,north" order.
    """
    api_key = os.getenv("FIRMS_API_KEY", "")

    if not api_key:
        return {
            "source": "NASA FIRMS",
            "status": "unavailable",
            "reason": "FIRMS_API_KEY not configured. Request a free same-day key at "
                      "https://firms.modaps.eosdis.nasa.gov/api/ and set it as an env var.",
            "points": [],
        }

    url = f"{FIRMS_AREA_URL}/{api_key}/VIIRS_SNPP_NRT/{bbox}/{days}"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
    except Exception as exc:
        return {
            "source": "NASA FIRMS",
            "status": "unavailable",
            "reason": f"FIRMS request failed: {exc}",
            "points": [],
        }

    lines = response.text.strip().splitlines()

    if len(lines) < 2:
        return {"source": "NASA FIRMS", "status": "ok", "points": []}

    header = lines[0].split(",")
    lat_idx = header.index("latitude")
    lon_idx = header.index("longitude")
    conf_idx = header.index("confidence") if "confidence" in header else None

    points = []

    for line in lines[1:]:
        cols = line.split(",")
        try:
            points.append({
                "lat": float(cols[lat_idx]),
                "lon": float(cols[lon_idx]),
                "confidence": cols[conf_idx] if conf_idx is not None else None,
            })
        except (ValueError, IndexError):
            continue

    return {"source": "NASA FIRMS", "status": "ok", "points": points}
