from sqlalchemy import text

from app.database import engine


def main():
    query = text("""
        UPDATE locations
        SET
            soil_class = :soil_class,
            soil_retention_score = :soil_retention_score
        WHERE region_id = (
            SELECT id
            FROM regions
            WHERE slug = 'darjeeling'
            LIMIT 1
        )
          AND name = 'Darjeeling Reference Point'
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "soil_class": "mixed_hill_soil_reference",
                "soil_retention_score": 0.45,
            },
        )

    print(
        f"Updated {result.rowcount} location(s) "
        "with soil reference baseline."
    )


if __name__ == "__main__":
    main()