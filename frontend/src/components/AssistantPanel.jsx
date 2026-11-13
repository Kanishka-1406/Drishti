import { useState } from "react";
import api from "../services/api";

// Local rule-based FAQ so the assistant never looks broken in a demo with no
// internet or no LLM key configured on the backend. Keep this tightly scoped
// to DRISHTI's own domain — it is a dashboard explainer, not a general chatbot.
const FAQ = [
  { q: ["risk score", "what does the score mean", "0 to 100"], a: "The risk score (0–100) is a deterministic sum of four weighted factors — rainfall (40%), slope (25%), soil retention (20%), and nearby historical events (15%) — plus any live sensor adjustment. It is a decision-support indicator, not a landslide prediction." },
  { q: ["category", "low moderate high severe", "thresholds"], a: "Score bands: LOW 0–24, MODERATE 25–49, HIGH 50–74, SEVERE 75–100. These are fixed cutoffs chosen for actionability, not a claim that risk changes discontinuously at the boundary." },
  { q: ["sensor", "hardware", "simulated"], a: "The 'SENSOR' badge means the value comes from DRISHTI's own ground-node pipeline. Right now that pipeline is fed by a simulator clearly labeled 'SIMULATED' in the code and UI — real hardware can be swapped in without changing the pipeline." },
  { q: ["external", "source", "where does the data come from"], a: "The 'EXTERNAL' badge names the real third-party API behind a value — Open-Meteo for rainfall, OpenTopography COP30 for slope/elevation, or OSM for infrastructure. Nothing is fabricated; unavailable sources are marked as such rather than filled in." },
  { q: ["scenario", "what if", "simulator"], a: "The scenario simulator recomputes the same live risk formula with hypothetical inputs (e.g., +50mm rainfall) so officials can explore preparedness scenarios. It never overwrites the live score." },
  { q: ["ml zone", "machine learning", "ai"], a: "The operational score is currently deterministic and explainable. A trained ML factor is not shown until a sufficiently large, validated training dataset and held-out metrics are available." },
  { q: ["historical", "past landslide", "accident"], a: "Historical markers show verified past landslide events (e.g., GSI-sourced records) plotted as diamonds, distinct from live risk hotspots shown as circles." },
  { q: ["boundary", "map of india", "official"], a: "The interactive basemap is OpenStreetMap/CARTO/ESRI tiles for visual context. The authoritative India boundary reference is the Survey of India Political Map, linked directly in the map's official-reference panel — we don't relabel a third-party boundary as the government one." },
  { q: ["theme", "dark mode", "light mode"], a: "DRISHTI uses one command-center theme so status and risk colors remain consistent during operations." },
  { q: ["global", "other countries", "outside india"], a: "This deployment is scoped to configured Indian regions and uses a linked Survey of India political-map reference." },
];

function localAnswer(question) {
  const lower = question.toLowerCase();
  const hit = FAQ.find((entry) => entry.q.some((kw) => lower.includes(kw)));
  return hit
    ? hit.a
    : "I can help explain DRISHTI's risk score, factors, sensor vs. external data badges, the scenario simulator, or the map layers — try asking about one of those.";
}

const SUGGESTIONS = ["What does the risk score mean?", "Is this sensor data real?", "What sources feed this map?"];

export default function AssistantPanel({ context = {} }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi, I'm the DRISHTI assistant. Ask me what any score, badge, or layer on this dashboard means." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send(question) {
    const q = question.trim();
    if (!q || busy) return;

    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);

    try {
      // Try the backend LLM-backed endpoint first; fall back to the local FAQ
      // immediately if it's not configured/reachable, so the demo never breaks.
      const { data } = await api.post("/assistant/ask", { question: q, context });
      setMessages((m) => [...m, { role: "bot", text: data.answer || localAnswer(q) }]);
    } catch {
      setMessages((m) => [...m, { role: "bot", text: localAnswer(q) }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {open && (
        <div className="assistant-panel">
          <header>
            <strong>DRISHTI Assistant</strong>
            <button onClick={() => setOpen(false)}>×</button>
          </header>
          <div className="assistant-messages">
            {messages.map((m, i) => (
              <div key={i} className={`assistant-msg ${m.role}`}>{m.text}</div>
            ))}
          </div>
          <div className="assistant-suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)}>{s}</button>
            ))}
          </div>
          <div className="assistant-input">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
              placeholder="Why is this region high risk?"
            />
            <button onClick={() => send(input)} disabled={busy}>Ask</button>
          </div>
        </div>
      )}
      <button className="assistant-bubble" onClick={() => setOpen((v) => !v)} aria-label="Open assistant">
        {open ? "×" : "💬"}
      </button>
    </>
  );
}
