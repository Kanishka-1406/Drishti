import csv
from pathlib import Path

from sqlalchemy import text

from app.database import engine


CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "historical_landslides.csv"
)


def get_darjeeling_region_id():
    query = text("""
        SELECT id
        FROM regions
        WHERE slug = 'darjeeling'
        LIMIT 1
    """)

    with engine.connect() as connection:
        row = connection.execute(query).mappings().first()

    if not row:
        raise RuntimeError("Darjeeling region not found.")

    return row["id"]


def load_historical():
    region_id = get_darjeeling_region_id()

    if not CSV_PATH.exists():
        raise RuntimeError(
            f"CSV not found: {CSV_PATH}"
        )

    inserted = 0
    skipped = 0

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    with engine.begin() as connection:
        for row in rows:
            latitude = row.get("latitude")
            longitude = row.get("longitude")

            if not latitude or not longitude:
                print(
                    f"Skipping {row.get('name')}: "
                    "missing coordinates"
                )
                skipped += 1
                continue

            latitude = float(latitude)
            longitude = float(longitude)

            if not (-90 <= latitude <= 90):
                print("Invalid latitude:", latitude)
                skipped += 1
                continue

            if not (-180 <= longitude <= 180):
                print("Invalid longitude:", longitude)
                skipped += 1
                continue

            existing_query = text("""
                SELECT id
                FROM historical_landslides
                WHERE region_id = :region_id
                  AND event_date = :event_date
                  AND source = :source
                  AND ST_DWithin(
                        geom::geography,
                        ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            4326
                        )::geography,
                        20
                  )
                LIMIT 1
            """)

            existing = connection.execute(
                existing_query,
                {
                    "region_id": region_id,
                    "event_date": row.get(
                        "event_date"
                    ) or None,
                    "source": row.get("source"),
                    "longitude": longitude,
                    "latitude": latitude,
                },
            ).first()

            if existing:
                print(
                    f"Already exists: "
                    f"{row.get('name')}"
                )
                skipped += 1
                continue

            insert_query = text("""
                INSERT INTO historical_landslides (
                    region_id,
                    geom,
                    event_date,
                    severity,
                    description,
                    source,
                    confidence
                )
                VALUES (
                    :region_id,
                    ST_SetSRID(
                        ST_MakePoint(
                            :longitude,
                            :latitude
                        ),
                        4326
                    ),
                    :event_date,
                    :severity,
                    :description,
                    :source,
                    :confidence
                )
            """)

            connection.execute(
                insert_query,
                {
                    "region_id": region_id,
                    "longitude": longitude,
                    "latitude": latitude,
                    "event_date": (
                        row.get("event_date")
                        or None
                    ),
                    "severity": (
                        row.get("severity")
                        or None
                    ),
                    "description": (
                        row.get("description")
                        or None
                    ),
                    "source": (
                        row.get("source")
                        or "unknown"
                    ),
                    "confidence": float(
                        row.get("confidence")
                        or 1.0
                    ),
                },
            )

            inserted += 1

    print(
        f"Historical load complete. "
        f"inserted={inserted}, "
        f"skipped={skipped}"
    )


if __name__ == "__main__":
    load_historical()