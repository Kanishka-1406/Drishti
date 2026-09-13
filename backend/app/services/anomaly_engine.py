from dataclasses import dataclass

from sqlalchemy import text

from app.database import engine


NORMAL_THRESHOLD = 1.0
ANOMALY_THRESHOLD = 2.0
ANOMALY_PERSISTENCE = 3

ANOMALY_RISK_ADJUSTMENT = 8.0


@dataclass
class AnomalyResult:
    node_id: str
    state: str

    latest_tilt: float
    consecutive_high_readings: int

    sensor_adjustment: float
    explanation: str


def evaluate_node(
    node_id: str,
    live_only: bool = False,
) -> AnomalyResult:
    source_filter = "AND source_mode = 'LIVE'" if live_only else ""
    query = text(f"""
        SELECT
            tilt_magnitude
        FROM sensor_readings
        WHERE node_id = :node_id
          AND tilt_magnitude IS NOT NULL
          {source_filter}
        ORDER BY recorded_at DESC
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "node_id": node_id,
                "limit": ANOMALY_PERSISTENCE,
            },
        ).mappings().all()

    if not rows:
        return AnomalyResult(
            node_id=node_id,
            state="NO_DATA",
            latest_tilt=0.0,
            consecutive_high_readings=0,
            sensor_adjustment=0.0,
            explanation=(
                "No sensor readings are "
                "available for this node."
            ),
        )

    values = [
        float(row["tilt_magnitude"])
        for row in rows
    ]

    latest = values[0]

    consecutive_high = 0

    for value in values:
        if value > ANOMALY_THRESHOLD:
            consecutive_high += 1
        else:
            break

    if (
        len(values) >= ANOMALY_PERSISTENCE
        and consecutive_high
        >= ANOMALY_PERSISTENCE
    ):
        return AnomalyResult(
            node_id=node_id,
            state="ANOMALY",
            latest_tilt=latest,
            consecutive_high_readings=(
                consecutive_high
            ),
            sensor_adjustment=(
                ANOMALY_RISK_ADJUSTMENT
            ),
            explanation=(
                "Tilt magnitude exceeded "
                "2° for at least 3 "
                "consecutive readings."
            ),
        )

    if latest > NORMAL_THRESHOLD:
        if latest > ANOMALY_THRESHOLD:
            explanation = (
                "Tilt exceeds 2°, but "
                "persistence requirement "
                "has not yet been met."
            )
        else:
            explanation = (
                "Tilt exceeds the 1° "
                "watch threshold."
            )

        return AnomalyResult(
            node_id=node_id,
            state="WATCH",
            latest_tilt=latest,
            consecutive_high_readings=(
                consecutive_high
            ),
            sensor_adjustment=0.0,
            explanation=explanation,
        )

    return AnomalyResult(
        node_id=node_id,
        state="NORMAL",
        latest_tilt=latest,
        consecutive_high_readings=0,
        sensor_adjustment=0.0,
        explanation=(
            "Tilt remains within the "
            "normal threshold."
        ),
    )

def get_region_sensor_state(
    region_id: int,
) -> AnomalyResult | None:
    query = text("""
        SELECT node_id
        FROM sensor_nodes
        WHERE region_id = :region_id
          AND status = 'active'
        ORDER BY id
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "region_id": region_id,
            },
        ).mappings().all()

    if not rows:
        return None

    results = [
        evaluate_node(row["node_id"], live_only=True)
        for row in rows
    ]

    priority = {
        "ANOMALY": 3,
        "WATCH": 2,
        "NORMAL": 1,
        "NO_DATA": 0,
    }

    return max(
        results,
        key=lambda result: priority[
            result.state
        ],
    )
