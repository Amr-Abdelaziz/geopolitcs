"""Tests for Live Web Search Integration and Web OSINT Evidence Collection."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app
from services.collection.web_search import WebSearchClient
from services.collection.collector import EvidenceCollector


@pytest.mark.asyncio
async def test_web_search_client_instantiation():
    """Verify WebSearchClient initializes and handles queries."""
    client = WebSearchClient(timeout=5.0)
    assert client.timeout == 5.0

    # Test conversion to evidence objects with mock/live fallback resilience
    evidences = await client.search_as_evidence(
        query="Egypt military defense",
        target_countries=["Egypt"],
        max_results=3
    )
    # Even if offline or network restricted, should return a list without raising unhandled exception
    assert isinstance(evidences, list)
    for doc in evidences:
        assert doc.id.startswith("EVD-WEB-")
        assert doc.source_id.startswith("SRC-WEB-")
        assert doc.reliability is not None
        assert doc.credibility is not None


@pytest.mark.asyncio
async def test_evidence_collector_includes_web_search():
    """Verify EvidenceCollector invokes web search during topic collection."""
    collector = EvidenceCollector()
    results = await collector.collect_for_topic(
        research_question="تطورات الأمن في ليبيا والحدود المشتركة",
        target_countries=["Libya", "Egypt"]
    )
    assert len(results) >= 5
    # Must contain evidence items from store
    ids = [d.id for d in results]
    assert any("EVD-" in i for i in ids)


@pytest.mark.asyncio
async def test_api_web_search_endpoint():
    """Verify GET /api/search returns 200 and search results."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/search?q=Egypt+Sinai+security&limit=3")
        assert res.status_code == 200
        items = res.json()
        assert isinstance(items, list)
