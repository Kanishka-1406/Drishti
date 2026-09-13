import math

from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.schemas.sensors import SensorCalibration, SensorReadingCreate
from fastapi import BackgroundTasks
from app.services.anomaly_engine import (evaluate_node,)
from app.services.ws_manager import (manager,)

router = APIRouter(
    prefix="/sensors",
    tags=["sensors"],
)


def get_sensor_node(node_id: str):
    query = text("""
        SELECT
            id,
            node_id,
            region_id,
            location_id,
            label,
            baseline_tilt_x,
            baseline_tilt_y,
            last_seen_at,
            status
        FROM sensor_nodes
        WHERE node_id = :node_id
        LIMIT 1
    """)

    with engine.connect() as connection:
        return connection.execute(
            query,
            {
                "node_id": node_id,
            },
        ).mappings().first()


@router.post("/readings")
def ingest_sensor_reading(
    payload: SensorReadingCreate,
    background_tasks: BackgroundTasks,
    x_device_key: str | None = Header(
        default=None,
        alias="X-Device-Key",
    ),
    x_source_mode: str | None = Header(default=None, alias="X-Source-Mode"),
):
    # --------------------------------
    # Device authentication
    # --------------------------------

    if (
        not x_device_key
        or x_device_key
        != settings.device_api_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid device key",
        )

    # --------------------------------
    # Find node
    # --------------------------------

    node = get_sensor_node(
        payload.node_id
    )

    if not node:
        raise HTTPException(
            status_code=404,
            detail="Sensor node not found",
        )

    if node["status"] != "active":
        raise HTTPException(
            status_code=403,
            detail="Sensor node is inactive",
        )

    # --------------------------------
    # Timestamp
    # --------------------------------

    recorded_at = (
        payload.recorded_at
        or datetime.now(timezone.utc)
    )

    received_at = datetime.now(
        timezone.utc
    )

    # --------------------------------
    # Tilt magnitude
    # --------------------------------

    tilt_magnitude = math.sqrt(
        payload.tilt_x ** 2
        + payload.tilt_y ** 2
    )

    # --------------------------------
    # Insert reading
    # --------------------------------

    source_mode = "SIMULATED" if (x_source_mode or "").upper() == "SIMULATED" else "LIVE"
    insert_query = text("""
        INSERT INTO sensor_readings (
            node_id,
            recorded_at,
            soil_moisture,
            rain_wetness,
            rain_active,
            tilt_x,
            tilt_y,
            tilt_magnitude,
            battery,
            received_at,
            source_mode
        )
        VALUES (
            :node_id,
            :recorded_at,
            :soil_moisture,
            :rain_wetness,
            :rain_active,
            :tilt_x,
            :tilt_y,
            :tilt_magnitude,
            :battery,
            :received_at,
            :source_mode
        )
        RETURNING id
    """)

    update_node_query = text("""
        UPDATE sensor_nodes
        SET last_seen_at = :last_seen_at
        WHERE node_id = :node_id
    """)

    with engine.begin() as connection:
        reading_id = connection.execute(
            insert_query,
            {
                "node_id":
                    payload.node_id,
                "recorded_at":
                    recorded_at,
                "soil_moisture":
                    payload.soil_moisture,
                "rain_wetness":
                    payload.rain_wetness,
                "rain_active":
                    payload.rain_active,
                "tilt_x":
                    payload.tilt_x,
                "tilt_y":
                    payload.tilt_y,
                "tilt_magnitude":
                    tilt_magnitude,
                "battery":
                    payload.battery,
                "received_at":
                    received_at,
                "source_mode": source_mode,
            },
        ).scalar_one()

        connection.execute(
            update_node_query,
            {
                "node_id":
                    payload.node_id,
                "last_seen_at":
                    received_at,
            },
        )

    anomaly = evaluate_node(
        payload.node_id
    )

    ws_message = {
        "type": "sensor_reading",
        "source_mode": source_mode,
        "node_id": payload.node_id,
        "reading": {
            "id": reading_id,
            "recorded_at":
                recorded_at.isoformat(),
            "tilt_x":
                payload.tilt_x,
            "tilt_y":
                payload.tilt_y,
            "tilt_magnitude":
                round(
                    tilt_magnitude,
                    3,
                ),
            "soil_moisture":
                payload.soil_moisture,
            "rain_wetness":
                payload.rain_wetness,
            "rain_active":
                payload.rain_active,
            "battery":
                payload.battery,
        },

        "anomaly": {
            "state":
                anomaly.state,

            "latest_tilt":
                anomaly.latest_tilt,

            "consecutive_high_readings":
                anomaly
                .consecutive_high_readings,

            "sensor_adjustment":
                anomaly.sensor_adjustment,

            "explanation":
                anomaly.explanation,
        },
        
    }

    background_tasks.add_task(
        manager.broadcast,
        ws_message,
    )

    return {
        "status": "accepted",
        "reading_id": reading_id,
        "node_id":
            payload.node_id,
        "recorded_at":
            recorded_at,
        "tilt_magnitude":
            round(
                tilt_magnitude,
                3,
            ),
        "anomaly_state": anomaly.state,
        "sensor_adjustment": anomaly.sensor_adjustment,
        "source_mode": source_mode,
    }

