"""Strategic OSIRIS - Autonomous Radar Daemon.
Runs continuous background ingestion from OSIRIS, updates threat metrics,
and escalates threshold anomalies into early warning alerts.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from packages.schemas.models import WarningAlert
from packages.storage.database import DatabaseManager
from services.collection.collector import EvidenceCollector, OsirisClient
from services.warning.indicator_engine import IndicatorEngine

log = logging.getLogger("strategic_osiris.radar")


class RadarDaemon:
    """Continuous background worker for automated situational awareness."""

    def __init__(
        self,
        osiris_client: Optional[OsirisClient] = None,
        collector: Optional[EvidenceCollector] = None,
        indicator_engine: Optional[IndicatorEngine] = None,
        db: Optional[DatabaseManager] = None,
        interval_seconds: int = 600  # Default: 10 minutes
    ):
        self.client = osiris_client or OsirisClient()
        self.collector = collector or EvidenceCollector(client=self.client)
        self.indicator_engine = indicator_engine or IndicatorEngine()
        self.db = db or DatabaseManager()
        self.interval = interval_seconds

        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_run: Optional[datetime] = None
        self.total_ingested = 0
        self.last_ingested_count = 0
        self.last_triggered_alerts: List[str] = []

    async def start(self) -> None:
        """Start the background monitoring loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        log.info("RadarDaemon started with polling interval %ds", self.interval)

    async def stop(self) -> None:
        """Stop the background monitoring loop."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("RadarDaemon stopped")

    async def _loop(self) -> None:
        """Continuous execution loop."""
        # Initial run on startup
        try:
            await self.run_cycle()
        except Exception as e:
            log.warning("Initial radar cycle error: %s", e)

        while self.is_running:
            try:
                await asyncio.sleep(self.interval)
                if self.is_running:
                    await self.run_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Radar cycle error: %s", e)

    async def run_cycle(self) -> Dict[str, Any]:
        """Execute a single ingestion and threshold evaluation cycle."""
        log.info("Executing continuous radar ingestion cycle...")
        now = datetime.now(timezone.utc)
        self.last_run = now

        # 1. Fetch live news from OSIRIS
        news_items = await self.client.fetch_news(limit=60)
        new_count = 0

        # Region event counters
        region_counts = {
            "Red Sea": 0,
            "Libya": 0,
            "Israel": 0,
            "East Med": 0
        }

        for item in news_items:
            eid = str(item.get("id") or "")
            if not eid:
                continue

            # Save to database
            try:
                await self.db.save_radar_event(item)
                new_count += 1
            except Exception as e:
                log.debug("Failed to store radar event in DB: %s", e)

            # Location and regional tagging
            title = str(item.get("title") or "").lower()
            snippet = str(item.get("summary") or item.get("description") or "").lower()
            place_name = str((item.get("place") or {}).get("name") or "").lower()
            combined = f"{title} {snippet} {place_name}"

            if any(k in combined for k in ("red sea", "bab el-mandeb", "yemen", "houthi", "البحر الأحمر")):
                region_counts["Red Sea"] += 1
            if any(k in combined for k in ("libya", "tripoli", "benghazi", "tobruk", "ليبيا")):
                region_counts["Libya"] += 1
            if any(k in combined for k in ("gaza", "israel", "sinai", "philadelphi", "غزة", "إسرائيل")):
                region_counts["Israel"] += 1
            if any(k in combined for k in ("east med", "mediterranean", "gas", "المتوسط", "غاز")):
                region_counts["East Med"] += 1

        self.last_ingested_count = new_count
        self.total_ingested += new_count

        # 2. Update Early Warning Indicators based on regional incident rates
        new_alerts: List[WarningAlert] = []

        if region_counts["Red Sea"] > 0:
            # Baseline is 3.0 weekly
            metric = min(12.0, max(2.0, region_counts["Red Sea"] * 0.8))
            alert = self.indicator_engine.update_metric("IND-REDSEA-01", metric)
            if alert:
                new_alerts.append(alert)

        if region_counts["Libya"] > 0:
            metric = min(10.0, max(1.5, region_counts["Libya"] * 0.7))
            alert = self.indicator_engine.update_metric("IND-LIBYA-01", metric)
            if alert:
                new_alerts.append(alert)

        if region_counts["Israel"] > 0:
            metric = min(15.0, max(3.0, region_counts["Israel"] * 1.2))
            alert = self.indicator_engine.update_metric("IND-ISRAEL-01", metric)
            if alert:
                new_alerts.append(alert)

        if region_counts["East Med"] > 0:
            metric = min(8.0, max(1.0, region_counts["East Med"] * 0.5))
            alert = self.indicator_engine.update_metric("IND-EASTMED-01", metric)
            if alert:
                new_alerts.append(alert)

        self.last_triggered_alerts = [a.id for a in new_alerts]
        active_alerts = self.indicator_engine.get_alerts(active_only=True)

        summary = {
            "status": "success",
            "timestamp": now.isoformat(),
            "items_fetched": len(news_items),
            "new_events_stored": new_count,
            "region_counts": region_counts,
            "new_alerts_triggered": len(new_alerts),
            "total_active_alerts": len(active_alerts)
        }
        log.info("Radar cycle completed: %s", summary)
        return summary

    def get_status(self) -> Dict[str, Any]:
        """Return operational status and metrics."""
        now = datetime.now(timezone.utc)
        seconds_ago = (now - self.last_run).total_seconds() if self.last_run else None
        active_alerts = self.indicator_engine.get_alerts(active_only=True)

        return {
            "status": "active" if self.is_running else "idle",
            "interval_seconds": self.interval,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_run_seconds_ago": round(seconds_ago, 1) if seconds_ago is not None else None,
            "last_ingested_count": self.last_ingested_count,
            "total_ingested": self.total_ingested,
            "active_alerts_count": len(active_alerts),
            "alerts": [a.model_dump() for a in active_alerts[:5]]
        }
