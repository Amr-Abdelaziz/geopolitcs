"""Offline regression tests for durable and traceable assessment evidence."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import aiosqlite
import pytest

from packages.schemas.models import DocumentEvidence
from packages.storage.database import DatabaseManager
from services.collection.collector import EvidenceCollector
from services.collection.evidence_metadata import canonical_url, publication_date
from services.collection.web_search import WebSearchClient
from services.verification.admiralty import ClaimVerifier


def collector_for(path, items=(), demo=False):
    return EvidenceCollector(
        osiris_client=Mock(fetch_news=AsyncMock(return_value=list(items))),
        web_search_client=Mock(search_as_evidence=AsyncMock(return_value=[])),
        knowledge_engine_inst=Mock(search_as_evidence=Mock(return_value=[])),
        db=DatabaseManager(str(path)),
        demo_mode=demo,
    )


@pytest.mark.asyncio
async def test_restart_reordering_and_versions(tmp_path):
    path = tmp_path / "evidence.db"
    items = [
        {"id": 42, "title": "Egypt shipping", "link": "https://example.org/a?utm_source=feed",
         "published": "2024-03-01T10:00:00Z", "summary": "Original text"},
        {"id": "other", "title": "Egypt economy", "link": "https://example.org/b"},
    ]
    first = collector_for(path, items)
    docs = await first.collect_for_topic("Egypt", ["Egypt"])
    original = next(doc for doc in docs if doc.title == "Egypt shipping")
    assert original.published_at == datetime(2024, 3, 1, 10, tzinfo=timezone.utc)
    assert original.url == "https://example.org/a"
    assert next(doc for doc in docs if doc.title == "Egypt economy").published_at is None

    items[0]["summary"] = "Revised text"
    second = collector_for(path, list(reversed(items)))
    updated = await second.collect_for_topic("Egypt", ["Egypt"])
    assert len(updated) == 2
    revised = next(doc for doc in updated if doc.id == original.id)
    assert revised.content_hash != original.content_hash
    assert revised.ingested_at == original.ingested_at

    restarted = collector_for(path)
    await restarted.load_evidence()
    assert len(restarted.get_all()) == 2
    async with aiosqlite.connect(path) as db:
        async with db.execute("SELECT COUNT(*) FROM evidence_versions WHERE id = ?", (original.id,)) as cursor:
            assert (await cursor.fetchone())[0] == 2


@pytest.mark.asyncio
async def test_demo_is_explicit_and_never_persisted(tmp_path):
    path = tmp_path / "evidence.db"
    demo = collector_for(path, demo=True)
    docs = await demo.collect_for_topic("Egypt", ["Egypt"])
    assert docs and all(doc.is_demo and doc.published_at is None for doc in docs)
    assert all(doc.source_name.startswith("DEMO /") for doc in docs)
    live = collector_for(path)
    assert await live.collect_for_topic("Egypt", ["Egypt"]) == []
    assert await live.db.list_evidence() == []


@pytest.mark.asyncio
async def test_manual_evidence_survives_restart(tmp_path):
    path = tmp_path / "evidence.db"
    first = collector_for(path)
    saved = await first.add_evidence(DocumentEvidence(
        id="EVD-MANUAL-1", source_id="SRC-1", source_name="Archive",
        title="Report", content_snippet="Text", url="https://example.org/report#section",
    ))
    assert saved.content_hash and saved.url == "https://example.org/report"
    second = collector_for(path)
    await second.load_evidence()
    assert second.get_all() == [saved]


@pytest.mark.asyncio
async def test_web_identity_survives_title_changes_and_unknown_date():
    client = WebSearchClient()
    client.search = AsyncMock(return_value=[{
        "title": "Egypt report", "url": "https://example.org/a", "body": "Text",
        "date": "invalid",
    }])
    first, = await client.search_as_evidence("Egypt")
    client.search.return_value[0]["title"] = "Egypt revised report"
    second, = await client.search_as_evidence("Egypt")
    assert first.id == second.id
    assert first.content_hash != second.content_hash
    assert first.published_at is None and second.published_at is None


def test_citations_accept_live_and_knowledge_ids_and_reject_missing():
    ids = ["EVD-001", "EVD-OSI-ABC123", "EVD-WEB-123ABC", "EVD-KB-DOC-EGY-001"]
    verifier = ClaimVerifier({key: None for key in ids})
    text = " ".join(f"[{key}]" for key in ids)
    valid, citations, missing = verifier.verify_analyst_text(text + " [EVD-001]")
    assert valid and citations == ids and missing == []
    valid, _, missing = verifier.verify_analyst_text(text + " [EVD-WEB-MISSING]")
    assert not valid and missing == ["EVD-WEB-MISSING"]


def test_metadata_does_not_invent_dates_or_strip_identity_parameters():
    assert publication_date(None) is None
    assert publication_date("bad date") is None
    assert publication_date("Fri, 01 Mar 2024 10:00:00 GMT").year == 2024
    assert canonical_url("https://EXAMPLE.org/a?id=2&utm_medium=rss#top") == "https://example.org/a?id=2"


@pytest.mark.asyncio
async def test_evidence_api_persists_and_reloads(tmp_path, monkeypatch):
    from httpx import ASGITransport, AsyncClient
    from apps.api.main import app, pipeline

    collector = collector_for(tmp_path / "api.db")
    monkeypatch.setattr(pipeline, "collector", collector)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/evidence", json={
            "id": "EVD-API-1", "source_id": "SRC-API", "source_name": "Archive",
            "title": "Report", "content_snippet": "Source text",
        })
        assert response.status_code == 200
        assert response.json()["content_hash"]
        collector.store.clear()
        listed = await client.get("/api/evidence")
        assert listed.status_code == 200
        assert listed.json() == [response.json()]
