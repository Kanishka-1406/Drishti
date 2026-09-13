from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200


def test_regions():
    response = client.get("/regions")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_scenario_simulation():
    payload = {
        "region_id": 1,
        "rainfall_mm": 150,
        "slope_deg": 22.5,
        "soil_retention_score": 0.5,
        "historical_count_2km": 2,
        "sensor_adjustment": 0,
    }

    response = client.post(
        "/scenarios/simulate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["risk_score"] == 48.5
    assert body["risk_category"] == "MODERATE"
    assert body["scenario"] is True


def test_invalid_scenario_rejected():
    payload = {
        "region_id": 1,
        "rainfall_mm": -500,
        "slope_deg": 22.5,
        "soil_retention_score": 0.5,
        "historical_count_2km": 2,
    }

    response = client.post(
        "/scenarios/simulate",
        json=payload,
    )

    assert response.status_code == 422