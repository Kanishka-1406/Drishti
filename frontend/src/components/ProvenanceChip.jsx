// Small badge that answers, at a glance, the single question every judge asks:
// "is this number coming from your own hardware, or from an external feed?"
//
// kind: "sensor"   -> came from DRISHTI's own sensor_readings pipeline (hardware or its
//                      simulator stand-in, clearly labeled by the caller via `source`)
// kind: "external" -> came from a named third-party API (Open-Meteo, OpenTopography, OSM, etc.)

function ProvenanceChip({ source, kind = "external", status }) {
  if (!source) return null;
  const label = status || (kind === "sensor" ? `SENSOR · ${source}` : `EXTERNAL · ${source}`);

  return (
    <span className={`provenance-chip ${kind === "sensor" ? "sensor" : "external"}`} title={
      kind === "sensor"
        ? "From DRISHTI's own sensor/hardware ingestion pipeline."
        : "From a named external data provider, not project hardware."
    }>
      {label}
    </span>
  );
}

export default ProvenanceChip;
