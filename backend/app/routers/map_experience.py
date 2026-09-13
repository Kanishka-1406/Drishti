from fastapi import APIRouter

from app.ingestion.fetch_firms import fetch_active_fires

router = APIRouter(prefix="/map", tags=["map-experience"])


@router.get("/firms")
def get_active_fires():
    """Secondary context layer only -- never feeds the landslide risk score.

    Returns status="unavailable" with a reason if FIRMS_API_KEY isn't set,
    rather than fabricating points.
    """
    return fetch_active_fires()


@router.get("/bootstrap")
def get_map_bootstrap():
    """UI bootstrap metadata for the India Explorer.

    Boundary attribution deliberately distinguishes an authoritative Survey of India
    reference from the non-authoritative visual basemap. The prototype must never
    relabel third-party vector boundaries as official Government of India data.
    """
    return {
        "focus": {
            "country": "India",
            "center": [82.5, 23.4],
            "zoom": 4.35,
            "pitch": 48,
            "bearing": 0,
        },
        "boundary": {
            "mode": "official_reference",
            "title": "Political Map of India",
            "publisher": "Survey of India, Department of Science & Technology, Government of India",
            "edition": "13th Edition 2026",
            "scale": "1:4,000,000",
            "reference_url": "https://surveyofindia.gov.in/UserFiles/files/POL_MAP_4M_ENGLISH_13thEdn2026%281%29.pdf",
            "vector_status": "not_embedded",
            "message": (
                "Official Survey of India boundary reference is linked here. "
                "The interactive basemap boundary is visual context only until an "
                "authoritative SoI shapefile is explicitly imported."
            ),
        },
        "terrain": {
            "enabled": True,
            "provider": "MapLibre demo terrain tiles",
            "dem_tiles": "https://demotiles.maplibre.org/terrain-tiles/tiles.json",
            "exaggeration": 1.35,
            "status": "network_required",
        },
        "layers": [
            {"id": "terrain", "label": "3D terrain (DEM)", "enabled": True, "kind": "terrain"},
            {"id": "risk", "label": "Landslide susceptibility", "enabled": True, "kind": "risk"},
            {"id": "rain", "label": "Rainfall signal", "enabled": True, "kind": "rain"},
            {"id": "historical", "label": "Historical landslides", "enabled": True, "kind": "historical"},
            {"id": "sensors", "label": "Ground nodes", "enabled": True, "kind": "sensor"},
            {"id": "official-reference", "label": "Official boundary reference", "enabled": True, "kind": "boundary"},
        ],
        "hotspots": [],
        "usp": [
            {
                "id": "why-risk",
                "title": "Why this risk?",
                "description": "Click any hotspot to see the dominant contributing signals instead of a black-box score.",
            },
            {
                "id": "what-if",
                "title": "What-if rainfall simulator",
                "description": "Explore how a rainfall increase changes the local assessment while preserving provenance.",
            },
            {
                "id": "terrain-story",
                "title": "Terrain story",
                "description": "Tilt and rotate the map to relate slope, relief and landslide exposure spatially.",
            },
            {
                "id": "field-to-map",
                "title": "Field-to-map evidence",
                "description": "Ground-node measurements can be shown beside satellite, historical and terrain evidence.",
            },
        ],
    }
