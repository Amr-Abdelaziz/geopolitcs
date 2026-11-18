"""Strategic OSIRIS - FastAPI Intelligence Fusion Backend.
Provides REST APIs for multi-agent strategic assessment execution,
evidence storage, Admiralty verification, early warning alerts, and human review gates.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from packages.prompts.registry import AGENT_REGISTRY, build_system_prompt
from packages.schemas.models import (
    AgentDefinition,
    AgentID,
    ApprovalAction,
    AssessmentRequest,
    DocumentEvidence,
    StrategicAssessment,
)
from services.orchestrator.pipeline import StrategicPipeline
from services.reporting.generator import ReportGenerator
from services.warning.indicator_engine import IndicatorEngine

app = FastAPI(
    title="Strategic OSIRIS (SIFP) Intelligence API",
    description="Multi-Agent Strategic Intelligence Fusion Platform for Defense and Geopolitics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = StrategicPipeline()
indicator_engine = IndicatorEngine()


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "online",
        "service": "Strategic OSIRIS Intelligence Fusion Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_count": len(AGENT_REGISTRY),
        "llm_mode": "mock_fallback" if pipeline.llm.mock_mode else "openrouter_live",
        "target_countries": ["Egypt", "Libya", "Israel"]
    }


# --- Agent Management ---

@app.get("/api/agents", response_model=List[AgentDefinition])
async def list_agents() -> List[AgentDefinition]:
    return list(AGENT_REGISTRY.values())


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    try:
        aid = AgentID(agent_id.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent ID not found")
    
    agent_def = AGENT_REGISTRY.get(aid)
    if not agent_def:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    
    sample_prompt = build_system_prompt(aid, "سؤال استراتيجي اختباري")
    return {
        "metadata": agent_def.model_dump(),
        "system_prompt_sample": sample_prompt
    }


# --- Assessment Pipeline ---

@app.post("/api/assessments", response_model=StrategicAssessment)
async def create_assessment(request: AssessmentRequest) -> StrategicAssessment:
    assessment = await pipeline.execute_assessment(request)
    return assessment


@app.get("/api/assessments", response_model=List[StrategicAssessment])
async def list_assessments() -> List[StrategicAssessment]:
    return pipeline.list_assessments()


@app.get("/api/assessments/{assessment_id}", response_model=StrategicAssessment)
async def get_assessment(assessment_id: str) -> StrategicAssessment:
    assessment = pipeline.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@app.post("/api/assessments/{assessment_id}/approve", response_model=StrategicAssessment)
async def approve_assessment(assessment_id: str, action: ApprovalAction) -> StrategicAssessment:
    assessment = pipeline.approve_assessment(
        assessment_id=assessment_id,
        reviewer=action.reviewer,
        action=action.action,
        notes=action.notes
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@app.get("/api/assessments/{assessment_id}/export")
async def export_assessment(assessment_id: str, format: str = Query("markdown")) -> Response:
    assessment = pipeline.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if format == "html":
        html_content = ReportGenerator.to_html(assessment)
        return HTMLResponse(content=html_content)
    elif format == "json":
        return Response(content=assessment.model_dump_json(indent=2), media_type="application/json")
    else:
        md_content = ReportGenerator.to_arabic_markdown(assessment)
        return PlainTextResponse(content=md_content, media_type="text/markdown; charset=utf-8")


# --- Evidence Store ---

@app.get("/api/evidence", response_model=List[DocumentEvidence])
async def list_evidence() -> List[DocumentEvidence]:
    return pipeline.collector.get_all()


@app.post("/api/evidence", response_model=DocumentEvidence)
async def add_evidence(doc: DocumentEvidence) -> DocumentEvidence:
    pipeline.collector.add_evidence(doc)
    return doc


# --- Indicators and Early Warning ---

@app.get("/api/indicators")
async def list_indicators():
    return indicator_engine.get_indicators()


@app.post("/api/indicators/{indicator_id}/update")
async def update_indicator(indicator_id: str, new_value: float = Query(...)):
    alert = indicator_engine.update_metric(indicator_id, new_value)
    return {
        "status": "updated",
        "indicator_id": indicator_id,
        "new_value": new_value,
        "triggered_alert": alert.model_dump() if alert else None
    }


@app.get("/api/alerts")
async def list_alerts(active_only: bool = True):
    return indicator_engine.get_alerts(active_only=active_only)


@app.post("/api/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    success = indicator_engine.dismiss_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "dismissed", "alert_id": alert_id}


# Mount web dashboard if available
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "public")
if os.path.isdir(web_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
