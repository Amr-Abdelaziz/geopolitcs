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
from packages.prompts.registry import (
    AGENT_REGISTRY,
    agent_config_manager,
    build_system_prompt,
)
from packages.schemas.models import (
    AgentDefinition,
    AgentDetailResponse,
    AgentID,
    AgentUpdateRequest,
    ApprovalAction,
    AssessmentRequest,
    DocumentEvidence,
    RECOMMENDED_MODELS,
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
    osiris_health = await pipeline.collector.client.check_health()
    return {
        "status": "online",
        "service": "Strategic OSIRIS Intelligence Fusion Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_count": len(AGENT_REGISTRY),
        "llm_mode": "mock_fallback" if pipeline.llm.mock_mode else "openrouter_live",
        "target_countries": ["Egypt", "Libya", "Israel"],
        "osiris_upstream": osiris_health
    }


@app.get("/api/osiris/status")
async def osiris_status() -> Dict[str, Any]:
    health = await pipeline.collector.client.check_health()
    sample_news = await pipeline.collector.client.fetch_news(limit=5)
    return {
        "health": health,
        "sample_live_news_count": len(sample_news),
        "latest_headline": sample_news[0].get("title") if sample_news else None,
        "sample_items": [
            {
                "id": n.get("id"),
                "source": n.get("source_name"),
                "title": n.get("title"),
                "published": n.get("published"),
                "risk_score": n.get("risk_score")
            }
            for n in sample_news[:3]
        ]
    }



# --- Agent Management & Customization ---

@app.get("/api/agents", response_model=List[AgentDefinition])
async def list_agents() -> List[AgentDefinition]:
    return agent_config_manager.list_agents()


@app.get("/api/agents/models", response_model=List[str])
async def list_recommended_models() -> List[str]:
    return RECOMMENDED_MODELS


@app.get("/api/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str) -> AgentDetailResponse:
    try:
        aid = AgentID(agent_id.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent ID not found")
    
    agent_def = agent_config_manager.get_agent(aid)
    if not agent_def:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    
    current_prompt = agent_config_manager.get_prompt(aid)
    default_prompt = agent_config_manager.get_default_prompt(aid)
    sample_prompt = build_system_prompt(aid, "سؤال استراتيجي اختباري")
    return AgentDetailResponse(
        metadata=agent_def,
        system_prompt=current_prompt,
        default_system_prompt=default_prompt,
        is_customized=agent_def.is_customized,
        system_prompt_sample=sample_prompt,
        available_models=RECOMMENDED_MODELS
    )


@app.put("/api/agents/{agent_id}", response_model=AgentDetailResponse)
async def update_agent(agent_id: str, update: AgentUpdateRequest) -> AgentDetailResponse:
    try:
        aid = AgentID(agent_id.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent ID not found")
    
    if aid not in agent_config_manager.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_def = agent_config_manager.update_agent(aid, update)
    current_prompt = agent_config_manager.get_prompt(aid)
    default_prompt = agent_config_manager.get_default_prompt(aid)
    sample_prompt = build_system_prompt(aid, "سؤال استراتيجي اختباري")
    return AgentDetailResponse(
        metadata=agent_def,
        system_prompt=current_prompt,
        default_system_prompt=default_prompt,
        is_customized=agent_def.is_customized,
        system_prompt_sample=sample_prompt,
        available_models=RECOMMENDED_MODELS
    )


@app.post("/api/agents/{agent_id}/reset", response_model=AgentDetailResponse)
async def reset_agent(agent_id: str) -> AgentDetailResponse:
    try:
        aid = AgentID(agent_id.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent ID not found")
    
    agent_def = agent_config_manager.reset_agent(aid)
    current_prompt = agent_config_manager.get_prompt(aid)
    default_prompt = agent_config_manager.get_default_prompt(aid)
    sample_prompt = build_system_prompt(aid, "سؤال استراتيجي اختباري")
    return AgentDetailResponse(
        metadata=agent_def,
        system_prompt=current_prompt,
        default_system_prompt=default_prompt,
        is_customized=False,
        system_prompt_sample=sample_prompt,
        available_models=RECOMMENDED_MODELS
    )


@app.post("/api/agents/reset-all", response_model=List[AgentDefinition])
async def reset_all_agents() -> List[AgentDefinition]:
    return agent_config_manager.reset_all()


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
