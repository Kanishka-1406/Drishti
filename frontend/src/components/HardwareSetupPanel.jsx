import { useEffect, useState } from "react";
import api from "../services/api";
import ProvenanceChip from "./ProvenanceChip";

export default function HardwareSetupPanel({ nodeId = "drishti-node-01" }) {
  const [node,setNode]=useState(null),[error,setError]=useState(null);
  useEffect(()=>{let active=true;const load=()=>api.get('/sensors').then(({data})=>{if(active){setNode(data.find(n=>n.node_id===nodeId)||null);setError(null)}}).catch(()=>active&&setError('Node registry unavailable'));load();const timer=setInterval(load,5000);return()=>{active=false;clearInterval(timer)}},[nodeId]);
  const host=window.location.hostname||'YOUR_LAPTOP_IP';
  return <section className="card hardware-setup-card"><div className="hardware-heading"><div><div className="eyebrow">PHYSICAL HARDWARE BRIDGE</div><h2>ESP32 ground station</h2><p>One authenticated packet enters the same anomaly engine, WebSocket, timeline and risk score used by this dashboard.</p></div><ProvenanceChip source={node?.online?"LIVE":"Awaiting ground node"} kind="sensor" status={node?.online?"SENSOR · LIVE":"OFFLINE / AWAITING DATA"}/></div>
  <div className="hardware-flow"><span>Soil + Rain + MPU6050</span><i>→</i><span>ESP32</span><i>→</i><span>POST /sensors/readings</span><i>→</i><span>Risk engine + WebSocket</span></div>
  <div className="hardware-grid"><div><small>NODE</small><strong>{nodeId}</strong></div><div><small>CONNECTION</small><strong className={node?.online?'live-text':''}>{node?.online?`Online · ${node.age_seconds}s ago`:'Offline'}</strong></div><div><small>PACKETS STORED</small><strong>{node?.packet_count??'—'}</strong></div><div><small>CALIBRATION</small><strong>{node?`${Number(node.baseline_tilt_x||0).toFixed(2)}° / ${Number(node.baseline_tilt_y||0).toFixed(2)}°`:'—'}</strong></div></div>
  <details className="hardware-guide"><summary>Connect the physical node</summary><ol><li>Open <code>firmware/drishti_node/drishti_node.ino</code> in Arduino IDE.</li><li>Set Wi-Fi name/password and set <code>API_URL</code> to <code>http://{host}:8000/sensors/readings</code>. If this page uses localhost, replace it with the laptop's Wi-Fi IPv4 address.</li><li>Wire MPU6050 SDA→GPIO21, SCL→GPIO22; soil analog→GPIO34; rain analog→GPIO35; rain digital→GPIO27.</li><li>Keep the node still during its two-second boot calibration, then open Serial Monitor at 115200 baud.</li></ol></details>{error&&<p className="hardware-error">{error}</p>}</section>;
}
