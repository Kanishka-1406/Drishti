import { useEffect, useState } from "react";

import {
  simulateScenario,
} from "../services/api";


function SliderField({
  label,
  value,
  min,
  max,
  step,
  unit = "",
  onChange,
}) {
  return (
    <div className="scenario-field">
      <div className="scenario-field-top">
        <label>{label}</label>

        <strong>
          {value}
          {unit}
        </strong>
      </div>

      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) =>
          onChange(
            Number(event.target.value)
          )
        }
      />

      <div className="scenario-range">
        <span>
          {min}
          {unit}
        </span>

        <span>
          {max}
          {unit}
        </span>
      </div>
    </div>
  );
}


function ScenarioSimulator({
  regionId,
  currentRisk,
}) {
  const [rainfall, setRainfall] =
    useState(0);

  const [slope, setSlope] =
    useState(0);

  const [
    soilRetention,
    setSoilRetention,
  ] = useState(0.5);

  const [
    historicalCount,
    setHistoricalCount,
  ] = useState(0);

  const [
    scenarioResult,
    setScenarioResult,
  ] = useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);


  useEffect(() => {
    if (!currentRisk?.data) {
      return;
    }

    const rainfallValue =
      currentRisk.data.rainfall
        ?.rainfall_7d_mm ?? 0;

    setRainfall(
      Number(
        Number(rainfallValue).toFixed(1)
      )
    );

    setSlope(
      Number(
        Number(
          currentRisk.data.slope_deg ?? 0
        ).toFixed(1)
      )
    );

    setSoilRetention(
      Number(
        Number(
          currentRisk.data
            .soil_retention_score ?? 0.5
        ).toFixed(2)
      )
    );

    setHistoricalCount(
      Number(
        currentRisk.data
          .historical_count_2km ?? 0
      )
    );

    setScenarioResult(null);
  }, [currentRisk]);


  async function runScenario() {
    if (!regionId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log("SCENARIO INPUTS:", {
        region_id: regionId,
        rainfall_mm: rainfall,
        slope_deg: slope,
        soil_retention_score: soilRetention,
        historical_count_2km: historicalCount,
        sensor_adjustment: 0,
      });

      const result =
        await simulateScenario({
          region_id: regionId,
          rainfall_mm: rainfall,
          slope_deg: slope,
          soil_retention_score:
            soilRetention,
          historical_count_2km:
            historicalCount,
          sensor_adjustment: 0,
        });

      setScenarioResult(result);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to simulate scenario."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!regionId || !currentRisk?.data) return;
    const timer = setTimeout(runScenario, 450);
    return () => clearTimeout(timer);
  }, [rainfall, slope, soilRetention, historicalCount, regionId]);


  function resetScenario() {
    if (!currentRisk?.data) {
      return;
    }

    setRainfall(
      Number(
        Number(
          currentRisk.data.rainfall
            ?.rainfall_7d_mm ?? 0
        ).toFixed(1)
      )
    );

    setSlope(
      Number(
        Number(
          currentRisk.data.slope_deg ?? 0
        ).toFixed(1)
      )
    );

    setSoilRetention(
      Number(
        Number(
          currentRisk.data
            .soil_retention_score ?? 0.5
        ).toFixed(2)
      )
    );

    setHistoricalCount(
      Number(
        currentRisk.data
          .historical_count_2km ?? 0
      )
    );

    setScenarioResult(null);
    setError(null);
  }


  if (!currentRisk) {
    return null;
  }

  const delta =
    scenarioResult
      ? (
          scenarioResult.risk_score -
          currentRisk.risk_score
        ).toFixed(1)
      : null;


  return (
    <section className="card scenario-card">
      <div className="scenario-header">
        <div>
          <div className="eyebrow">
            SCENARIO EXPLORATION
          </div>

          <h2>
            What if conditions change?
          </h2>

          <p>
            Modify environmental inputs and
            inspect how the deterministic
            risk indicator responds.
          </p>
        </div>

        <div className="scenario-warning">
          Exploratory — not a forecast
        </div>
      </div>

      <div className="scenario-layout">
        <div className="scenario-controls">
          <SliderField
            label="7-day rainfall"
            value={rainfall}
            min={0}
            max={400}
            step={5}
            unit=" mm"
            onChange={setRainfall}
          />

          <SliderField
            label="Slope"
            value={slope}
            min={0}
            max={60}
            step={0.5}
            unit="°"
            onChange={setSlope}
          />

          <SliderField
            label="Soil retention"
            value={soilRetention}
            min={0}
            max={1}
            step={0.05}
            onChange={setSoilRetention}
          />

          <SliderField
            label="Historical events within 2 km"
            value={historicalCount}
            min={0}
            max={10}
            step={1}
            onChange={setHistoricalCount}
          />

          <div className="scenario-actions">
            <button
              className="primary-button"
              type="button"
              onClick={runScenario}
              disabled={loading}
            >
              {loading
                ? "Simulating..."
                : "Run Scenario"}
            </button>

            <button
              className="secondary-button"
              type="button"
              onClick={resetScenario}
            >
              Reset
            </button>
          </div>

          {error && (
            <div className="scenario-error">
              {error}
            </div>
          )}
        </div>

        <div className="scenario-results">
          <div className="comparison-grid">
            <div className="comparison-box">
              <span>
                CURRENT
              </span>

              <strong>
                {currentRisk.risk_score}
              </strong>

              <div>
                {
                  currentRisk.risk_category
                }
              </div>
            </div>

            <div className="comparison-arrow">
              →
            </div>

            <div className="comparison-box scenario">
              <span>
                SCENARIO
              </span>

              <strong>
                {scenarioResult
                  ? scenarioResult.risk_score
                  : "—"}
              </strong>

              <div>
                {scenarioResult
                  ? scenarioResult.risk_category
                  : "Run simulation"}
              </div>
            </div>
          </div>

          {scenarioResult && (
            <>
              <div
                className={
                  Number(delta) > 0
                    ? "scenario-delta increase"
                    : Number(delta) < 0
                    ? "scenario-delta decrease"
                    : "scenario-delta"
                }
              >
                {Number(delta) > 0
                  ? "+"
                  : ""}
                {delta} points from current
              </div>

              <div className="scenario-factors">
                <div className="scenario-factor-title">
                  Scenario contributions
                </div>

                {scenarioResult.factors.map(
                  (factor) => (
                    <div
                      className="scenario-factor-row"
                      key={factor.name}
                    >
                      <span>
                        {factor.name}
                      </span>

                      <strong>
                        +
                        {Number(
                          factor.contribution
                        ).toFixed(1)}
                      </strong>
                    </div>
                  )
                )}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="scenario-disclaimer">
        Scenario values represent user-defined
        exploratory conditions. They are not
        observed conditions and do not constitute
        a landslide forecast or prediction.
      </div>
    </section>
  );
}

export default ScenarioSimulator;
