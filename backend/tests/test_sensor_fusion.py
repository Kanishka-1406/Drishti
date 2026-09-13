from app.services.sensor_fusion import compute_soil_saturation_index, modulate_soil_retention, normalize_percent


def test_normalize_percent_clamps_sensor_values():
    assert normalize_percent(-5) == 0
    assert normalize_percent(65) == 0.65
    assert normalize_percent(180) == 1


def test_saturation_weights_soil_and_recent_rain():
    result = compute_soil_saturation_index([70, 80], [20, 40])
    assert result == 0.615


def test_saturation_handles_one_available_signal():
    assert compute_soil_saturation_index([60], []) == 0.6
    assert compute_soil_saturation_index([], [30]) == 0.3
    assert compute_soil_saturation_index([], []) is None


def test_live_saturation_reduces_retention():
    assert modulate_soil_retention(0.5, 0.6) == 0.2
    assert modulate_soil_retention(0.5, None) == 0.5
