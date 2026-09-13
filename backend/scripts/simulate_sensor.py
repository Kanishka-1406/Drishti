import math
import random
import time

import httpx


API_URL = (
    "http://127.0.0.1:8000"
    "/sensors/readings"
)

DEVICE_KEY = "drishti-dev-key"

NODE_ID = "drishti-node-01"


def generate_reading(
    counter: int,
):
    # Normal small movement.
    tilt_x = (
        random.uniform(
            -0.25,
            0.25,
        )
    )

    tilt_y = (
        random.uniform(
            -0.25,
            0.25,
        )
    )

    # Every ~20 readings,
    # deliberately produce
    # a stronger simulated tilt.
    if (
        counter % 20
        in (16, 17, 18)
    ):
        tilt_x += 2.8

    soil = random.randint(
        1700,
        1900,
    )

    rain = random.randint(
        850,
        1050,
    )

    return {
        "node_id": NODE_ID,
        "tilt_x": round(
            tilt_x,
            3,
        ),
        "tilt_y": round(
            tilt_y,
            3,
        ),
        "soil_moisture": soil,
        "rain_wetness": rain,
        "rain_active": False,
        "battery": 4.0,
    }


def main():
    headers = {
        "X-Device-Key":
            DEVICE_KEY,
        "X-Source-Mode": "SIMULATED",
    }

    counter = 0

    print(
        "DRISHTI development "
        "sensor simulator"
    )

    print(
        "SOURCE: SIMULATED"
    )

    print(
        "Press Ctrl+C to stop."
    )

    with httpx.Client(
        timeout=10.0
    ) as client:
        while True:
            counter += 1

            payload = (
                generate_reading(
                    counter
                )
            )

            try:
                response = client.post(
                    API_URL,
                    headers=headers,
                    json=payload,
                )

                print(
                    response.status_code,
                    payload,
                )

            except Exception as exc:
                print(
                    "POST failed:",
                    exc,
                )

            time.sleep(2)


if __name__ == "__main__":
    main()
