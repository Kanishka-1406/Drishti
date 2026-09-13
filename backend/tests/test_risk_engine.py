import pytest

from app.services.risk_engine import (
    RiskInput,
    compute_risk,
    get_risk_category,
)


def test_known_risk_calculation():
    data = RiskInput(
        rainfall_7d_mm=150.0,
        slope_deg=22.5,
        soil_retention_score=0.5,
        historical_count_2km=2,
        sensor_adjustment=0.0,
    )

    result = compute_risk(data)

    # Rainfall:
    # 150 / 300 = 0.5
    # 0.5 * 0.40 * 100 = 20

    # Slope:
    # 22.5 / 45 = 0.5
    # 0.5 * 0.25 * 100 = 12.5

    # Soil:
    # 1 - 0.5 = 0.5
    # 0.5 * 0.20 * 100 = 10

    # History:
    # 2 / 5 = 0.4
    # 0.4 * 0.15 * 100 = 6

    # Total = 48.5

    assert result.base_score == 48.5
    assert result.final_score == 48.5
    assert result.category == "MODERATE"


def test_sensor_adjustment():
    data = RiskInput(
        rainfall_7d_mm=150,
        slope_deg=22.5,
        soil_retention_score=0.5,
        historical_count_2km=2,
        sensor_adjustment=8,
    )

    result = compute_risk(data)

    assert result.base_score == 48.5
    assert result.final_score == 56.5
    assert result.category == "HIGH"


def test_inputs_are_clamped():
    data = RiskInput(
        rainfall_7d_mm=1000,
        slope_deg=90,
        soil_retention_score=-1,
        historical_count_2km=100,
    )

    result = compute_risk(data)

    assert result.final_score == 100
    assert result.category == "SEVERE"


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "LOW"),
        (24.99, "LOW"),
        (25, "MODERATE"),
        (49.99, "MODERATE"),
        (50, "HIGH"),
        (74.99, "HIGH"),
        (75, "SEVERE"),
        (100, "SEVERE"),
    ],
)
def test_risk_categories(score, expected):
    assert get_risk_category(score) == expected