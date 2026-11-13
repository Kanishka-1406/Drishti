import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
  timeout: 10000,
});

export async function fetchRegions() {
  const response = await api.get("/regions");
  return response.data;
}

export async function fetchRisk(regionId) {
  const response = await api.get("/risk", { params: { region_id: regionId } });
  return response.data;
}

export async function fetchHistorical(regionId) {
  const response = await api.get("/historical", { params: { region_id: regionId } });
  return response.data;
}

export async function fetchInfrastructure(regionId) {
  const response = await api.get("/infrastructure", { params: { region_id: regionId } });
  return response.data;
}

export async function simulateScenario(payload) {
  const response = await api.post("/scenarios/simulate", payload);
  return response.data;
}

export async function fetchMapBootstrap() {
  const response = await api.get("/map/bootstrap");
  return response.data;
}

export default api;
