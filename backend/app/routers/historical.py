import json

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/historical",
    tags=["historical"],
)


@router.get("")
def get_historical_landslides(
    region_id: int = Query(..., gt=0),
):
    query = text("""
        SELECT
            id,
            event_date,
            severity,
            description,
            source,
            confidence,
            ST_AsGeoJSON(geom) AS geometry
        FROM historical_landslides
        WHERE region_id = :region_id
        ORDER BY event_date DESC NULLS LAST
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"region_id": region_id},
        ).mappings().all()

    features = []

    for row in rows:
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(
                    row["geometry"]
                ),
                "properties": {
                    "id": row["id"],
                    "event_date": (
                        row["event_date"].isoformat()
                        if row["event_date"]
                        else None
                    ),
                    "severity": row["severity"],
                    "description": row["description"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }