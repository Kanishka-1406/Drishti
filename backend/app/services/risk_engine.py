from dataclasses import dataclass


@dataclass
class RiskInput:
    rainfall_7d_mm: float
    slope_deg: float
    soil_retention_score: float
    historical_count_2km: int
    sensor_adjustment: float = 0.0


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
    rainfall_norm = clamp(
        data.rainfall_7d_mm / 300.0
    )

    slope_norm = clamp(
        data.slope_deg / 45.0
    )

    soil_norm = clamp(
        1.0 - data.soil_retention_score
    )

    history_norm = clamp(
        data.historical_count_2km / 5.0
    )

    factors = [
        RiskFactor(
            name="rainfall",
            raw_value=data.rainfall_7d_mm,
            normalized_value=rainfall_norm,
            weight=0.40,
            contribution=rainfall_norm * 0.40 * 100,
        ),
        RiskFactor(
            name="slope",
            raw_value=data.slope_deg,
            normalized_value=slope_norm,
            weight=0.25,
            contribution=slope_norm * 0.25 * 100,
        ),
        RiskFactor(
            name="soil",
            raw_value=data.soil_retention_score,
            normalized_value=soil_norm,
            weight=0.20,
            contribution=soil_norm * 0.20 * 100,
        ),
        RiskFactor(
            name="history",
            raw_value=float(data.historical_count_2km),
            normalized_value=history_norm,
            weight=0.15,
            contribution=history_norm * 0.15 * 100,
        ),
    ]

    base_score = sum(
        factor.contribution
        for factor in factors
    )

    base_score = clamp(
        base_score,
        0.0,
        100.0,
    )

    final_score = clamp(
        base_score + data.sensor_adjustment,
        0.0,
        100.0,
    )

    category = get_risk_category(
        final_score
    )

    return RiskResult(
        base_score=round(base_score, 2),
        sensor_adjustment=round(
            data.sensor_adjustment,
            2,
        ),
        final_score=round(final_score, 2),
        category=category,
        factors=[
            RiskFactor(
                name=factor.name,
                raw_value=round(
                    factor.raw_value,
                    2,
                ),
                normalized_value=round(
                    factor.normalized_value,
                    4,
                ),
                weight=factor.weight,
                contribution=round(
                    factor.contribution,
                    2,
                ),
            )
            for factor in factors
        ],
    )