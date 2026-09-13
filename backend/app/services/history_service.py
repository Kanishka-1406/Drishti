from sqlalchemy import text

from app.database import engine


def get_nearby_history_count(
    location_id: int,
    radius_m: float = 2000,
) -> int:

    query = text("""
        SELECT COUNT(*)
        FROM historical_landslides h
        JOIN locations l
          ON l.id = :location_id
        WHERE h.region_id = l.region_id
          AND ST_DWithin(
                h.geom::geography,
                l.geom::geography,
                :radius_m
          )
    """)

    with engine.connect() as connection:
        count = connection.execute(
            query,
            {
                "location_id": location_id,
                "radius_m": radius_m,
            },
        ).scalar_one()

    return int(count)