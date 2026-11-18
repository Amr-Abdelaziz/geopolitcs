"""Strategic OSIRIS - OSIRIS Direct Integration Client.
Connects directly to the OSIRIS situational awareness and intelligence API.
Provides built-in live feeds and rich fallback fixtures for Egypt, Libya, and Israel.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import httpx
from packages.schemas.models import AdmiraltyCredibility, AdmiraltyReliability, DocumentEvidence
from packages.storage.database import DatabaseManager
from services.collection.evidence_metadata import canonical_url, content_hash, evidence_id, publication_date
from services.collection.web_search import WebSearchClient
from services.knowledge.knowledge_engine import KnowledgeEngine, knowledge_engine

log = logging.getLogger("strategic_osiris.collection")


# Strategic baseline fixtures for Egypt, Libya, and Israel
DEFAULT_EVIDENCES: List[Dict[str, Any]] = [
    {
        "id": "EVD-001",
        "source_name": "Official Armed Forces & Defense Release",
        "title": "مناورات تفتيش حرب وتأمين الاتجاه الاستراتيجي الشمالي الشرقي والغربي",
        "snippet": "القوات المسلحة المصرية تنفذ تدريبات تعبوية بالذخيرة الحية لرفع درجات الاستعداد القتالي وتأمين الحدود البرية والساحلية ومكافحة التهديدات العابرة للحدود.",
        "countries": ["Egypt", "Libya", "Israel"],
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "tags": ["military", "border_security", "readiness"]
    },
    {
        "id": "EVD-002",
        "source_name": "Regional Security Monitor & Libya Desk",
        "title": "متابعة تطورات الحوار الأمني الليبي والسيطرة على المعابر الغربية",
        "snippet": "تنسيق عسكري وأمني مكثف لمنع محاولات التسلل عبر الحدود الليبية-المصرية المشتركة ودعم المسار السياسي برعاية الأمم المتحدة لتوحيد المؤسسات.",
        "countries": ["Libya", "Egypt"],
        "reliability": AdmiraltyReliability.B,
        "credibility": AdmiraltyCredibility.TWO,
        "tags": ["political", "border_security", "libya"]
    },
    {
        "id": "EVD-003",
        "source_name": "Maritime Security Centre & Suez Canal Authority",
        "title": "رصد حركة الملاحة الدولية في البحر الأحمر ومضيق باب المندب",
        "snippet": "تسيير دوريات بحرية مصرية لتأمين حرية الملاحة الدولية في البحر الأحمر والتصدي لأي مخاطر تهدد حركة التجارة العالمية باتجاه قناة السويس.",
        "countries": ["Egypt", "Red Sea"],
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "tags": ["maritime", "suez_canal", "energy", "red_sea"]
    },
    {
        "id": "EVD-004",
        "source_name": "Middle East Strategic Studies & Regional Desk",
        "title": "تقييم التوازنات العسكرية وتداعيات التصعيد في قطاع غزة والحدود المشتركة",
        "snippet": "تأكيدات مصرية استراتيجية حاسمة على عدم المساس بالسيادة الوطنية ورفض تصفية القضية الفلسطينية مع مواصلة جهود الوساطة والتهدئة.",
        "countries": ["Egypt", "Israel"],
        "reliability": AdmiraltyReliability.B,
        "credibility": AdmiraltyCredibility.TWO,
        "tags": ["military", "geopolitics", "israel", "gaza"]
    },
    {
        "id": "EVD-005",
        "source_name": "East Med Gas Forum & Defense Tech Bulletin",
        "title": "تطوير منظومات الرصد الراداري والتصنيع الدفاعي بمعرض EDEX",
        "snippet": "الصناعات الدفاعية المصرية تعلن دخول أنظمة مسيرات استطلاع ورادارات إنذار مبكر الخدمة مع استمرار تصدير الغاز المسال عبر منشآت إدكو ودمياط.",
        "countries": ["Egypt", "East Med"],
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.TWO,
        "tags": ["defense_tech", "energy", "east_med", "edex"]
    }
]


class OsirisClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get("OSIRIS_URL", "https://agent.gorbit.space")).rstrip("/")

    async def check_health(self) -> Dict[str, Any]:
        """Check status of live OSIRIS instance."""
        for verify in (True, False):
            try:
                async with httpx.AsyncClient(timeout=5.0, verify=verify) as client:
                    res = await client.get(f"{self.base_url}/api/health")
                    if res.status_code == 200:
                        return {"status": "online", "url": self.base_url, "data": res.json()}
            except Exception as e:
                if verify:
                    continue
                return {"status": "offline", "url": self.base_url, "error": str(e)}
        return {"status": "offline", "url": self.base_url}

    async def fetch_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch raw live news & event intelligence from OSIRIS."""
        for verify in (True, False):
            try:
                async with httpx.AsyncClient(timeout=8.0, verify=verify) as client:
                    res = await client.get(f"{self.base_url}/api/news")
                    if res.status_code == 200:
                        data = res.json()
                        items = data.get("news", [])
                        log.info("Ingested %d live items from OSIRIS API (%s)", len(items), self.base_url)
                        return items[:limit]
            except Exception as e:
                if verify:
                    continue
                log.warning("Could not reach OSIRIS at %s: %s", self.base_url, str(e))
        return []

    async def fetch_brief(self) -> Dict[str, Any]:
        """Fetch world brief or headline summary from OSIRIS."""
        news = await self.fetch_news(limit=5)
        if news:
            top_headlines = [f"• {item.get('title', '')}" for item in news[:3]]
            return {
                "headline": news[0].get("title", ""),
                "text": "\n".join(top_headlines)
            }
        return {
            "headline": "المشهد الاستراتيجي لمنطقة الشرق الأوسط وشمال إفريقيا",
            "text": "استمرار التوترات في الممرات البحرية بالبحر الأحمر والحدود الإقليمية، مع يقظة دفاعية مصرية شاملة."
        }


