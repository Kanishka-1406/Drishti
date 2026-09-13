import json

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/infrastructure",
    tags=["infrastructure"],
)


@router.get("")
def get_infrastructure(
    region_id: int = Query(..., gt=0),
):
    query = text("""
        SELECT
            id,
            osm_id,
            category,
            COALESCE(
                NULLIF(name, ''),
                INITCAP(category)
            ) AS name,
            fetched_at,
            ST_AsGeoJSON(geom) AS geometry
        FROM infrastructure
        WHERE region_id = :region_id
          AND category IN (
              'hospital',
              'school',
              'police',
              'fire_station'
            )
        ORDER BY category, name
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
                    "osm_id": row["osm_id"],
                    "category": row["category"],
                    "name": row["name"],
                    "fetched_at": (
                        row["fetched_at"].isoformat()
                        if row["fetched_at"]
                        else None
                    ),
                },
            }
        )

    
    category_counts = {}

    for feature in features:
        category = (
            feature["properties"].get("category")
            or "unknown"
        )

        category_counts[category] = (
            category_counts.get(category, 0)
              + 1
        )


    return {
        "type": "FeatureCollection",
        "count": len(features),
        "category_counts": category_counts,
        "features": features,
    }