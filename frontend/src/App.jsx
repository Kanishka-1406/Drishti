import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import IndiaExplorer from "./pages/IndiaExplorer";
import AssistantPanel from "./components/AssistantPanel";
import "./index.css";

const nav = [
  ["overview", "Overview", "⌂"],
  ["explorer", "India Explorer", "◫"],
  ["scenario", "Scenario Simulator", "◎"],
  ["sources", "Data Sources", "◉"],
];

function ComingSoon({ title }) {
  return (
    <div className="coming-soon">
      <span>DRISHTI WORKSPACE</span>
      <h2>{title}</h2>
      <p>This module is connected to the same terrain-intelligence workspace and will be expanded in the next pass.</p>
    </div>
  );
}

const sources = [
  ["Open-Meteo", "SATELLITE/API", "Rainfall observations · timestamp shown with each assessment"],
  ["OpenTopography", "SATELLITE/API", "Terrain ingestion · unavailable when no stored fetch exists"],
  ["OpenStreetMap / Overpass", "SATELLITE/API", "Hospitals, schools, police and fire stations"],
  ["GSI Bhusanket", "HISTORICAL", "Attributed historical landslide records"],
  ["ESP32 ground node", "LIVE SENSOR", "Live only after an authenticated device reading"],
  ["Scenario engine", "SIMULATED", "Planning values never overwrite the current assessment"],
];

function DataSources() {
  return <div className="sources-page"><span className="eyebrow">DATA TRANSPARENCY</span><h1>Evidence register</h1><p>Every operational value must resolve to a named source, a stored timestamp, or an unavailable state.</p><div className="source-register">{sources.map(([name,status,note])=><article key={name}><b>{name}</b><span>{status}</span><small>{note}</small></article>)}</div></div>;
}

export default function App() {
  const [activePage, setActivePage] = useState("explorer");
  const [assistantContext, setAssistantContext] = useState({});

  return (
    <div className="drishti-shell">
      <aside className="side-rail">
        <div>
          <div className="brand-block">
            <div className="brand-mark">⌃</div>
            <div>
              <strong>DRISHTI</strong>
              <small>TERRAIN INTELLIGENCE</small>
              <em>See the Risk. Act Before.</em>
            </div>
          </div>

          <nav className="rail-nav">
            {nav.map(([id, label, icon]) => (
              <button key={id} className={activePage === id ? "active" : ""} onClick={() => setActivePage(id)}>
                <span>{icon}</span>{label}
              </button>
            ))}
          </nav>

        </div>

        <div className="rail-footer">
          <blockquote>“A safer tomorrow is a more resilient India.”</blockquote>
          <div className="india-signoff"><span>🇮🇳</span><small>Built for a safer, stronger India</small></div>
        </div>
      </aside>

      <main className="main-stage">
        {activePage === "explorer" && <IndiaExplorer onContext={setAssistantContext} />}
        {(activePage === "overview" || activePage === "scenario") && <Dashboard onContext={setAssistantContext} />}
        {activePage === "sources" && <DataSources />}
        {!['explorer','overview','scenario','sources'].includes(activePage) && <ComingSoon title={nav.find(x => x[0] === activePage)?.[1]} />}
      </main>
      <AssistantPanel context={assistantContext} />

    </div>
  );
}
