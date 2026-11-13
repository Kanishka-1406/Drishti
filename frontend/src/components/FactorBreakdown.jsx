import ProvenanceChip from "./ProvenanceChip";

function formatFactorName(name) {
  return name
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}

// Each risk factor traces to exactly one named source — no factor is a black box.
const FACTOR_PROVENANCE = {
  rainfall: { source: "Open-Meteo", kind: "external" },
  slope: { source: "OpenTopography COP30", kind: "external" },
  soil: { source: "Seeded baseline", kind: "external" },
  history: { source: "GSI record", kind: "external" },
};


function FactorBreakdown({ factors, demo = false }) {
  if (!factors?.length) {
    return null;
  }

  const orderedFactors = [...factors].sort(
    (a, b) =>
      b.contribution - a.contribution
  );

  return (
    <section className="card">
      <div className="section-header">
        <div>
          <div className="eyebrow">
            EXPLAINABILITY
          </div>

          <h2>
            What contributes to this score?
          </h2>
        </div>
      </div>

      <div className="factor-list">
        {orderedFactors.map((factor) => (
          <div
            className="factor-row"
            key={factor.name}
          >
            <div>
              <div className="factor-name">
                {formatFactorName(
                  factor.name
                )}
                {demo ? <ProvenanceChip source="Scenario data" kind="sensor" status="SIMULATED" /> : FACTOR_PROVENANCE[factor.name] && (
                  <ProvenanceChip
                    source={FACTOR_PROVENANCE[factor.name].source}
                    kind={FACTOR_PROVENANCE[factor.name].kind}
                  />
                )}
              </div>

              <div className="factor-meta">
                Weight{" "}
                {Math.round(
                  factor.weight * 100
                )}
                %
              </div>
            </div>

            <div className="factor-value">
              +{factor.contribution.toFixed(1)}
            </div>
            <div className="factor-track"><i style={{ width: `${Math.min(100, factor.normalized_value * 100)}%` }} /></div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default FactorBreakdown;
