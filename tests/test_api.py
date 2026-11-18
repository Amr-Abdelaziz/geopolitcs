"""Integration tests for Strategic OSIRIS FastAPI endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app


@pytest.mark.asyncio
async def test_api_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        assert data["agents_count"] == 14
        assert "Egypt" in data["target_countries"]


@pytest.mark.asyncio
async def test_api_agents_list_and_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # List all
        res = await client.get("/api/agents")
        assert res.status_code == 200
        agents = res.json()
        assert len(agents) == 14

        # Detail of A01
        res = await client.get("/api/agents/A01")
        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["id"] == "A01"
        assert "رئيس خلية التحليل الاستراتيجي" in data["metadata"]["name_ar"]


@pytest.mark.asyncio
async def test_api_assessment_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Assessment
        payload = {
            "research_question": "متابعة تطورات أمن الملاحة في البحر الأحمر والحدود الغربية المشتركة مع ليبيا",
            "reference_country": "Egypt",
            "target_countries": ["Egypt", "Libya", "Israel"],
            "time_horizon": "6-12 months",
            "assessment_mode": "strategic_assessment"
        }
        create_res = await client.post("/api/assessments", json=payload)
        assert create_res.status_code == 200
        assessment = create_res.json()
        aid = assessment["id"]
        assert assessment["status"] == "pending_review"
        assert len(assessment["key_judgments"]) > 0

        # 2. Get Details
        get_res = await client.get(f"/api/assessments/{aid}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == aid

        # 3. Export Markdown
        md_res = await client.get(f"/api/assessments/{aid}/export?format=markdown")
        assert md_res.status_code == 200
        assert "تقدير موقف استراتيجي" in md_res.text
        assert aid in md_res.text

        # 4. Export HTML
        html_res = await client.get(f"/api/assessments/{aid}/export?format=html")
        assert html_res.status_code == 200
        assert "<html" in html_res.text
        assert aid in html_res.text

        # 5. Human Approval Gate
        approve_res = await client.post(f"/api/assessments/{aid}/approve", json={
            "action": "approve",
            "reviewer": "Director of Strategic Intelligence",
            "notes": "Certified and approved for distribution."
        })
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "approved"
        assert approve_res.json()["approval_reviewer"] == "Director of Strategic Intelligence"


@pytest.mark.asyncio
async def test_api_indicators_and_alerts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List Indicators
        res = await client.get("/api/indicators")
        assert res.status_code == 200
        indicators = res.json()
        assert len(indicators) >= 4

        # 2. Update metric past threshold to trigger alert
        update_res = await client.post("/api/indicators/IND-REDSEA-01/update?new_value=8.0")
        assert update_res.status_code == 200
        data = update_res.json()
        assert data["triggered_alert"] is not None
        alert_id = data["triggered_alert"]["id"]

        # 3. List Alerts
        alerts_res = await client.get("/api/alerts")
        assert alerts_res.status_code == 200
        alerts = alerts_res.json()
        assert any(a["id"] == alert_id for a in alerts)

        # 4. Dismiss Alert
        dismiss_res = await client.post(f"/api/alerts/{alert_id}/dismiss")
        assert dismiss_res.status_code == 200
        assert dismiss_res.json()["status"] == "dismissed"
