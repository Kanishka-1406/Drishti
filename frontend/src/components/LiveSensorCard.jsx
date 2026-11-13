import useSensorWebSocket from "../hooks/useSensorWebSocket";
import ProvenanceChip from "./ProvenanceChip";


function formatValue(value, digits = 2) {
  if (value === null || value === undefined) {
    return "—";
  }

  return Number(value).toFixed(digits);
}


function LiveSensorCard({ nodeId = "drishti-node-01" }) {
  const {
    reading,
    anomaly,
    sourceMode,
    connectionStatus,
    history,
  } = useSensorWebSocket(nodeId);


  return (
    <section className="card sensor-card">
      <div className="sensor-card-header">
        <div>
          <div className="eyebrow">
            GROUND NODE
          </div>

          <h2>
            DRISHTI Node 01
          </h2>
        </div>

        <ProvenanceChip source={sourceMode || "Awaiting ground node"} kind="sensor"
          status={sourceMode === "SIMULATED" ? "SIMULATED" : sourceMode === "LIVE" ? "SENSOR · LIVE" : sourceMode === "RECORDED" ? "SENSOR · RECORDED" : "OFFLINE / AWAITING DATA"} />

        <div
          className={
            connectionStatus === "connected"
              ? "sensor-status connected"
              : "sensor-status"
          }
        >
          {connectionStatus}
        </div>
      </div>


      <div className="sensor-source-row">
        <span>Signal source</span>

        <strong
          className={
            sourceMode === "SIMULATED"
              ? "source-simulated"
              : ""
          }
        >
          {sourceMode ?? "Awaiting ground node"}
        </strong>
      </div>


      {!reading ? (
        <div className="sensor-empty">
          Waiting for the next sensor reading...
        </div>
      ) : (
        <>
          <div className="sensor-metrics">
            <div className="sensor-metric">
              <span>Tilt magnitude</span>

              <strong>
                {formatValue(reading.tilt_magnitude)}°
              </strong>
            </div>


            <div className="sensor-metric">
              <span>Tilt X</span>

              <strong>
                {formatValue(reading.tilt_x)}°
              </strong>
            </div>


            <div className="sensor-metric">
              <span>Tilt Y</span>

              <strong>
                {formatValue(reading.tilt_y)}°
              </strong>
            </div>


            <div className="sensor-metric">
              <span>Soil signal</span>

              <strong>
                {formatValue(
                  reading.soil_moisture,
                  0
                )}
              </strong>
            </div>


            <div className="sensor-metric">
              <span>Rain signal</span>

              <strong>
                {formatValue(
                  reading.rain_wetness,
                  0
                )}
              </strong>
            </div>


            <div className="sensor-metric">
              <span>Battery</span>

              <strong>
                {reading.battery != null
                  ? formatValue(
                      reading.battery,
                      1
                    )
                  : "—"}
              </strong>
            </div>
          </div>


          {anomaly && (
            <div
              className={`anomaly-panel ${
                anomaly.state?.toLowerCase() ?? ""
              }`}
            >
              <div className="anomaly-top">
                <span>
                  Ground Movement State
                </span>

                <strong>
                  {anomaly.state}
                </strong>
              </div>


              <p>
                {anomaly.explanation}
              </p>


              <div className="anomaly-meta">
                <span>
                  Persistent high readings
                </span>

                <strong>
                  {anomaly.consecutive_high_readings ?? 0}/3
                </strong>
              </div>


              <div className="anomaly-meta">
                <span>
                  Risk adjustment
                </span>

                <strong>
                  {anomaly.sensor_adjustment > 0
                    ? `+${anomaly.sensor_adjustment}`
                    : "0"}
                </strong>
              </div>
            </div>
          )}


          <div className="sensor-timestamp">
            Last WebSocket update:{" "}
            {reading.recorded_at
              ? new Date(
                  reading.recorded_at
                ).toLocaleTimeString()
              : "—"}
          </div>
          <div className="sensor-timeline"><div className="eyebrow">RAW READING TIMELINE</div>{history.length ? history.slice().reverse().map((item,index)=><div className="timeline-reading" key={`${item.recorded_at}-${index}`}><time>{item.recorded_at ? new Date(item.recorded_at).toLocaleTimeString() : "now"}</time><span>Tilt {formatValue(item.tilt_magnitude)}°</span><span>Soil {formatValue(item.soil_moisture,0)}</span><b>{item.anomaly_state || "READING"}</b></div>) : <p>Timeline begins with the next live reading.</p>}</div>
        </>
      )}


      {sourceMode === "SIMULATED" && (
        <div className="simulation-notice">
          Development mode: simulated sensor input.
          This is not a physical measurement.
        </div>
      )}
    </section>
  );
}


export default LiveSensorCard;
