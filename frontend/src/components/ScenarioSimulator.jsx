import { useCallback, useEffect, useRef, useState } from "react";
import { simulateScenario } from "../services/api";

function SliderField({ label, value, min, max, step, unit = "", onChange }) {
  return (
    <div className="scenario-field">
      <div className="scenario-field-top">
        <label>{label}</label>
        <strong>{value}{unit}</strong>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <div className="scenario-range">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

function getBaseline(currentRisk) {
  const data = currentRisk?.data;
  if (!data) return null;

  const rainfall = data.rainfall?.rainfall_7d_mm;
  const slope = data.slope_deg;
  const soil = data.soil_retention_score;
  const history = data.historical_count_2km;

  // Keep the API's actual baseline values. Do not silently replace missing
  // terrain/history values with fabricated numbers.
  if ([rainfall, slope, soil, history].some((value) => value == null || !Number.isFinite(Number(value)))) {
    return null;
  }

  return {
    rainfall: Number(Number(rainfall).toFixed(1)),
    slope: Number(Number(slope).toFixed(1)),
    soilRetention: Number(Number(soil).toFixed(2)),
    historicalCount: Number(history),
  };
}

function ScenarioSimulator({ regionId, currentRisk }) {
  const [rainfall, setRainfall] = useState(0);
  const [slope, setSlope] = useState(0);
  const [soilRetention, setSoilRetention] = useState(0.5);
  const [historicalCount, setHistoricalCount] = useState(0);
  const [scenarioResult, setScenarioResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestSequence = useRef(0);

  const baseline = getBaseline(currentRisk);
  const rainfallSource = currentRisk?.data?.rainfall;
  const rainfallIsObserved = Boolean(rainfallSource?.fetched_at);
  const isDemo = Boolean(currentRisk?.demo);

  useEffect(() => {
    requestSequence.current += 1;
    setScenarioResult(null);
    setError(null);
    setLoading(false);

    const next = getBaseline(currentRisk);
    if (!next) return;

    setRainfall(next.rainfall);
    setSlope(next.slope);
    setSoilRetention(next.soilRetention);
    setHistoricalCount(next.historicalCount);
  }, [regionId, currentRisk]);

  const runScenario = useCallback(async () => {
    if (!regionId || !baseline) {
      setError("A complete regional baseline is required before simulation.");
      return;
    }

    const requestId = ++requestSequence.current;
    setLoading(true);
    setError(null);

    try {
      const result = await simulateScenario({
        region_id: regionId,
        rainfall_mm: rainfall,
        slope_deg: slope,
        soil_retention_score: soilRetention,
        historical_count_2km: historicalCount,
        // No live sensor adjustment is injected into a hypothetical scenario.
        sensor_adjustment: 0,
      });

      // Ignore a slower response if a newer scenario has already completed.
      if (requestId === requestSequence.current) {
        setScenarioResult(result);
      }
    } catch (err) {
      console.error("DRISHTI scenario simulation failed:", err);
      if (requestId === requestSequence.current) {
        setError(err.response?.data?.detail || "Unable to simulate this scenario. Check the API connection and input values.");
        setScenarioResult(null);
      }
    } finally {
      if (requestId === requestSequence.current) {
        setLoading(false);
      }
    }
  }, [regionId, baseline, rainfall, slope, soilRetention, historicalCount]);

  function resetScenario() {
    const next = getBaseline(currentRisk);
    requestSequence.current += 1;
    setLoading(false);
    setError(null);
    setScenarioResult(null);
    if (!next) return;
    setRainfall(next.rainfall);
    setSlope(next.slope);
    setSoilRetention(next.soilRetention);
    setHistoricalCount(next.historicalCount);
  }

  if (!currentRisk) return null;

  const delta = scenarioResult
    ? Number(scenarioResult.risk_score - currentRisk.risk_score).toFixed(1)
    : null;

  return (
    <section className="card scenario-card">
      <div className="scenario-header">
        <div>
          <div className="eyebrow">SCENARIO EXPLORATION</div>
          <h2>What if conditions change?</h2>
          <p>Change the regional baseline inputs and compare the deterministic assessment. Current observations are not overwritten.</p>
        </div>
        <div className="scenario-warning">Exploratory — not a forecast</div>
      </div>

      {!baseline && (
        <div className="scenario-error">
          Regional terrain, rainfall, soil and historical inputs are incomplete. A scenario cannot be calculated until the baseline is available.
        </div>
      )}

      {baseline && (
        <>
          <div className="scenario-source-note">
            {isDemo
              ? "SIMULATED BASELINE — demonstration values, not live observations."
              : rainfallIsObserved
                ? "BASELINE — rainfall observation timestamp is available."
                : "PARTIAL BASELINE — rainfall source has no stored observation timestamp. Treat the rainfall slider as a scenario assumption, not a live measurement."}
          </div>

          <div className="scenario-layout">
            <div className="scenario-controls">
              <SliderField label="7-day rainfall" value={rainfall} min={0} max={400} step={5} unit=" mm" onChange={setRainfall} />
              <SliderField label="Slope" value={slope} min={0} max={60} step={0.5} unit="°" onChange={setSlope} />
              <SliderField label="Soil retention" value={soilRetention} min={0} max={1} step={0.05} onChange={setSoilRetention} />
              <SliderField label="Historical events within 2 km" value={historicalCount} min={0} max={10} step={1} onChange={setHistoricalCount} />

              <div className="scenario-actions">
                <button className="primary-button" type="button" onClick={runScenario} disabled={loading || !baseline}>
                  {loading ? "Simulating..." : "Run Scenario"}
                </button>
                <button className="secondary-button" type="button" onClick={resetScenario} disabled={loading}>
                  Reset
                </button>
              </div>

              {error && <div className="scenario-error">{error}</div>}
            </div>

            <div className="scenario-results">
              <div className="comparison-grid">
                <div className="comparison-box">
                  <span>CURRENT</span>
                  <strong>{currentRisk.risk_score}</strong>
                  <div>{currentRisk.risk_category}</div>
                </div>
                <div className="comparison-arrow">→</div>
                <div className="comparison-box scenario">
                  <span>SCENARIO</span>
                  <strong>{scenarioResult ? scenarioResult.risk_score : "—"}</strong>
                  <div>{scenarioResult ? scenarioResult.risk_category : "Run simulation"}</div>
                </div>
              </div>

              {scenarioResult && (
                <>
                  <div className={Number(delta) > 0 ? "scenario-delta increase" : Number(delta) < 0 ? "scenario-delta decrease" : "scenario-delta"}>
                    {Number(delta) > 0 ? "+" : ""}{delta} points from current
                  </div>
                  <div className="scenario-factors">
                    <div className="scenario-factor-title">Scenario contributions</div>
                    {(scenarioResult.factors || []).map((factor) => (
                      <div className="scenario-factor-row" key={factor.name}>
                        <span>{factor.name}</span>
                        <strong>{Number(factor.contribution).toFixed(1)}</strong>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </>
      )}

      <div className="scenario-disclaimer">
        Scenario values are user-defined exploratory conditions. They are not observed conditions and do not constitute a landslide forecast or prediction.
      </div>
    </section>
  );
}

export default ScenarioSimulator;
