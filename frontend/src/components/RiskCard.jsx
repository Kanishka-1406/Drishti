import ProvenanceChip from "./ProvenanceChip";

function RiskCard({ risk }) {
  if (!risk) {
    return null;
  }

  // The overall score blends live external factors with any active sensor adjustment —
  // show both provenance chips when a sensor adjustment is actually contributing.
  const hasSensorAdjustment = !!risk.sensor_adjustment;

  return (
    <section className="risk-card">
      <div className="eyebrow">
        CURRENT CONTEXTUAL RISK
        {risk.demo ? <ProvenanceChip source="Scenario data" kind="sensor" status="SIMULATED" /> : <ProvenanceChip source="Open-Meteo + OpenTopography" kind="external" />}
        {hasSensorAdjustment && <ProvenanceChip source="Ground Node" kind="sensor" />}
      </div>

      <div className="risk-score-row">
        <div className="risk-gauge" style={{ "--score": risk.risk_score }}><div><strong>{risk.risk_score}</strong><small>RISK INDEX</small></div></div>

        <div>
          <div className="risk-out-of">
            / 100
          </div>

          <div
            className={`risk-category category-${risk.risk_category.toLowerCase()}`}
          >
            {risk.risk_category}
          </div>
        </div>
      </div>

      <p className="risk-note">
        Explainable decision-support indicator.
        Not a landslide prediction.
      </p>
      <details className="score-explainer">
        <summary>Explain this score</summary>
        <p>Score = rainfall × 40% + slope × 25% + soil saturation × 20% + nearby history × 15%, after each signal is normalized from 0–1. A verified ground-node anomaly is then added and the result is capped at 100.</p>
      </details>
    </section>
  );
}

export default RiskCard;
