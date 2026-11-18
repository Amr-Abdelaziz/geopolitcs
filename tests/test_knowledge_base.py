"""Unit & Integration tests for the Strategic Knowledge Base and Geopolitical Knowledge Graph."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from packages.schemas.models import AdmiraltyCredibility, AdmiraltyReliability, KnowledgeDocument
from services.collection.collector import EvidenceCollector
from services.knowledge.knowledge_engine import KnowledgeEngine, knowledge_engine
from services.knowledge.knowledge_graph_service import KnowledgeGraphService, knowledge_graph_service


def test_knowledge_engine_seed_and_search():
    """Verify knowledge engine initializes default strategic documents and performs relevance search."""
    docs = knowledge_engine.get_all()
    assert len(docs) >= 6

    # Test search for Bab el-Mandeb maritime security
    results = knowledge_engine.search(query="مضيق باب المندب وقناة السويس", target_countries=["Egypt", "Yemen"])
    assert len(results) > 0
    top_doc, score = results[0]
    assert score > 0.0
    assert "DOC-MR-002" in [d.id for d, s in results]

    # Test search as evidence items for 14-agent pipeline
    evidences = knowledge_engine.search_as_evidence(
        query="العقيدة العسكرية وتأمين الحدود الغربية",
        target_countries=["Egypt", "Libya"],
        limit=3
    )
    assert len(evidences) >= 1
    assert evidences[0].reliability == AdmiraltyReliability.A
    assert evidences[0].credibility == AdmiraltyCredibility.ONE
    assert "KB" in evidences[0].id


def test_knowledge_engine_ingest_and_retrieve(tmp_path):
    """Verify document ingestion and retrieval lifecycle."""
    custom_engine = KnowledgeEngine(data_dir=str(tmp_path))
    new_doc = KnowledgeDocument(
        id="DOC-TEST-999",
        title_ar="تقرير استخباراتي تجريبي",
        title_en="Experimental Strategic Report",
        category="doctrine",
        country_coverage=["Egypt", "Sudan"],
        summary="ملخص استراتيجي تجريبي لاختبار محرك المعرفة",
        content="محتوى تفصيلي يوضح جاهزية القوات المشتركة على الحدود الجنوبية لمصر والسودان",
        reliability=AdmiraltyReliability.A,
        credibility=AdmiraltyCredibility.ONE,
        key_entities=["قاعدة برنيس", "معبر قسطل"]
    )
    custom_engine.ingest_document(new_doc)

    retrieved = custom_engine.get_document("DOC-TEST-999")
    assert retrieved is not None
    assert retrieved.title_ar == "تقرير استخباراتي تجريبي"

    # Search hits custom document
    search_hits = custom_engine.search(query="قسطل برنيس", target_countries=["Sudan"])
    assert any(d.id == "DOC-TEST-999" for d, s in search_hits)


def test_knowledge_graph_service_generation():
    """Verify dynamic knowledge graph generation and theater filtering."""
    graph = knowledge_graph_service.build_graph()
    assert len(graph.nodes) >= 15
    assert len(graph.edges) >= 10
    assert "theaters" in graph.model_dump()

    # Node attributes verification
    egy_hq = next((n for n in graph.nodes if n.id == "NODE-EGY-HQ"), None)
    assert egy_hq is not None
    assert egy_hq.unit_id == "EGY-GHQ"
    assert egy_hq.latitude is not None

    # Syria node 6474 verification
    syr_node = next((n for n in graph.nodes if n.id == "NODE-SYR-6474"), None)
    assert syr_node is not None
    assert syr_node.unit_id == "GC-6474"
    assert syr_node.placemark_url is not None

    # Theater filter
    egypt_graph = knowledge_graph_service.build_graph(theater="egypt")
    assert all(n.theater in ("egypt", "regional") for n in egypt_graph.nodes)


@pytest.mark.asyncio
async def test_evidence_collector_merges_knowledge_base():
    """Verify EvidenceCollector automatically pulls verified doctrine into assessment evidence."""
    collector = EvidenceCollector()
    evidences = await collector.collect_for_topic(
        research_question="تقييم المخاطر على الملاحة البحرية بمضيق باب المندب",
        target_countries=["Egypt", "Yemen"]
    )
    assert len(evidences) >= 5
    # Should include at least one knowledge base doctrine item
    has_kb_evidence = any("KB" in e.id or "Strategic Knowledge Base" in e.source_name for e in evidences)
    assert has_kb_evidence is True


@pytest.mark.asyncio
async def test_api_knowledge_endpoints():
    """Test REST API endpoints for Knowledge Base and Knowledge Graph."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/knowledge/graph
        res_graph = await client.get("/api/knowledge/graph")
        assert res_graph.status_code == 200
        graph_data = res_graph.json()
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) >= 15

        # 2. GET /api/knowledge/documents
        res_docs = await client.get("/api/knowledge/documents")
        assert res_docs.status_code == 200
        docs_data = res_docs.json()
        assert len(docs_data) >= 6

        # 3. GET /api/knowledge/documents/DOC-EGY-001
        res_single = await client.get("/api/knowledge/documents/DOC-EGY-001")
        assert res_single.status_code == 200
        assert res_single.json()["id"] == "DOC-EGY-001"

        # 4. GET /api/knowledge/query
        res_query = await client.get("/api/knowledge/query?q=باب+المندب&country=Egypt,Yemen")
        assert res_query.status_code == 200
        qdata = res_query.json()
        assert qdata["total_count"] > 0
        assert len(qdata["results"]) > 0

        # 5. POST /api/knowledge/ingest
        payload = {
            "id": "DOC-API-001",
            "title_ar": "وثيقة استراتيجية عبر الـ API",
            "title_en": "API Ingested Strategic Doc",
            "category": "doctrine",
            "country_coverage": ["Egypt"],
            "summary": "ملخص تجريبي عبر الـ API",
            "content": "نص تفصيلي",
            "reliability": "A",
            "credibility": 1,
            "key_entities": ["قناة السويس"]
        }
        res_ingest = await client.post("/api/knowledge/ingest", json=payload)
        assert res_ingest.status_code == 200
        assert res_ingest.json()["id"] == "DOC-API-001"
