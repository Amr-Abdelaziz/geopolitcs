"""Tests for MiroFish Integration and Multi-Actor Wargame Simulation."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app
from packages.schemas.models import WargameRequest
from services.simulation.mirofish_client import MiroFishClient


@pytest.mark.asyncio
async def test_mirofish_client_status():
    """Verify MiroFish client status reporting."""
    client = MiroFishClient(base_url="http://localhost:5001")
    status = await client.check_status()
    assert "status" in status
    assert "url" in status
    assert status["status"] in ("online", "standby")


@pytest.mark.asyncio
async def test_api_simulation_status():
    """Verify GET /api/simulation/status endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/simulation/status")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "mode" in data


@pytest.mark.asyncio
async def test_api_wargame_simulation_execution():
    """Verify POST /api/simulation/wargame executes wargame with actors and rounds."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "research_question": "محاكاة تداعيات فرض منطقة حظر طيران أو منطقة عازلة غرب ليبيا",
            "reference_country": "Egypt",
            "target_countries": ["Egypt", "Libya"],
            "rounds_count": 2,
            "god_view_intervention": "مصر تنشر منظومات رادار دفاع جوي متقدمة وتعلن خط أحمر أمني",
            "use_live_web_evidence": False
        }
        res = await client.post("/api/simulation/wargame", json=payload, timeout=45.0)
        assert res.status_code == 200
        sim = res.json()
        assert sim["id"].startswith("WARGAME-")
        assert sim["status"] == "completed"
        assert len(sim["actors"]) >= 3
        assert len(sim["rounds"]) >= 2
        assert len(sim["emergent_outcomes"]) >= 1
        assert "probability_distribution" in sim
        assert "knowledge_graph" in sim
        assert len(sim["knowledge_graph"]["nodes"]) >= 5


@pytest.mark.asyncio
async def test_api_simulation_graph():
    """Verify GET /api/simulation/graph returns knowledge graph."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/simulation/graph")
        assert res.status_code == 200
        data = res.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) >= 10
        assert len(data["edges"]) >= 10


def test_mirofish_fallback_generation():
    """Verify deterministic fallback produces valid schema on error."""
    client = MiroFishClient()
    req = WargameRequest(
        research_question="اختبار سيناريو استراتيجي",
        god_view_intervention="إجراء احترازي"
    )
    fallback = client._fallback_result("WARGAME-TEST", req, evidence_count=3)
    assert fallback.id == "WARGAME-TEST"
    assert len(fallback.actors) >= 3
    assert len(fallback.rounds) >= 2
    assert len(fallback.emergent_outcomes) >= 1
