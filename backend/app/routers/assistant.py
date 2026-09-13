"""Chat-assistant endpoint that explains DRISHTI's own dashboard in plain language.

Scoped tightly to DRISHTI's own domain (risk score, factors, provenance badges,
map layers). If no LLM key is configured, or the call fails, falls back to a
small rule-based FAQ so the feature never looks broken in a demo with no
internet or no key — it never blocks the rest of the app either way.
"""

import json

import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/assistant", tags=["assistant"])

SYSTEM_PROMPT = (
    "You are the DRISHTI dashboard assistant. Only answer questions about DRISHTI's "
    "own risk score, its four weighted factors (rainfall 40%, slope 25%, soil retention "
    "20%, historical events 15%), its category thresholds (LOW 0-24, MODERATE 25-49, "
    "HIGH 50-74, SEVERE 75-100), its SENSOR vs EXTERNAL data-source badges, its scenario "
    "simulator, or its map layers and basemaps. If asked about anything else, briefly say "
    "this assistant only explains the DRISHTI dashboard. Keep answers under 60 words. "
    "Use only the structured context supplied with the question. Never invent a number. "
    "If the context does not support an answer, explicitly say that the data is unavailable."
)

FAQ = [
    (["risk score", "score mean", "0 to 100", "0-100"],
     "The risk score (0-100) is a deterministic sum of four weighted factors -- rainfall "
     "(40%), slope (25%), soil retention (20%), and nearby historical events (15%) -- plus "
     "any live sensor adjustment. It's a decision-support indicator, not a prediction."),
    (["category", "low moderate high severe", "threshold"],
     "Score bands: LOW 0-24, MODERATE 25-49, HIGH 50-74, SEVERE 75-100 -- fixed cutoffs "
     "chosen for actionability, not evidence of a sharp jump in actual risk at the boundary."),
    (["sensor", "hardware", "simulated"],
     "The SENSOR badge means the value comes from DRISHTI's own ground-node pipeline. That "
     "pipeline is currently fed by a simulator explicitly labeled SIMULATED -- real hardware "
     "can be swapped in without changing the pipeline."),
    (["external", "source", "where does the data come from"],
     "The EXTERNAL badge names the real third-party API behind a value -- Open-Meteo for "
     "rainfall, OpenTopography COP30 for slope/elevation, or OSM for infrastructure."),
    (["scenario", "what if", "simulator"],
     "The scenario simulator recomputes the same live formula with hypothetical inputs so "
     "officials can explore preparedness scenarios. It never overwrites the live score."),
    (["ml zone", "machine learning", "ai"],
     "DRISHTI's core score is a deterministic formula, not a trained ML model. Any 'ML risk "
     "zone' map layer is an interpolation across nearby point scores, not a spatial model."),
]


class AssistantRequest(BaseModel):
    question: str
    context: dict | None = None


def local_answer(question: str) -> str:
    lowered = question.lower()
    for keywords, answer in FAQ:
        if any(k in lowered for k in keywords):
            return answer
    return (
        "I can help explain DRISHTI's risk score, factors, sensor vs. external data "
        "badges, the scenario simulator, or the map layers -- try asking about one of those."
    )


@router.post("/ask")
def ask(payload: AssistantRequest):
    api_key = settings.llm_api_key

    if not api_key:
        return {"answer": local_answer(payload.question), "source": "local_faq"}

    try:
        context_text = json.dumps(payload.context or {}, default=str)[:12000]
        user_text = f"Structured DRISHTI context:\n{context_text}\n\nQuestion: {payload.question}"
        if settings.llm_provider.lower() == "openai":
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_text}], "max_tokens": 200},
                timeout=8.0,
            )
            response.raise_for_status()
            return {"answer": response.json()["choices"][0]["message"]["content"], "source": "llm"}
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 200,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=8.0,
        )
        response.raise_for_status()
        data = response.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        ).strip()
        return {"answer": text or local_answer(payload.question), "source": "llm"}
    except Exception:
        return {"answer": local_answer(payload.question), "source": "local_faq_fallback"}