class EvidenceCollector:
    def __init__(
        self,
        osiris_client: Optional[OsirisClient] = None,
        web_search_client: Optional[WebSearchClient] = None,
        knowledge_engine_inst: Optional[KnowledgeEngine] = None,
        db: Optional[DatabaseManager] = None,
        demo_mode: Optional[bool] = None,
    ):
        self.client = osiris_client or OsirisClient()
        self.web_search = web_search_client or WebSearchClient()
        self.knowledge = knowledge_engine_inst or knowledge_engine
        self.db = db or DatabaseManager()
        self.demo_mode = demo_mode if demo_mode is not None else os.getenv("DEMO_EVIDENCE", "0") == "1"
        self.store: Dict[str, DocumentEvidence] = {}
        # Preload baseline
        for item in DEFAULT_EVIDENCES if self.demo_mode else []:
            doc = DocumentEvidence(
                id=item["id"],
                source_id="SRC-DEF",
                source_name=f"DEMO / {item['source_name']}",
                title=item["title"],
                content_snippet=item["snippet"],
                reliability=AdmiraltyReliability.F,
                credibility=AdmiraltyCredibility.SIX,
                countries_mentioned=item["countries"],
                tags=item["tags"] + ["demo"],
                is_demo=True,
                published_at=None,
                content_hash=content_hash(item["title"], item["snippet"]),
            )
            self.store[doc.id] = doc

    async def collect_for_topic(
        self,
        research_question: str,
        target_countries: List[str]
    ) -> List[DocumentEvidence]:
        """Collect and filter evidence from live OSIRIS feeds, real-time web search, and strategic defense baselines."""
        await self.load_evidence()
        # 0. Ingest verified strategic doctrine & chokepoint treaties from Knowledge Base
        kb_docs = self.knowledge.search_as_evidence(
            query=research_question,
            target_countries=target_countries,
            limit=4
        )
        collected = list(kb_docs)
        for kdoc in kb_docs:
            self.store[kdoc.id] = kdoc
        if kb_docs:
            log.info("Ingested %d strategic doctrine documents from Knowledge Base", len(kb_docs))

        # 1. Fetch live news items from OSIRIS
        osiris_news = await self.client.fetch_news(limit=40)
        for item in osiris_news:
            title = item.get("title") or ""
            snippet = item.get("summary") or item.get("description") or ""
            source_name = f"OSIRIS / {item.get('source_name', 'Live Feed')}"
            link = canonical_url(item.get("link") or item.get("url"))
            doc_id = evidence_id("OSI", link, str(item.get("id") or f"{source_name}:{title}"))
            
            # Extract mentioned countries safely
            coords_str = str(item.get("coords_anchor") or "")
            place_dict = item.get("place") or {}
            place_name = str(place_dict.get("name") or "")
            combined_text = f"{title} {snippet} {coords_str} {place_name}".lower()
            detected_countries = []
            if any(k in combined_text for k in ("egypt", "cairo", "suez", "sinai", "مصر")):
                detected_countries.append("Egypt")
            if any(k in combined_text for k in ("libya", "tripoli", "benghazi", "ليبيا")):
                detected_countries.append("Libya")
            if any(k in combined_text for k in ("israel", "tel aviv", "gaza", "palestin", "إسرائيل", "غزة")):
                detected_countries.append("Israel")
            if any(k in combined_text for k in ("red sea", "yemen", "houthi", "bab el-mandeb", "البحر الأحمر")):
                detected_countries.append("Red Sea")
            if any(k in combined_text for k in ("mediterranean", "east med", "المتوسط")):
                detected_countries.append("East Med")
            if not detected_countries:
                detected_countries.append("Regional")

            tags = (item.get("risk_keywords") or []) + [item.get("alert_kind") or "osint"]

            doc = DocumentEvidence(
                id=doc_id,
                source_id=f"OSIRIS-{str(item.get('id') or doc_id)}",
                source_name=source_name,
                title=title,
                url=link,
                content_snippet=snippet[:400],
                reliability=AdmiraltyReliability.B,
                credibility=AdmiraltyCredibility.TWO,
                countries_mentioned=detected_countries,
                tags=tags,
                published_at=publication_date(item.get("published_at") or item.get("published") or item.get("date")),
                content_hash=content_hash(title, snippet[:400]),
            )
            self.store[doc.id] = doc
            collected.append(doc)

        # 2. Execute live open-source web search on the research topic
        search_query = " ".join(research_question.split()[:10])
        try:
            web_docs = await self.web_search.search_as_evidence(
                query=search_query,
                target_countries=target_countries,
                max_results=5
            )
            for wdoc in web_docs:
                self.store[wdoc.id] = wdoc
            collected.extend(web_docs)
            if web_docs:
                log.info("Ingested %d live web search evidence items for query '%s'", len(web_docs), search_query)
        except Exception as e:
            log.warning("Live web search collection failed gracefully: %s", e)

        saved = await self.db.save_evidence([self._prepare(doc) for doc in collected if not doc.is_demo])
        self.store.update({doc.id: doc for doc in saved})

        # 3. Filter store by relevance to target countries
        country_set = {c.lower() for c in target_countries}
        results = self.get_all()
        relevant = [
            doc for doc in results
            if not country_set or any(c.lower() in country_set for c in doc.countries_mentioned)
        ]
        
        return relevant[:18]

    def _prepare(self, doc: DocumentEvidence) -> DocumentEvidence:
        return doc.model_copy(update={
            "url": canonical_url(doc.url),
            "content_hash": content_hash(doc.title, doc.content_snippet),
        })

    async def load_evidence(self) -> None:
        for doc in await self.db.list_evidence():
            if not doc.is_demo:
                self.store[doc.id] = doc

    async def add_evidence(self, doc: DocumentEvidence) -> DocumentEvidence:
        doc = self._prepare(doc)
        if not doc.is_demo:
            doc, = await self.db.save_evidence([doc])
        self.store[doc.id] = doc
        return doc

    def get_all(self) -> List[DocumentEvidence]:
        return [doc for doc in self.store.values() if self.demo_mode or not doc.is_demo]
