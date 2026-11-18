"""Strategic OSIRIS - Geopolitical & Defense Knowledge Base Engine.
Provides persistent storage, semantic/lexical hybrid retrieval, and intelligence ingestion
for strategic defense doctrines, maritime chokepoints, treaties, and geopolitical precedents.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from packages.schemas.models import (
    AdmiraltyCredibility,
    AdmiraltyReliability,
    DocumentEvidence,
    KnowledgeDocument,
    KnowledgeSearchResponse,
    utc_now,
)

log = logging.getLogger("strategic_osiris.knowledge")

DEFAULT_KNOWLEDGE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "id": "DOC-EGY-001",
        "title_ar": "العقيدة العسكرية الدفاعية وتأمين الاتجاهات الاستراتيجية للدولة المصرية",
        "title_en": "Egyptian Defense Doctrine & Strategic Axes Security Architecture",
        "category": "doctrine",
        "country_coverage": ["Egypt", "Libya", "Israel", "Red Sea"],
        "summary": "المرتكزات الأساسية للعقيدة القتالية المصرية: حماية السيادة الوطنية، الردع الشامل، وتأمين الاتجاهات الاستراتيجية الثلاثة (الشمالي الشرقي، الغربي، الجنوبي والبحري).",
        "content": (
            "ترتكز العقيدة العسكرية للقوات المسلحة المصرية على مبدأ 'الردع الاستراتيجي الفعال' والدفاع الوقائي غير المعتدي. "
            "يتوزع المسرح العملياتي إلى ثلاثة اتجاهات استراتيجية حاسمة:\n"
            "1. الاتجاه الاستراتيجي الشمالي الشرقي (سيناء والمنافذ الحدودية): تتولى قيادة الجيشين الثاني والثالث الميدانيين "
            "تأمين شبكة خطوط الدفاع الحيوية والمضايق وقناة السويس مع فرض سيطرة سيادية كاملة على طول خط الحدود الدولية ومعبر رفح ومحور فيلادلفيا، "
            "ورفض أي سيناريوهات للتهجير القسري أو المساس بالأمن القومي.\n"
            "2. الاتجاه الاستراتيجي الغربي (الحدود الليبية): تتولى المنطقة العسكرية الغربية وقاعدة 3 يوليو البحرية والجوية (جرجوب) "
            "وقاعدة محمد نجيب تأمين خط الحدود الممتد لأكثر من 1115 كم، وتطبيق خطوط حمراء استراتيجية لمنع تسلل التنظيمات الإرهابية أو السيطرة الأجنبية على خط سرت-الجفرة.\n"
            "3. الاتجاه الاستراتيجي الجنوبي والبحري (البحر الأحمر والقرن الإفريقي): تتولى قاعدة برنيس العسكرية والأسطول الجنوبي "
            "تأمين حركة الملاحة باتجاه مضيق باب المندب، وتأمين المنشآت الاقتصادية ومكافحة القرصنة والتهديدات غير النمطية."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "القيادة العامة للقوات المسلحة المصرية", "الجيش الثاني الميداني", "الجيش الثالث الميداني",
            "المنطقة العسكرية الغربية", "قاعدة 3 يوليو", "قاعدة برنيس", "محور فيلادلفيا", "سرت-الجفرة"
        ],
        "sources": [
            "وزارة الدفاع المصرية - البيانات العسكرية الرسمية",
            "مركز الأهرام للدراسات السياسية والاستراتيجية",
            "The Military Balance - IISS"
        ]
    },
    {
        "id": "DOC-MR-002",
        "title_ar": "النظام الأمني ومحددات الملاحة بمضيق باب المندب وقناة السويس",
        "title_en": "Maritime Security & Chokepoint Regime: Bab el-Mandeb & Suez Canal",
        "category": "chokepoint",
        "country_coverage": ["Egypt", "Yemen", "Red Sea", "Regional"],
        "summary": "القواعد القانونية لاتفاقية الأمم المتحدة لأعالي البحار (UNCLOS)، آليات الردع ضد التهديدات غير النمطية، والآثار الاقتصادية لتعطيل الملاحة على إيرادات قناة السويس والتجارة الدولية.",
        "content": (
            "يُعد مضيق باب المندب عنق الزجاجة الاستراتيجي للتجارة العالمية الرابطة بين المحيط الهندي والبحر الأبيض المتوسط عبر قناة السويس.\n"
            "1. النظام القانوني: يخضع المرور في مضيق باب المندب لنظام 'المرور العابر' (Transit Passage) وفقاً لاتفاقية الأمم المتحدة لقانون البحار (UNCLOS 1982)، "
            "والذي يضمن حرية الملاحة البحرية والجوية لجميع السفن دون إعاقة، بشرط الامتناع عن أي عمل عدائي.\n"
            "2. التهديدات غير النمطية: تشمل هجمات الزوارق المسيرة غير المأهولة (USVs)، الصواريخ الباليستية والمجنحة المضادة للسفن (ASBMs/ASCMs)، "
            "والألغام البحرية الطافية التي تهدد ناقلات النفط وسفن الحاويات العملاقة.\n"
            "3. الآثار الجيواقتصادية على مصر: يؤدي تحويل مسار السفن التجارية حول رأس الرجاء الصالح إلى انخفاض عائدات قناة السويس "
            "بنسب تتجاوز 40-50%، مما يشكل ضغطاً على ميزان المدفوعات والسيولة الدولارية، ويستدعي تحركات دبلوماسية ودوريات بحرية متواصلة لحفظ الاستقرار."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "قناة السويس", "مضيق باب المندب", "الأسطول الجنوبي المصري", "حركة أنصار الله (الحوثيون)",
            "اتفاقية UNCLOS", "رأس الرجاء الصالح", "قوة المهام المشتركة 153"
        ],
        "sources": [
            "هيئة قناة السويس - التقارير الإحصائية للملاحة",
            "International Maritime Organization (IMO) Circulars",
            "United Nations Convention on the Law of the Sea (UNCLOS)"
        ]
    },
    {
        "id": "DOC-LBY-003",
        "title_ar": "الهيكل الأمني الليبي وتوازنات القوى العسكرية والحدود المشتركة",
        "title_en": "Libyan Security Architecture, Military Balances & Border Regimes",
        "category": "conflict_history",
        "country_coverage": ["Libya", "Egypt"],
        "summary": "توزيع السيطرة الميدانية بين القيادة العامة في الشرق (LNA) وحكومة الوحدة الوطنية في الغرب (GNU)، مسار اللجنة العسكرية المشتركة (5+5)، وبروتوكولات تأمين الحدود.",
        "content": (
            "يتسم المشهد الأمني الليبي بالانقسام المؤسسي والميداني وتوازن الردع الحذر:\n"
            "1. المعسكر الشرقي (LNA): تقوده القيادة العامة في الرجمة ببنغازي، ويسيطر على إقليم برقة، منطقة الهلال النفطي الحيوية، والحدود الجنوبية والشرقية. "
            "يرتبط بتنسيق أمني عالي المستوى مع الأجهزة المصرية لضبط الحدود ومكافحة شبكات الهجرة غير الشرعية وتهريب السلاح.\n"
            "2. المعسكر الغربي (GNU/طرابلس): حكومة الوحدة الوطنية وتشكيلات المنطقة الغربية ومصراتة وجهاز الردع واللواء 444، وتتحكم بالمنافذ الرسمية كمعبر رأس جدير ومطار معيتيقة.\n"
            "3. خط التماس والاستقرار: يشكل خط 'سرت - الجفرة' التوازن العسكري الحرج الذي كرسته مخرجات إعلان القاهرة 2020، "
            "وتعمل اللجنة العسكرية المشتركة (5+5) برعاية أممية على تثبيت وقف إطلاق النار وتفكيك الميليشيات وإخراج المرتزقة والقوات الأجنبية لضمان سلامة وحدة الأراضي الليبية."
        ),
        "reliability": AdmiraltyReliability.B,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "الجيش الوطني الليبي (LNA)", "حكومة الوحدة الوطنية (GNU)", "اللجنة العسكرية المشتركة (5+5)",
            "معبر السلوم - مساعد", "الهلال النفطي", "معبر رأس جدير", "إعلان القاهرة 2020"
        ],
        "sources": [
            "بعثة الأمم المتحدة للدعم في ليبيا (UNSMIL)",
            "تقارير فريق الخبراء المعني بليبيا التابع لمجلس الأمن",
            "بيانات القيادة العامة - الرجمة"
        ]
    },
    {
        "id": "DOC-EMED-004",
        "title_ar": "أمن الطاقة والترسيم البحري في حوض شرق المتوسط",
        "title_en": "Eastern Mediterranean Maritime Security & Offshore Energy Architecture",
        "category": "treaty",
        "country_coverage": ["Egypt", "Israel", "East Med", "Regional"],
        "summary": "منتدى غاز شرق المتوسط (EMGF)، حماية حقول الغاز البحرية العملاقة (ظهر، ليفياثان، أفروديت)، واتفاقيات ترسيم الحدود البحرية الإقليمية.",
        "content": (
            "تحول حوض شرق المتوسط إلى بؤرة للتنافس الجيوسياسي ومحور للتعاون الطاقوي الإقليمي:\n"
            "1. منتدى غاز شرق المتوسط (EMGF): ومقره الدائم القاهرة، يمثل المظلة الإقليمية للتحول إلى مركز إقليمي لتداول وتجارة الغاز الطبيعي "
            "عبر استغلال مصانع إسالة الغاز في إدكو ودمياط لإعادة تصديره إلى الأسواق الأوروبية.\n"
            "2. حماية البنية التحتية الحرجة: تنشر البحرية المصرية فرقاطات الفريم (FREMM) وميكو (MEKO A-200) وحاملات المروحيات الميسترال "
            "لتأمين حقل ظهر ومنصات الإنتاج ضد أي تهديدات سيبرانية أو عمليات تخريبية تحت سطح البحر.\n"
            "3. اتفاقيات التعيين البحري: تستند مصر إلى اتفاقيات الترسيم القانونية مع قبرص (2003) واليونان (2020) المتوافقة مع قانون البحار الدولي، "
            "مما يوفر غطاءً تشريعياً واستثمارياً لشركات الطاقة العالمية (Eni, BP, Chevron) لاستكمال أعمال الاستكشاف في المياه العميقة."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "منتدى غاز شرق المتوسط (EMGF)", "حقل ظهر للغاز", "محطة إسالة الغاز بإدكو ودمياط",
            "حاملة المروحيات ميسترال", "اتفاقية الترسيم البحري مصر-اليونان", "شركة إيني (Eni)"
        ],
        "sources": [
            "وزارة البترول والثروة المعدنية المصرية",
            "ميثاق منتدى غاز شرق المتوسط (القاهرة)",
            "Eastern Mediterranean Energy Security Review - S&P Global"
        ]
    },
    {
        "id": "DOC-SYR-005",
        "title_ar": "إعادة هيكلة القوات والمشهد الأمني السوري بعد تحولات ديسمبر 2024",
        "title_en": "Post-Dec 2024 Syrian Security Architecture & Transitional Defense Realignment",
        "category": "military_analysis",
        "country_coverage": ["Syria", "Israel", "Regional"],
        "summary": "توثيق التشكيلات الميدانية وترتيب المعركة (GeoConfirmed Node 6474)، جهاز الأمن العام (GSS)، وخطوط فض الاشتباك مع إسرائيل في الجولان.",
        "content": (
            "بعد التحولات الاستراتيجية الكبرى في سوريا في ديسمبر 2024، أظهرت بيانات الرصد الجغرافي العسكري (GeoConfirmed ORBAT Node 6474) خريطة جديدة للقوى:\n"
            "1. إعادة هيكلة المؤسسات الأمنية: تبرز وحدات جهاز الأمن العام (General Security Service - GSS / عقدة 6476) "
            "والتي تولت ضبط الأمن الداخلي وحماية المنشآت الحيوية في حلب ودمشق ومحيطها الجغرافي.\n"
            "2. القوات المسلحة السورية الانتقالية (العقدتان 6477 و6478): مساعي دمج التشكيلات وتثبيت انتشار الجيش السوري الجديد في غرف العمليات المشتركة "
            "للسيطرة على المعابر البرية ومستودعات الذخيرة والمطارات العسكرية.\n"
            "3. الجبهة الجنوبية وخط وقف إطلاق النار: تصاعد الضغوط على خط فض الاشتباك 1974 في الجولان السوري المحتل، "
            "مع محاولات إسرائيلية لتوسيع المنطقة العازلة وتأمين قمة جبل الشيخ ومراقبة أي انتشار عسكري قد يهدد العمق الشمالي لإسرائيل."
        ),
        "reliability": AdmiraltyReliability.B,
        "credibility": AdmiraltyCredibility.TWO,
        "key_entities": [
            "GeoConfirmed ORBAT Node 6474", "جهاز الأمن العام (GSS)", "القوات المسلحة السورية",
            "هيئة العمليات المشتركة", "مرتفعات الجولان", "اتفاقية فض الاشتباك 1974"
        ],
        "sources": [
            "GeoConfirmed OSINT Syria Conflict Database",
            "Syrian Observatory for Human Rights (SOHR)",
            "Institute for the Study of War (ISW) Syria Updates"
        ]
    },
    {
        "id": "DOC-SDN-006",
        "title_ar": "توازنات النزاع السوداني وتداعياته على أمن البحر الأحمر والعمق الاستراتيجي المصري",
        "title_en": "Sudan Conflict Balances, Red Sea Coast & Egyptian Strategic Depth",
        "category": "conflict_history",
        "country_coverage": ["Sudan", "Egypt", "Red Sea"],
        "summary": "خريطة المواجهات بين القوات المسلحة السودانية (SAF) وقوات الدعم السريع (RSF)، تأمين ميناء بورتسودان، وأمن مياه النيل والحدود الجنوبية المصرية.",
        "content": (
            "يمثل النزاع في السودان تحدياً مباشراً للأمن القومي المصري ولمنظومة أمن حوض البحر الأحمر:\n"
            "1. التمركز العسكري: تحتفظ القوات المسلحة السودانية (SAF) بالسيطرة على ولايات الشرق والساحل البحري (بورتسودان) "
            "والشمال، بينما تنتشر قوات الدعم السريع (RSF) في أجزاء واسعة من الخرطوم ودارفور والجزيرة.\n"
            "2. العمق الجنوبي المصري: يمثل استقرار السودان خط الدفاع المتقدم للأمن المائي المصري (نهر النيل) والحدود البرية الجنوبية عبر معبري قسطل وأرقين، "
            "حيث ترفض مصر أي تفكك للجيش الوطني السوداني وتدعم مؤسسات الدولة الرسمية.\n"
            "3. البعد الإقليمي: محاولات القوى الدولية والإقليمية لإيجاد موطئ قدم على ساحل البحر الأحمر السوداني تفرض تنسيقاً مصرياً-سودانياً مكثفاً "
            "لمنع إقامة أي قواعد عسكرية أجنبية غير متوافق عليها إقليمياً."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "القوات المسلحة السودانية (SAF)", "قوات الدعم السريع (RSF)", "ميناء بورتسودان",
            "معبر قسطل وأرقين", "أمن مياه النيل", "قمة دول جوار السودان"
        ],
        "sources": [
            "القوات المسلحة السودانية - الإيجازات الميدانية",
            "تقارير الاتحاد الإفريقي ولجنة الإيقاد (IGAD)",
            "مركز الأهرام - أوراق حول الأزمة السودانية"
        ]
    }
]


class KnowledgeEngine:
    """Core repository and search engine for strategic intelligence documents."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            root_dir = Path(__file__).resolve().parent.parent.parent
            self.data_dir = root_dir / "data" / "knowledge_base"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_file = self.data_dir / "documents.json"
        self._documents: Dict[str, KnowledgeDocument] = {}
        self._load_or_initialize()

    def _load_or_initialize(self) -> None:
        """Load documents from disk or seed with comprehensive baseline."""
        if self.documents_file.exists():
            try:
                with open(self.documents_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        doc = KnowledgeDocument(**item)
                        self._documents[doc.id] = doc
                log.info("Loaded %d strategic documents from %s", len(self._documents), self.documents_file)
                return
            except Exception as e:
                log.warning("Could not read knowledge file %s: %s. Re-seeding defaults.", self.documents_file, e)

        # Seed defaults
        for item in DEFAULT_KNOWLEDGE_DOCUMENTS:
            doc = KnowledgeDocument(**item)
            self._documents[doc.id] = doc
        self._save_to_disk()
        log.info("Initialized knowledge base with %d default documents", len(self._documents))

    def _save_to_disk(self) -> None:
        """Persist current documents to JSON."""
        try:
            raw = [doc.model_dump(mode="json") for doc in self._documents.values()]
            with open(self.documents_file, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error("Failed to save knowledge documents to disk: %s", e)

    def get_all(self) -> List[KnowledgeDocument]:
        """Return all knowledge documents sorted by ID."""
        return sorted(self._documents.values(), key=lambda d: d.id)

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve a specific document by its ID."""
        return self._documents.get(doc_id)

    def ingest_document(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        """Add or update a strategic intelligence document."""
        self._documents[doc.id] = doc
        self._save_to_disk()
        log.info("Ingested knowledge document %s (%s)", doc.id, doc.title_ar)
        return doc

    def search(
        self,
        query: str,
        target_countries: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Tuple[KnowledgeDocument, float]]:
        """Hybrid lexical & semantic relevance search across knowledge documents."""
        query_clean = re.sub(r"[^\w\s]", " ", query.lower())
        tokens = set(t for t in query_clean.split() if len(t) > 2)

        country_tokens = set(c.lower() for c in (target_countries or []))
        scored_results: List[Tuple[KnowledgeDocument, float]] = []

        for doc in self._documents.values():
            score = 0.0

            # 1. Category filter
            if category and category.lower() != "all" and doc.category.lower() != category.lower():
                continue

            # 2. Country relevance (heavy weight)
            doc_countries = {c.lower() for c in doc.country_coverage}
            overlap = country_tokens.intersection(doc_countries)
            if overlap:
                score += len(overlap) * 35.0
            elif "regional" in doc_countries and country_tokens:
                score += 15.0

            # 3. Text & Entity matching
            doc_text = f"{doc.title_ar} {doc.title_en} {doc.summary} {doc.content} {' '.join(doc.key_entities)}".lower()
            
            # Exact phrase matches
            if query.lower() in doc_text:
                score += 40.0

            # Token overlap
            token_hits = sum(1 for t in tokens if t in doc_text)
            score += token_hits * 10.0

            # Key entities direct match
            for entity in doc.key_entities:
                if any(t in entity.lower() for t in tokens):
                    score += 15.0

            # Admiralty quality bonus
            if doc.reliability == AdmiraltyReliability.A:
                score += 5.0
            if doc.credibility == AdmiraltyCredibility.ONE:
                score += 5.0

            if score > 0.0 or not tokens:
                # If no search query, return default baseline weight
                scored_results.append((doc, score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:limit]

    def search_as_evidence(
        self,
        query: str,
        target_countries: List[str],
        limit: int = 3
    ) -> List[DocumentEvidence]:
        """Convert top matching strategic documents directly into DocumentEvidence items for the 14 agents."""
        scored = self.search(query=query, target_countries=target_countries, limit=limit)
        evidences: List[DocumentEvidence] = []

        for doc, score in scored:
            evidences.append(
                DocumentEvidence(
                    id=f"EVD-KB-{doc.id}",
                    source_id=f"SRC-KB-{doc.id}",
                    source_name=f"Strategic Knowledge Base ({doc.category.upper()})",
                    title=doc.title_ar,
                    url=next((source for source in doc.sources if source.startswith(("https://", "http://"))), None),
                    content_snippet=doc.summary + " " + doc.content[:280] + "...",
                    reliability=doc.reliability,
                    credibility=doc.credibility,
                    countries_mentioned=doc.country_coverage,
                    tags=["doctrine", doc.category] + [e[:20] for e in doc.key_entities[:3]],
                    published_at=doc.published_at
                )
            )

        return evidences


# Singleton instance
knowledge_engine = KnowledgeEngine()
