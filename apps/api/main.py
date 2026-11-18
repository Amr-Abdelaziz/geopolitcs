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
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
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
    WargameRequest,
    WargameSimulationResult,
    KnowledgeGraph,
    KnowledgeDocument,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    OrbatCatalogItem,
    OrbatTreeResponse,
    OrbatUnit,
)
from packages.storage.database import DatabaseManager
from services.orchestrator.pipeline import StrategicPipeline
from services.reporting.generator import ReportGenerator
from services.simulation.mirofish_client import MiroFishClient
from services.orbat.orbat_service import OrbatService
from contextlib import asynccontextmanager
from services.warning.indicator_engine import IndicatorEngine
from services.warning.radar_daemon import RadarDaemon
from services.knowledge.knowledge_engine import knowledge_engine
from services.knowledge.knowledge_graph_service import knowledge_graph_service

db = DatabaseManager()
pipeline = StrategicPipeline(db=db)
mirofish_client = MiroFishClient(llm_client=pipeline.llm)
orbat_service = OrbatService()
indicator_engine = IndicatorEngine()
radar_daemon = RadarDaemon(
    osiris_client=pipeline.collector.client,
    collector=pipeline.collector,
    indicator_engine=indicator_engine,
    db=db,
    interval_seconds=600
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    await radar_daemon.start()
    try:
        yield
    finally:
        await radar_daemon.stop()


app = FastAPI(
    title="Strategic OSIRIS (SIFP) Intelligence API",
    description="Multi-Agent Strategic Intelligence Fusion Platform for Defense and Geopolitics",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "osiris_upstream": osiris_health,
        "radar": radar_daemon.get_status()
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


# --- Assessment Pipeline & Streaming ---

@app.post("/api/assessments", response_model=StrategicAssessment)
async def create_assessment(request: AssessmentRequest) -> StrategicAssessment:
    assessment = await pipeline.execute_assessment(request)
    return assessment


@app.post("/api/assessments/stream")
async def stream_assessment(request: AssessmentRequest) -> StreamingResponse:
    """Stream multi-agent deliberation events via Server-Sent Events (SSE)."""
    return StreamingResponse(
        pipeline.execute_assessment_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/assessments", response_model=List[StrategicAssessment])
async def list_assessments(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    country: Optional[str] = Query(None)
) -> List[StrategicAssessment]:
    return await pipeline.list_assessments_async(limit=limit, status=status, country=country)


@app.get("/api/assessments/{assessment_id}", response_model=StrategicAssessment)
async def get_assessment(assessment_id: str) -> StrategicAssessment:
    assessment = await pipeline.get_assessment_async(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@app.get("/api/assessments/{assessment_id}/audits")
async def get_assessment_audits(assessment_id: str):
    """Retrieve full reviewer audit trail for this assessment."""
    return await db.get_audits(assessment_id)


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
    assessment = await pipeline.get_assessment_async(assessment_id)
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


# --- Autonomous Radar & Ingestion ---

@app.get("/api/radar/status")
async def get_radar_status() -> Dict[str, Any]:
    return radar_daemon.get_status()


@app.post("/api/radar/trigger")
async def trigger_radar_cycle() -> Dict[str, Any]:
    return await radar_daemon.run_cycle()


# --- Evidence Store & Web Search ---

@app.get("/api/search", response_model=List[DocumentEvidence])
async def search_live_web(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(5, ge=1, le=15)
) -> List[DocumentEvidence]:
    """Execute live open-source web search and return structured evidence items."""
    return await pipeline.collector.web_search.search_as_evidence(query=q, max_results=limit)


@app.get("/api/evidence", response_model=List[DocumentEvidence])
async def list_evidence() -> List[DocumentEvidence]:
    await pipeline.collector.load_evidence()
    return pipeline.collector.get_all()


@app.post("/api/evidence", response_model=DocumentEvidence)
async def add_evidence(doc: DocumentEvidence) -> DocumentEvidence:
    return await pipeline.collector.add_evidence(doc)


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


# --- MiroFish Multi-Agent Wargaming & Swarm Simulation ---

@app.get("/api/simulation/status")
async def get_simulation_status():
    """Return status of MiroFish wargaming engine (online container or native bridge)."""
    return await mirofish_client.check_status()


@app.get("/api/simulation/graph", response_model=KnowledgeGraph)
async def get_knowledge_graph(
    countries: Optional[str] = Query("Egypt,Libya,Israel", description="Comma-separated country list")
) -> KnowledgeGraph:
    """Return the active strategic knowledge graph connecting regional factions, chokepoints, and threats."""
    return knowledge_graph_service.build_graph()


# --- Strategic Knowledge Base & Geopolitical Knowledge Graph ---

@app.get("/api/knowledge/graph", response_model=KnowledgeGraph)
async def get_enhanced_knowledge_graph(
    theater: Optional[str] = Query(None, description="Filter by theater: all, egypt, libya, syria, red_sea, east_med, israel"),
    node_type: Optional[str] = Query(None, description="Filter by type: all, actor, military_unit, chokepoint, resource, threat")
) -> KnowledgeGraph:
    """Return the dynamic geopolitical knowledge graph with ORBAT linkages and chokepoints."""
    return knowledge_graph_service.build_graph(theater=theater, node_type=node_type)


@app.get("/api/knowledge/documents", response_model=List[KnowledgeDocument])
async def list_knowledge_documents(
    category: Optional[str] = Query(None, description="Filter by category: doctrine, treaty, chokepoint, military_analysis, conflict_history")
) -> List[KnowledgeDocument]:
    """List all strategic defense doctrine, treaty, and intelligence documents."""
    docs = knowledge_engine.get_all()
    if category and category.lower() != "all":
        docs = [d for d in docs if d.category.lower() == category.lower()]
    return docs


@app.get("/api/knowledge/documents/{doc_id}", response_model=KnowledgeDocument)
async def get_knowledge_document(doc_id: str) -> KnowledgeDocument:
    """Retrieve full strategic intelligence document by ID."""
    doc = knowledge_engine.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Knowledge document '{doc_id}' not found")
    return doc


@app.get("/api/knowledge/query", response_model=KnowledgeSearchResponse)
async def query_knowledge_base(
    q: str = Query(..., description="Search query string"),
    country: Optional[str] = Query(None, description="Optional target country"),
    category: Optional[str] = Query(None, description="Optional category"),
    limit: int = Query(5, ge=1, le=20)
) -> KnowledgeSearchResponse:
    """Semantic and lexical search across strategic doctrine and geopolitical treaties."""
    target_countries = [c.strip() for c in country.split(",") if c.strip()] if country else None
    results = knowledge_engine.search(query=q, target_countries=target_countries, category=category, limit=limit)
    docs = [r[0] for r in results]
    matched_entities = list({e for d in docs for e in d.key_entities})
    return KnowledgeSearchResponse(
        results=docs,
        total_count=len(docs),
        matched_entities=matched_entities[:10]
    )


@app.post("/api/knowledge/ingest", response_model=KnowledgeDocument)
async def ingest_knowledge_document(doc: KnowledgeDocument) -> KnowledgeDocument:
    """Ingest a new strategic doctrine or intelligence report into the persistent knowledge base."""
    return knowledge_engine.ingest_document(doc)


@app.post("/api/simulation/wargame", response_model=WargameSimulationResult)
async def run_wargame_simulation(request: WargameRequest) -> WargameSimulationResult:
    """Execute a deep multi-actor wargame simulation with emergent behavior modeling."""
    evidence = []
    if request.use_live_web_evidence:
        evidence = await pipeline.collector.collect_for_topic(
            research_question=request.research_question,
            target_countries=request.target_countries
        )
    return await mirofish_client.run_simulation(request=request, evidence_list=evidence)


# --- Order of Battle (ORBAT) Engine ---

@app.get("/api/orbat/catalogs", response_model=List[OrbatCatalogItem])
async def list_orbat_catalogs():
    """List all supported Order of Battle catalogs (GeoConfirmed + Local)."""
    return orbat_service.get_catalogs()


@app.get("/api/orbat", response_model=OrbatTreeResponse)
async def get_orbat_tree(
    catalog: Optional[str] = Query(None, description="Catalog slug: egypt, libya, israel, russia, middleeasternfactions, yemen, iran, sudan, us, ukraine, endf"),
    country: Optional[str] = Query(None, description="Target country or catalog slug"),
    branch: Optional[str] = Query("All", description="Branch filter: Ground, Naval, Air Force, Air Defense, Special Forces, Border Guard, or All"),
    search: Optional[str] = Query(None, description="Search query across unit name, role, equipment, or location")
) -> OrbatTreeResponse:
    """Return hierarchical Order of Battle (ORBAT) command structure with official logos."""
    return orbat_service.get_orbat_tree(catalog=catalog, country=country, branch=branch, search=search)


@app.get("/api/orbat/{unit_id}", response_model=OrbatUnit)
async def get_orbat_unit(unit_id: str) -> OrbatUnit:
    """Retrieve full military dossier and technical specifications for a single ORBAT unit."""
    unit = orbat_service.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found in Order of Battle")
    return unit


# Mount web dashboard if available
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "public")
if os.path.isdir(web_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
