"""Pytest configuration ensuring unit tests run safely and deterministically
without burning live API credits.
"""
import os
import pytest

# Ensure tests run in mock mode to protect user credits
os.environ["MOCK_LLM"] = "1"
os.environ["DEMO_EVIDENCE"] = "1"


@pytest.fixture(autouse=True)
def isolate_evidence_storage(tmp_path, monkeypatch):
    """Keep test assessments and knowledge ingestion out of application data."""
    from apps.api.main import db, pipeline
    from packages.storage.database import DatabaseManager
    from services.knowledge.knowledge_engine import knowledge_engine

    test_db = tmp_path / "application.db"
    original_init = DatabaseManager.__init__

    def init_test_database(self, db_path=None):
        original_init(self, db_path or str(test_db))

    monkeypatch.setattr(DatabaseManager, "__init__", init_test_database)
    monkeypatch.setattr(db, "db_path", test_db)
    monkeypatch.setattr(db, "_initialized", False)
    monkeypatch.setattr(pipeline.collector, "store", {
        key: doc for key, doc in pipeline.collector.store.items() if doc.is_demo
    })
    monkeypatch.setattr(knowledge_engine, "documents_file", tmp_path / "documents.json")
    monkeypatch.setattr(knowledge_engine, "_documents", dict(knowledge_engine._documents))
