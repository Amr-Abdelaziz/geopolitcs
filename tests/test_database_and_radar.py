"""Tests for Database persistence, Radar Daemon, and SSE Deliberation Streaming."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app, db, radar_daemon
from packages.schemas.models import (
    AssessmentMode,
    AssessmentRequest,
    AssessmentStatus,
    StrategicAssessment,
)
from packages.storage.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_crud_and_audit(tmp_path):
    """Verify storing, retrieving, and logging audits for assessments."""
    db_file = str(tmp_path / "test.db")
    mgr = DatabaseManager(db_path=db_file)
    await mgr.init_db()

    assessment = StrategicAssessment(
        id="SA-TEST-001",
        research_question="اختبار قاعدة البيانات الدائمة",
        reference_country="Egypt",
        target_countries=["Egypt", "Libya"],
        time_horizon="1-3 months",
        assessment_mode=AssessmentMode.STRATEGIC_ASSESSMENT,
        status=AssessmentStatus.PENDING_REVIEW,
        key_judgments=["حكم استراتيجي تجريبي"]
    )

    # 1. Save
    await mgr.save_assessment(assessment)

    # 2. Retrieve
    retrieved = await mgr.get_assessment("SA-TEST-001")
    assert retrieved is not None
    assert retrieved.id == "SA-TEST-001"
    assert retrieved.research_question == "اختبار قاعدة البيانات الدائمة"
    assert len(retrieved.key_judgments) == 1

    # 3. Audit log
    await mgr.log_audit("SA-TEST-001", "Chief Reviewer", "approve", "Approved for testing")
    audits = await mgr.get_audits("SA-TEST-001")
    assert len(audits) == 1
    assert audits[0]["reviewer"] == "Chief Reviewer"
    assert audits[0]["action"] == "approve"

    # 4. List assessments
    list_res = await mgr.list_assessments(limit=10)
    assert len(list_res) >= 1
    assert list_res[0].id == "SA-TEST-001"


@pytest.mark.asyncio
async def test_api_streaming_deliberation():
    """Verify that POST /api/assessments/stream streams SSE events."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "research_question": "تقييم أمن الملاحة في البحر الأحمر وقناة السويس",
            "reference_country": "Egypt",
            "target_countries": ["Egypt", "Red Sea"],
            "time_horizon": "1-3 months",
            "assessment_mode": "strategic_assessment"
        }
        res = await client.post("/api/assessments/stream", json=payload, timeout=30.0)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body_text = res.text
        assert "event: init" in body_text
        assert "event: phase" in body_text
        assert "event: complete" in body_text


@pytest.mark.asyncio
async def test_radar_daemon_and_api():
    """Verify radar status and cycle trigger endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Check radar status
        res = await client.get("/api/radar/status")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "interval_seconds" in data

        # 2. Trigger radar cycle
        trigger_res = await client.post("/api/radar/trigger")
        assert trigger_res.status_code == 200
        cycle_data = trigger_res.json()
        assert cycle_data["status"] == "success"
        assert "items_fetched" in cycle_data
