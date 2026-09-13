from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/regions",
    tags=["regions"],
)


@router.get("")
def list_regions():
    query = text("""
        SELECT
            id,
            name,
            slug,
            center_lat,
            center_lon,
            default_zoom
        FROM regions
        ORDER BY name
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "center_lat": float(row["center_lat"]),
            "center_lon": float(row["center_lon"]),
            "default_zoom": row["default_zoom"],
        }
        for row in rows
    ]