@router.get("/{node_id}/latest")
def get_latest_reading(
    node_id: str,
):
    node = get_sensor_node(
        node_id
    )

    if not node:
        raise HTTPException(
            status_code=404,
            detail="Sensor node not found",
        )

    query = text("""
        SELECT
            id,
            node_id,
            recorded_at,
            soil_moisture,
            rain_wetness,
            rain_active,
            tilt_x,
            tilt_y,
            tilt_magnitude,
            battery,
            received_at,
            source_mode
        FROM sensor_readings
        WHERE node_id = :node_id
        ORDER BY recorded_at DESC
        LIMIT 1
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "node_id": node_id,
            },
        ).mappings().first()

    if not row:
        return {
            "node_id": node_id,
            "label": node["label"],
            "status": node["status"],
            "reading": None,
        }

    return {
        "node_id": node_id,
        "label": node["label"],
        "status": node["status"],
        "last_seen_at":
            node["last_seen_at"],
        "reading": {
            "id": row["id"],
            "recorded_at":
                row["recorded_at"],
            "tilt_x":
                row["tilt_x"],
            "tilt_y":
                row["tilt_y"],
            "tilt_magnitude":
                row["tilt_magnitude"],
            "soil_moisture":
                row["soil_moisture"],
            "rain_wetness":
                row["rain_wetness"],
            "rain_active":
                row["rain_active"],
            "battery":
                row["battery"],
            "received_at":
                row["received_at"],
            "source_mode": row["source_mode"],
        },
        "source_mode": row["source_mode"],
    }


@router.get("")
def list_sensor_nodes():
    query = text("""
        SELECT n.node_id, n.label, n.status, n.last_seen_at, n.baseline_tilt_x,
               n.baseline_tilt_y, n.region_id, COUNT(r.id) AS packet_count
        FROM sensor_nodes n LEFT JOIN sensor_readings r ON r.node_id=n.node_id
        GROUP BY n.id ORDER BY n.id
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()
    now = datetime.now(timezone.utc)
    return [{**dict(row), "online": bool(row["last_seen_at"] and (now-row["last_seen_at"]).total_seconds()<30), "age_seconds": int((now-row["last_seen_at"]).total_seconds()) if row["last_seen_at"] else None} for row in rows]


@router.get("/{node_id}/history")
def sensor_history(node_id: str, limit: int = 30):
    if not get_sensor_node(node_id):
        raise HTTPException(status_code=404, detail="Sensor node not found")
    query = text("""SELECT recorded_at,tilt_magnitude,tilt_x,tilt_y,soil_moisture,
        rain_wetness,rain_active,battery,source_mode FROM sensor_readings
        WHERE node_id=:node_id ORDER BY recorded_at DESC LIMIT :limit""")
    with engine.connect() as connection:
        rows = connection.execute(query,{"node_id":node_id,"limit":min(max(limit,1),200)}).mappings().all()
    return {"node_id":node_id,"count":len(rows),"readings":[dict(row) for row in rows]}


@router.post("/{node_id}/calibrate")
def calibrate_sensor(node_id: str, payload: SensorCalibration, x_device_key: str | None = Header(default=None, alias="X-Device-Key")):
    if x_device_key != settings.device_api_key:
        raise HTTPException(status_code=401, detail="Invalid device key")
    with engine.begin() as connection:
        result=connection.execute(text("""UPDATE sensor_nodes SET baseline_tilt_x=:x,
            baseline_tilt_y=:y WHERE node_id=:node_id"""),{"x":payload.baseline_tilt_x,"y":payload.baseline_tilt_y,"node_id":node_id})
    if not result.rowcount: raise HTTPException(status_code=404,detail="Sensor node not found")
    return {"status":"calibrated","node_id":node_id,"baseline_tilt_x":payload.baseline_tilt_x,"baseline_tilt_y":payload.baseline_tilt_y}
