from dataclasses import dataclass


@dataclass
class RiskInput:
    rainfall_7d_mm: float
    slope_deg: float
    soil_retention_score: float
    historical_count_2km: int
    sensor_adjustment: float = 0.0
    rainfall_available: bool = True


@dataclass
class RiskFactor:
    name: str
    raw_value: float
    normalized_value: float
    weight: float
    contribution: float


@dataclass
class RiskResult:
    base_score: float
    sensor_adjustment: float
    final_score: float
    category: str
    factors: list[RiskFactor]


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(value, maximum))


def get_risk_category(score: float) -> str:
    if score < 25:
        return "LOW"
    if score < 50:
        return "MODERATE"
    if score < 75:
        return "HIGH"
    return "SEVERE"


def compute_risk(data: RiskInput) -> RiskResult:
    rainfall_norm = clamp(data.rainfall_7d_mm / 300.0)
    slope_norm = clamp(data.slope_deg / 45.0)
    soil_norm = clamp(1.0 - data.soil_retention_score)
    history_norm = clamp(data.historical_count_2km / 5.0)

    # If rainfall is missing, remove its weight and renormalize the remaining
    # evidence to 100%. Missing rainfall must never be interpreted as 0 mm.
    base_weights = {
        "rainfall": 0.40 if data.rainfall_available else 0.0,
        "slope": 0.25,
        "soil": 0.20,
        "history": 0.15,
    }
    active_weight_total = sum(base_weights.values())
    effective_weights = {
        name: weight / active_weight_total
        for name, weight in base_weights.items()
    }

    raw_factors = [
        ("rainfall", data.rainfall_7d_mm, rainfall_norm),
        ("slope", data.slope_deg, slope_norm),
        ("soil", data.soil_retention_score, soil_norm),
        ("history", float(data.historical_count_2km), history_norm),
    ]

    factors = [
        RiskFactor(
            name=name,
            raw_value=raw_value,
            normalized_value=normalized_value,
            weight=effective_weights[name],
            contribution=normalized_value * effective_weights[name] * 100,
        )
        for name, raw_value, normalized_value in raw_factors
    ]

    base_score = clamp(sum(factor.contribution for factor in factors), 0.0, 100.0)
    final_score = clamp(base_score + data.sensor_adjustment, 0.0, 100.0)

    return RiskResult(
        base_score=round(base_score, 2),
        sensor_adjustment=round(data.sensor_adjustment, 2),
        final_score=round(final_score, 2),
        category=get_risk_category(final_score),
        factors=[
            RiskFactor(
                name=factor.name,
                raw_value=round(factor.raw_value, 2),
                normalized_value=round(factor.normalized_value, 4),
                weight=round(factor.weight, 6),
                contribution=round(factor.contribution, 2),
            )
            for factor in factors
        ],
    )
