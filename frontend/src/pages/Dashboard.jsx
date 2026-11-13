import { useEffect, useState } from "react";

import RegionSelector from "../components/RegionSelector";
import RiskCard from "../components/RiskCard";
import FactorBreakdown from "../components/FactorBreakdown";
import MapView from "./MapView";
import ScenarioSimulator from "../components/ScenarioSimulator";
import LiveSensorCard from "../components/LiveSensorCard";
import HardwareSetupPanel from "../components/HardwareSetupPanel";

import {
  fetchRegions,
  fetchRisk,
  fetchInfrastructure,
} from "../services/api";
import ProvenanceChip from "../components/ProvenanceChip";

const DEMO_REGIONS = [
  { id: 101, name: "Gangtok · Demo", center_lat: 27.3389, center_lon: 88.6138, default_zoom: 10, demo: true },
  { id: 102, name: "Aizawl · Demo", center_lat: 23.7271, center_lon: 92.7176, default_zoom: 10, demo: true },
  { id: 103, name: "Joshimath · Demo", center_lat: 30.5554, center_lon: 79.5664, default_zoom: 10, demo: true },
  { id: 104, name: "Mandi · Demo", center_lat: 31.708, center_lon: 76.9314, default_zoom: 10, demo: true },
  { id: 105, name: "Idukki · Demo", center_lat: 9.9189, center_lon: 77.1025, default_zoom: 10, demo: true },
];
const demoRisk = (id) => {
  const values = {101:[68,82,31,.38,3],102:[64,91,33,.42,2],103:[57,34,35,.48,4],104:[53,47,28,.5,2],105:[48,105,24,.44,2]}[id] || [45,60,25,.5,1];
  const [score,rain,slope,soil,history]=values;
  return {region_id:id,risk_score:score,base_score:score,sensor_adjustment:0,risk_category:score>=75?"SEVERE":score>=50?"HIGH":score>=25?"MODERATE":"LOW",demo:true,factors:[{name:"rainfall",raw_value:rain,normalized_value:Math.min(rain/300,1),weight:.4,contribution:Math.min(rain/300,1)*40},{name:"slope",raw_value:slope,normalized_value:Math.min(slope/45,1),weight:.25,contribution:Math.min(slope/45,1)*25},{name:"soil",raw_value:soil,normalized_value:1-soil,weight:.2,contribution:(1-soil)*20},{name:"history",raw_value:history,normalized_value:Math.min(history/5,1),weight:.15,contribution:Math.min(history/5,1)*15}],data:{rainfall:{rainfall_7d_mm:rain,source:"simulated"},slope_deg:slope,soil_retention_score:soil,historical_count_2km:history},sensor:{node_id:null,state:"NO_NODE"}};
};


function Dashboard({ onContext }) {
  const [regions, setRegions] = useState([]);
  const [
    selectedRegionId,
    setSelectedRegionId,
  ] = useState(null);

  const [risk, setRisk] = useState(null);
  const [infrastructure, setInfrastructure] = useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(null);


  useEffect(() => {
    async function loadRegions() {
      try {
        const data = await fetchRegions();

        setRegions([...data, ...DEMO_REGIONS]);

        if (data.length > 0) {
          setSelectedRegionId(
            data[0].id
          );
        }
      } catch (err) {
        console.error(err);

        setError(
          "Unable to load regions."
        );
      }
    }

    loadRegions();
  }, []);


  useEffect(() => {
    if (!selectedRegionId) {
      return;
    }

    async function loadRisk() {
      setLoading(true);
      setError(null);

      try {
        if (selectedRegionId >= 100) {
          setRisk(demoRisk(selectedRegionId)); setInfrastructure(null); setLoading(false); return;
        }
        const [riskResult, infraResult] = await Promise.allSettled([fetchRisk(selectedRegionId), fetchInfrastructure(selectedRegionId)]);
        if (riskResult.status === "rejected") throw riskResult.reason;
        setRisk(riskResult.value);
        setInfrastructure(infraResult.status === "fulfilled" ? infraResult.value : null);
      } catch (err) {
        console.error(err);

        setError(
          "Unable to load risk assessment."
        );
      } finally {
        setLoading(false);
      }
    }

    loadRisk();
  }, [selectedRegionId]);

  const selectedRegion = regions.find(
  (region) =>
    region.id === selectedRegionId
  );
  useEffect(() => {
    onContext?.({ region: selectedRegion, risk, infrastructure });
  }, [selectedRegion, risk, infrastructure, onContext]);


  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">
            DRISHTI
          </div>

          <div className="tagline">
            See the Risk. Act Before.
          </div>
        </div>

        <div className="system-pill">
          DECISION SUPPORT
        </div>
      </header>

      <section className="dashboard-header">
        <div>
          <div className="eyebrow">
            LANDSLIDE RISK INTELLIGENCE
          </div>

          <h1>
            Terrain & Environmental
            Risk Overview
          </h1>

          <p>
            Transparent contextual risk
            assessment using environmental,
            terrain and historical factors.
          </p>
        </div>

        <RegionSelector
          regions={regions}
          selectedRegionId={
            selectedRegionId
          }
          onChange={
            setSelectedRegionId
          }
        />
      </section>

      {loading && (
        <div className="status-card">
          Loading assessment...
        </div>
      )}

      {error && (
        <div className="error-card">
          {error}
        </div>
      )}

      {!loading && !error && risk && (
        <>
         <div className="dashboard-grid">
          <RiskCard risk={risk} />

          <FactorBreakdown
            factors={risk.factors} demo={risk.demo}
          />
          <section className="card operations-card">
            <div className="eyebrow">REAL-TIME SIGNALS</div>
            <h2>{risk.data?.rainfall?.fetched_at ? `${risk.data.rainfall.rainfall_7d_mm} mm over 7 days` : "Rainfall unavailable"}</h2>
            <p>{risk.data?.rainfall?.fetched_at ? `Open-Meteo observation fetched ${new Date(risk.data.rainfall.fetched_at).toLocaleString()}.` : "No current Open-Meteo record is available. No substitute value is shown."}</p>
            <ProvenanceChip source="Open-Meteo" />
          </section>
          <section className="card operations-card">
            <div className="eyebrow">INFRASTRUCTURE & EXPOSURE</div>
            <h2>{infrastructure ? `${infrastructure.count} mapped response assets` : "Infrastructure unavailable"}</h2>
            <p>{infrastructure ? Object.entries(infrastructure.category_counts || {}).map(([key, value]) => `${value} ${key.replaceAll("_", " ")}`).join(" · ") || "No assets returned for this region." : "The OpenStreetMap infrastructure request did not return data."}</p>
            <ProvenanceChip source="OpenStreetMap" />
          </section>
          <section className="card operations-card response-review">
            <div className="eyebrow">RESPONSE / EVACUATION REVIEW</div>
            <h2>{infrastructure?.count ? "Review routes against mapped facilities" : "Awaiting local asset context"}</h2>
            <p>{infrastructure?.count ? "Use the map to verify hospitals, police, fire stations and schools before selecting an evacuation corridor." : "No route is recommended without verified infrastructure records and field confirmation."}</p>
          </section>
         </div>

         <MapView
          region={selectedRegion}
         />

         <ScenarioSimulator
           regionId={selectedRegionId}
           currentRisk={risk}
         />
         <HardwareSetupPanel nodeId={risk.sensor?.node_id || "drishti-node-01"} />
         <LiveSensorCard nodeId={risk.sensor?.node_id || "drishti-node-01"} />
        </>
      )}
    </main>
  );
}

export default Dashboard;
