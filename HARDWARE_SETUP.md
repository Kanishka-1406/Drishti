# DRISHTI hardware integration

## Wiring

| Sensor | ESP32 |
|---|---|
| MPU6050 VCC/GND | 3.3V/GND |
| MPU6050 SDA/SCL | GPIO21/GPIO22 |
| Capacitive soil analog | GPIO34 |
| Rain sensor analog | GPIO35 |
| Rain sensor digital | GPIO27 |
| Battery divider midpoint | GPIO32 |

Use a common ground. ESP32 ADC pins must never receive more than 3.3 V.

## Flash

Open `firmware/drishti_node/drishti_node.ino`. Set Wi-Fi credentials and replace the IP in `API_URL` with the laptop's Wi-Fi IPv4 address (`ipconfig`). Keep `NODE_ID=drishti-node-01` and make `DEVICE_KEY` equal the backend `.env` value. Flash with Arduino IDE using the ESP32 board package. Keep the node still during boot calibration and use Serial Monitor at 115200 baud.

## Network

Start DRISHTI, allow Python through Windows Firewall on Private networks, and confirm from another device on the same Wi-Fi that `http://LAPTOP_IP:8000/health` responds. The backend launcher must bind to `0.0.0.0` for ESP32 access.

## Packet contract

`POST /sensors/readings` with `Content-Type: application/json` and `X-Device-Key`.

```json
{"node_id":"drishti-node-01","tilt_x":0.14,"tilt_y":0.09,"soil_moisture":63,"rain_wetness":21,"rain_active":false,"battery":3.92}
```

Physical firmware omits `X-Source-Mode`, so it is stored as `LIVE`. The simulator alone sends `X-Source-Mode: SIMULATED`.

## Judge demo

1. Show the node as offline.
2. Power the ESP32 and show `SENSOR · LIVE`, packet count and last-seen age update.
3. Keep it level to show NORMAL.
4. Tilt beyond 1° to show WATCH.
5. Hold beyond 2° for three packets to show ANOMALY and the +8 risk adjustment.
6. Open the raw timeline to show the exact packets that caused the state.

Endpoints: `GET /sensors`, `GET /sensors/{node_id}/latest`, `GET /sensors/{node_id}/history`, and authenticated `POST /sensors/{node_id}/calibrate`.
