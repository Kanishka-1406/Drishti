from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.services.ws_manager import (
    manager,
)


router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


@router.websocket("/sensors")
async def sensor_websocket(
    websocket: WebSocket,
):
    await manager.connect(
        websocket
    )

    try:
        while True:
            # Keep connection open.
            #
            # Browser does not need to send
            # sensor data through WebSocket.
            #
            # Sensor readings still enter
            # through POST /sensors/readings.
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(
            websocket
        )

    except Exception:
        manager.disconnect(
            websocket
        )