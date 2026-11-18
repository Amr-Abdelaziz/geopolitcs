"""Strategic OSIRIS - Persistent SQLite / SQL Storage Engine.
Provides asynchronous database persistence for strategic assessments,
reviewer audit trails, and continuous radar events.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite
from packages.schemas.models import StrategicAssessment

log = logging.getLogger("strategic_osiris.storage")


class DatabaseManager:
    """Async database repository for Strategic OSIRIS."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            root_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = root_dir / "data" / "strategic_osiris.db"
        self._initialized = False

    async def init_db(self) -> None:
        """Create tables, indexes, and configure WAL mode."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            # 1. Assessments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    research_question TEXT NOT NULL,
                    reference_country TEXT NOT NULL,
                    target_countries TEXT NOT NULL,
                    time_horizon TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    data_json TEXT NOT NULL
                );
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_assessments_created ON assessments(created_at DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);")

            # 2. Audit Trail table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS assessment_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assessment_id TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    action TEXT NOT NULL,
                    notes TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
                );
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_audits_aid ON assessment_audits(assessment_id);")

            # 3. Radar Events table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS radar_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT,
                    published_at TEXT,
                    ingested_at TEXT NOT NULL,
                    risk_score REAL DEFAULT 0.0,
                    data_json TEXT
                );
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_radar_ingested ON radar_events(ingested_at DESC);")

            await db.commit()
            self._initialized = True
            log.info("Database initialized successfully at %s", self.db_path)

    async def save_assessment(self, assessment: StrategicAssessment) -> None:
        """Insert or update a StrategicAssessment record."""
        if not self._initialized:
            await self.init_db()

        created_iso = assessment.created_at.isoformat()
        updated_iso = (assessment.updated_at or assessment.created_at).isoformat()
        targets_json = json.dumps(assessment.target_countries, ensure_ascii=False)
        data_json = assessment.model_dump_json()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO assessments (
                    id, research_question, reference_country, target_countries,
                    time_horizon, status, created_at, updated_at, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    data_json=excluded.data_json;
            """, (
                assessment.id,
                assessment.research_question,
                assessment.reference_country,
                targets_json,
                assessment.time_horizon,
                assessment.status.value,
                created_iso,
                updated_iso,
                data_json
            ))
            await db.commit()

    async def get_assessment(self, assessment_id: str) -> Optional[StrategicAssessment]:
        """Fetch a single assessment by ID."""
        if not self._initialized:
            await self.init_db()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT data_json FROM assessments WHERE id = ?;", (assessment_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    return StrategicAssessment.model_validate_json(row[0])
        return None

    async def list_assessments(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[StrategicAssessment]:
        """List historical assessments ordered by creation date."""
        if not self._initialized:
            await self.init_db()

        query = "SELECT data_json FROM assessments"
        params: List[Any] = []
        conditions: List[str] = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if country:
            conditions.append("target_countries LIKE ?")
            params.append(f"%{country}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ?;"
        params.append(limit)

        results: List[StrategicAssessment] = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, tuple(params)) as cursor:
                async for row in cursor:
                    if row and row[0]:
                        try:
                            results.append(StrategicAssessment.model_validate_json(row[0]))
                        except Exception as e:
                            log.warning("Failed to deserialize assessment row: %s", e)
        return results

    async def log_audit(
        self,
        assessment_id: str,
        reviewer: str,
        action: str,
        notes: Optional[str] = None
    ) -> None:
        """Record an entry in the approval audit trail."""
        if not self._initialized:
            await self.init_db()

        now_iso = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO assessment_audits (assessment_id, reviewer, action, notes, timestamp)
                VALUES (?, ?, ?, ?, ?);
            """, (assessment_id, reviewer, action, notes or "", now_iso))
            await db.commit()

    async def get_audits(self, assessment_id: str) -> List[Dict[str, Any]]:
        """Fetch audit trail for a specific assessment."""
        if not self._initialized:
            await self.init_db()

        results: List[Dict[str, Any]] = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, reviewer, action, notes, timestamp
                FROM assessment_audits
                WHERE assessment_id = ?
                ORDER BY timestamp ASC;
            """, (assessment_id,)) as cursor:
                async for row in cursor:
                    results.append({
                        "id": row[0],
                        "reviewer": row[1],
                        "action": row[2],
                        "notes": row[3],
                        "timestamp": row[4]
                    })
        return results

    async def save_radar_event(self, event_dict: Dict[str, Any]) -> None:
        """Store or update a continuous radar event."""
        if not self._initialized:
            await self.init_db()

        eid = str(event_dict.get("id") or "")
        if not eid:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        title = str(event_dict.get("title") or "Unknown Event")
        source = str(event_dict.get("source_name") or "")
        pub = str(event_dict.get("published") or now_iso)
        risk = float(event_dict.get("risk_score") or 0.0)
        data_json = json.dumps(event_dict, ensure_ascii=False)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO radar_events (id, title, source, published_at, ingested_at, risk_score, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    risk_score=excluded.risk_score,
                    data_json=excluded.data_json;
            """, (eid, title, source, pub, now_iso, risk, data_json))
            await db.commit()
