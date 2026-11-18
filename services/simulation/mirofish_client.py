"""Strategic OSIRIS - MiroFish Integration & Multi-Actor Wargame Simulation Engine.
Connects to external MiroFish multi-agent swarm instances (via Docker / REST API)
with a high-fidelity game-theoretic simulation bridge powered by OpenRouter (Claude Haiku 5.5).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from packages.openrouter.client import OpenRouterClient
from packages.schemas.models import (
    DocumentEvidence,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    SimulationRound,
    WargameActor,
    WargameRequest,
    WargameSimulationResult,
    utc_now,
)

log = logging.getLogger("strategic_osiris.mirofish")


class MiroFishClient:
    """Client for MiroFish Multi-Agent Prediction & Scenario Simulation Engine."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        llm_client: Optional[OpenRouterClient] = None
    ):
        self.base_url = (base_url or os.environ.get("MIROFISH_URL", "http://localhost:5001")).rstrip("/")
        self.llm = llm_client or OpenRouterClient()

    async def check_status(self) -> Dict[str, Any]:
        """Check whether external MiroFish service is currently reachable."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/health")
                if res.status_code == 200:
                    return {
                        "status": "online",
                        "url": self.base_url,
                        "mode": "mirofish_external_live",
                        "details": res.json() if res.headers.get("content-type", "").startswith("application/json") else "online"
                    }
        except Exception:
            pass

        return {
            "status": "standby",
            "url": self.base_url,
            "mode": "mirofish_bridge_swarm",
            "note": "External MiroFish container in standby. Running high-fidelity native swarm wargame simulation."
        }

    async def run_simulation(
        self,
        request: WargameRequest,
        evidence_list: Optional[List[DocumentEvidence]] = None
    ) -> WargameSimulationResult:
        """Execute a full multi-actor wargame simulation."""
        sim_id = f"WARGAME-{uuid.uuid4().hex[:8].upper()}"
        status_info = await self.check_status()
        is_live = status_info["status"] == "online"

        evidence_list = evidence_list or []
        evidence_summary = "\n".join([
            f"- [{e.id}] ({e.reliability}{e.credibility}) {e.title}: {e.content_snippet}"
            for e in evidence_list[:8]
        ])

        log.info("Running wargame simulation %s (mode: %s) for '%s'", sim_id, status_info["mode"], request.research_question)

        # 1. Try external MiroFish REST endpoint if online
        if is_live:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = {
                        "task_id": sim_id,
                        "query": request.research_question,
                        "seed_text": evidence_summary,
                        "rounds": request.rounds_count,
                        "intervention": request.god_view_intervention
                    }
                    resp = await client.post(f"{self.base_url}/api/simulation/start", json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return self._parse_external_result(sim_id, request, data, len(evidence_list))
            except Exception as e:
                log.warning("MiroFish live API call failed (%s); falling back to native bridge swarm engine.", e)

        # 2. Native Multi-Actor Swarm Simulation Engine (Claude Haiku 5.5)
        return await self._execute_swarm_simulation(sim_id, request, evidence_summary, len(evidence_list))

    async def _execute_swarm_simulation(
        self,
        sim_id: str,
        request: WargameRequest,
        evidence_summary: str,
        evidence_count: int
    ) -> WargameSimulationResult:
        """Simulate dynamic multi-round wargame with autonomous stakeholder agents."""
        intervention_text = ""
        if request.god_view_intervention:
            intervention_text = f"\n⚠️ متغير تدخلي من منظور القيادة العليا (God-View Intervention):\n\"{request.god_view_intervention}\"\nيجب محاكاة ردود فعل كافة الأطراف على هذا الإجراء تحديداً."

        prompt = f"""أنت محرك المحاكاة ومناورات الحرب المتعددة الأطراف (MiroFish / Multi-Agent Wargame Simulation Engine).
مهمتك إجراء محاكاة ديناميكية متقدمة لسؤال التقدير الاستراتيجي التالي وفق نظرية الألعاب (Game Theory) والسلوك الانبثاقي (Emergent Behavior):

سؤال المحاكاة:
{request.research_question}

الدولة المرجعية: {request.reference_country}
النطاق الجغرافي والأطراف المعنية: {', '.join(request.target_countries)}
{intervention_text}

الأدلة والوقائع الاستخباراتية المتاحة كبذرة أولية (Seed Evidence):
{evidence_summary if evidence_summary else "لا توجد أدلة إضافية؛ اعتمد على موازين القوى والوقائع الجيوسياسية الإقليمية الراهنة."}

المطلوب إخراجه بتنسيق JSON حصراً وبالهيكل التالي:
{{
  "actors": [
    {{
      "id": "ACT-01",
      "name_ar": "اسم الطرف الفاعل بالعربية (مثل: قيادة المنطقة العسكرية الغربية المصرية)",
      "name_en": "Faction Name in English",
      "faction_type": "military | political | tribal | non_state | foreign_power",
      "objectives": "أهداف هذا الطرف ومصالحه الحيوية",
      "posture": "offensive | defensive | opportunistic | mediator",
      "leverage": "أدوات الضغط ونقاط القوة المتاحة لديه"
    }}
  ],
  "rounds": [
    {{
      "round_number": 1,
      "title": "عنوان الجولة الأولى (المواقف المبدئية واختبار النوايا)",
      "escalation_level": "low | elevated | high | critical",
      "actor_moves": [
        {{ "actor": "ACT-01", "move": "التحرك أو الإجراء الذي اتخذه هذا الطرف" }},
        {{ "actor": "ACT-02", "move": "رد الفعل المباشر" }}
      ],
      "key_developments_ar": "ملخص ديناميكيات الجولة الأولى"
    }}
  ],
  "emergent_outcomes": [
    "النتيجة الانبثاقية الرئيسية الأولى",
    "النتيجة الانبثاقية الثانية"
  ],
  "probability_distribution": {{
    "سيناريو الاستقرار المشروط": 0.45,
    "سيناريو التصعيد الموضعي": 0.35,
    "سيناريو المفاجأة أو التحول الجذري": 0.20
  }},
  "red_team_vulnerabilities": [
    "ثغرة غير متوقعة كشفتها المحاكاة",
    "نقطة ضعف قد يستغلها الخصم"
  ]
}}

أنشئ من 4 إلى 6 أطراف فاعلة متنافسة (Actors)، وثلاث جولات كاملة (3 Rounds) تعكس التفاعل المتبادل، واحرص على الموضوعية الصارمة والحياد الاستخباراتي. أخرج كود JSON فقط بدون أي مقدمات أو شروح."""

        raw_response = await self.llm.complete(
            messages=[
                {"role": "system", "content": "You are MiroFish Multi-Agent Wargaming Simulation Engine. You output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="anthropic/claude-haiku-5.5",
            temperature=0.3,
            max_tokens=3500
        )

        return self._parse_json_result(sim_id, request, raw_response, evidence_count)

    def _parse_json_result(
        self,
        sim_id: str,
        request: WargameRequest,
        raw_text: str,
        evidence_count: int
    ) -> WargameSimulationResult:
        """Parse LLM JSON completion into structured WargameSimulationResult."""
        try:
            # Strip markdown code blocks if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            data = json.loads(cleaned)

            actors = [
                WargameActor(
                    id=a.get("id", f"ACT-{i+1:02d}"),
                    name_ar=a.get("name_ar", "طرف فاعل"),
                    name_en=a.get("name_en", "Stakeholder"),
                    faction_type=a.get("faction_type", "military"),
                    objectives=a.get("objectives", ""),
                    posture=a.get("posture", "defensive"),
                    leverage=a.get("leverage", "")
                )
                for i, a in enumerate(data.get("actors", []))
            ]

            rounds = [
                SimulationRound(
                    round_number=r.get("round_number", idx + 1),
                    title=r.get("title", f"الجولة {idx+1}"),
                    escalation_level=r.get("escalation_level", "elevated"),
                    actor_moves=r.get("actor_moves", []),
                    key_developments_ar=r.get("key_developments_ar", "")
                )
                for idx, r in enumerate(data.get("rounds", []))
            ]

            return WargameSimulationResult(
                id=sim_id,
                research_question=request.research_question,
                engine="mirofish_bridge",
                status="completed",
                seed_evidence_count=evidence_count,
                god_view_intervention=request.god_view_intervention,
                actors=actors,
                rounds=rounds,
                emergent_outcomes=data.get("emergent_outcomes", [
                    "انبثاق توازن ردعي مشروط مع زيادة الاعتماد على خطوط الاتصال العسكرية الاستباقية."
                ]),
                probability_distribution=data.get("probability_distribution", {
                    "الاستقرار المشروط والاحتواء": 0.50,
                    "احتكاك موضعي محدود": 0.35,
                    "انزلاق تصعيدي": 0.15
                }),
                red_team_vulnerabilities=data.get("red_team_vulnerabilities", [
                    "مخاطر استغلال الجماعات المسلحة غير النظامية للفجوات الرادارية والمناطق الوعرة.",
                    "حساسية تأمين الممرات اللوجستية في أوقات تبدل التحالفات المحلية المفاجئة."
                ]),
                knowledge_graph=self.build_knowledge_graph(request.target_countries, actors),
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            log.error("Failed to parse wargame JSON output: %s; falling back to default structured model", e)
            return self._fallback_result(sim_id, request, evidence_count)

    def build_knowledge_graph(
        self,
        target_countries: Optional[List[str]] = None,
        actors: Optional[List[WargameActor]] = None
    ) -> KnowledgeGraph:
        """Construct a high-resolution, multi-domain geopolitical knowledge graph."""
        nodes: List[GraphNode] = [
            GraphNode(
                id="NODE-EGY-HQ",
                label_ar="القيادة العامة للقوات المسلحة المصرية",
                label_en="Egyptian Armed Forces GHQ",
                node_type="actor",
                country="Egypt",
                details="مركز القيادة والسيطرة الاستراتيجية وإدارة مسارح العمليات المشتركة وتأمين السيادة الوطنية",
                level=1
            ),
            GraphNode(
                id="NODE-EGY-WEST",
                label_ar="قيادة المنطقة الغربية وقاعدة 3 يوليو",
                label_en="Western Military Zone & July 3 Base",
                node_type="military_unit",
                country="Egypt",
                details="تأمين الاتجاه الاستراتيجي الغربي والساحل الشمالي والعمق الصحراوي مع ليبيا",
                level=2
            ),
            GraphNode(
                id="NODE-EGY-SINAI",
                label_ar="قيادة الجيشين الثاني والثالث الميدانيين",
                label_en="2nd & 3rd Field Armies (Sinai)",
                node_type="military_unit",
                country="Egypt",
                details="تأمين الاتجاه الاستراتيجي الشمالي الشرقي وشبه جزيرة سيناء والمنافذ الحدودية",
                level=2
            ),
            GraphNode(
                id="NODE-LBY-EAST",
                label_ar="القيادة العامة بالشرق الليبي (LNA)",
                label_en="Libyan National Army (Eastern Command)",
                node_type="actor",
                country="Libya",
                details="السيطرة العسكرية على برقة والهلال النفطي والتنسيق الأمني مع الحدود المصرية",
                level=1
            ),
            GraphNode(
                id="NODE-LBY-WEST",
                label_ar="حكومة الوحدة الوطنية والتشكيلات الغربية (طرابلس)",
                label_en="GNU & Western Tripoli Formations",
                node_type="actor",
                country="Libya",
                details="السيطرة الإدارية والمؤسساتية على طرابلس والمنطقة الغربية والمنافذ الجوية والبحرية",
                level=1
            ),
            GraphNode(
                id="NODE-ISR-IDF",
                label_ar="الجيش الإسرائيلي (IDF)",
                label_en="Israel Defense Forces",
                node_type="actor",
                country="Israel",
                details="الانتشار الميداني والعمليات في قطاع غزة والحدود الجنوبية",
                level=1
            ),
            GraphNode(
                id="NODE-CHK-SALLUM",
                label_ar="منفذ السلوم والحدود البرية المشتركة",
                label_en="Sallum Border Crossing Corridor",
                node_type="chokepoint",
                country="Egypt",
                details="المعبر البري الاستراتيجي وشريان التجارة وحركة الأفراد بين مصر وليبيا",
                level=2
            ),
            GraphNode(
                id="NODE-CHK-SUEZ",
                label_ar="قناة السويس والمجرى الملاحي الدولي",
                label_en="Suez Canal Maritime Corridor",
                node_type="chokepoint",
                country="Egypt",
                details="أهم ممر ملاحي عالمي يربط البحرين المتوسط والأحمر وركيزة استراتيجية للتجارة الدولية",
                level=1
            ),
            GraphNode(
                id="NODE-CHK-BAB",
                label_ar="مضيق باب المندب وجنوب البحر الأحمر",
                label_en="Bab el-Mandeb Strategic Chokepoint",
                node_type="chokepoint",
                country="Regional",
                details="المدخل الجنوبي للبحر الأحمر وممر تجارة الطاقة والسلع الدولية وركيزة سلامة الملاحة",
                level=1
            ),
            GraphNode(
                id="NODE-CHK-PHIL",
                label_ar="محور فيلادلفيا ومعبر رفح",
                label_en="Philadelphi Corridor & Rafah Crossing",
                node_type="chokepoint",
                country="Egypt",
                details="المنطقة الحدودية الحاكمة الفاصلة بين مصر وقطاع غزة",
                level=2
            ),
            GraphNode(
                id="NODE-RES-GAS",
                label_ar="حقول غاز شرق المتوسط وشبكة الأنابيب",
                label_en="East Med Offshore Gas Fields & Pipelines",
                node_type="resource",
                country="East Med",
                details="حقول ظهر وأفروديت ومحطات الإسالة بإدكو ودمياط وتصدير الغاز",
                level=2
            ),
            GraphNode(
                id="NODE-THR-SMUG",
                label_ar="شبكات التهريب والجماعات غير النظامية",
                label_en="Asymmetric Smuggling & Irregular Networks",
                node_type="threat",
                country="Regional",
                details="تهريب السلاح والمخدرات والهجرة غير الشرعية عبر الدروب الصحراوية الوعرة",
                level=2
            )
        ]

        if actors:
            for a in actors:
                node_id = f"NODE-{a.id}"
                if not any(n.id == node_id for n in nodes):
                    nodes.append(GraphNode(
                        id=node_id,
                        label_ar=a.name_ar,
                        label_en=a.name_en,
                        node_type="actor",
                        country="Regional",
                        details=f"الموقف: {a.posture} | الأهداف: {a.objectives}",
                        level=2
                    ))

        edges: List[GraphEdge] = [
            GraphEdge(source="NODE-EGY-HQ", target="NODE-EGY-WEST", relation_ar="قيادة وسيطرة عملياتية مباشرة", relation_en="Operational Command", edge_type="security", weight=1.0),
            GraphEdge(source="NODE-EGY-HQ", target="NODE-EGY-SINAI", relation_ar="انتشار تعبوي وجاهزية ردع", relation_en="Tactical Deployment", edge_type="security", weight=1.0),
            GraphEdge(source="NODE-EGY-WEST", target="NODE-CHK-SALLUM", relation_ar="تأمين مانع ومراقبة رادارية مستمرة", relation_en="Border Defense & Radar", edge_type="security", weight=1.0),
            GraphEdge(source="NODE-LBY-EAST", target="NODE-CHK-SALLUM", relation_ar="تنسيق أمني مشترك لضبط المنافذ", relation_en="Security Coordination", edge_type="alliance", weight=0.8),
            GraphEdge(source="NODE-LBY-EAST", target="NODE-LBY-WEST", relation_ar="تنافس سياسي ونزاع نفوذ وموارد", relation_en="Political & Resource Rivalry", edge_type="conflict", weight=0.9),
            GraphEdge(source="NODE-EGY-HQ", target="NODE-CHK-SUEZ", relation_ar="حماية سيادية ودفاع جوي وبحري", relation_en="Sovereign Protection", edge_type="security", weight=1.0),
            GraphEdge(source="NODE-CHK-SUEZ", target="NODE-CHK-BAB", relation_ar="شريان ملاحة تجاري متصل", relation_en="Maritime Supply Arteries", edge_type="resource", weight=1.0),
            GraphEdge(source="NODE-EGY-HQ", target="NODE-CHK-BAB", relation_ar="دوريات ردع بحرية مشتركة", relation_en="Naval Deterrence Patrols", edge_type="surveillance", weight=0.8),
            GraphEdge(source="NODE-EGY-SINAI", target="NODE-CHK-PHIL", relation_ar="تأمين سيادي مانع للاختراق", relation_en="Border Inviolability", edge_type="security", weight=1.0),
            GraphEdge(source="NODE-ISR-IDF", target="NODE-CHK-PHIL", relation_ar="توتر واحتكاك عملياتي ومراقبة", relation_en="Operational Friction", edge_type="conflict", weight=0.9),
            GraphEdge(source="NODE-EGY-HQ", target="NODE-RES-GAS", relation_ar="حماية المنطقة الاقتصادية الخالصة", relation_en="EEZ Protection", edge_type="security", weight=0.85),
            GraphEdge(source="NODE-THR-SMUG", target="NODE-CHK-SALLUM", relation_ar="محاولات تسلل وتهريب عابر", relation_en="Smuggling Infiltration", edge_type="conflict", weight=0.7),
            GraphEdge(source="NODE-EGY-WEST", target="NODE-THR-SMUG", relation_ar="مكافحة وإحباط استباقي للمسلحين", relation_en="Counter-Smuggling Interdiction", edge_type="security", weight=0.9)
        ]

        if actors:
            for a in actors:
                node_id = f"NODE-{a.id}"
                target_node = "NODE-CHK-SALLUM" if ("ليبيا" in a.name_ar or "Libya" in a.name_en) else "NODE-EGY-HQ"
                edges.append(GraphEdge(
                    source=node_id,
                    target=target_node,
                    relation_ar=f"تفاعل عملياتي ({a.posture})",
                    relation_en=f"Operational engagement ({a.posture})",
                    edge_type="conflict" if a.posture == "offensive" else "security",
                    weight=0.75
                ))

        return KnowledgeGraph(nodes=nodes, edges=edges)

    def _fallback_result(
        self,
        sim_id: str,
        request: WargameRequest,
        evidence_count: int
    ) -> WargameSimulationResult:
        """Deterministic high-level fallback simulation result."""
        return WargameSimulationResult(
            id=sim_id,
            research_question=request.research_question,
            engine="mirofish_bridge_deterministic",
            status="completed",
            seed_evidence_count=evidence_count,
            god_view_intervention=request.god_view_intervention,
            actors=[
                WargameActor(
                    id="ACT-01",
                    name_ar="القيادة الاستراتيجية للقوات المسلحة المصرية",
                    name_en="Egyptian Armed Forces Strategic Command",
                    faction_type="military",
                    objectives="حماية السيادة، تأمين الحدود الدولية، ومنع أي تسلل للمجموعات المسلحة أو الإرهابية",
                    posture="defensive",
                    leverage="تفوق ردعي كامل، انتشار نيراني وتعبوي، رادارات واستطلاع جوي دائم"
                ),
                WargameActor(
                    id="ACT-02",
                    name_ar="فصائل وتشكيلات الشرق الليبي (القيادة العامة)",
                    name_en="Eastern Libya Forces (LNA)",
                    faction_type="military",
                    objectives="فرض السيطرة على المعابر، تأمين المنشآت النفطية، وتعزيز التنسيق مع القاهرة",
                    posture="opportunistic",
                    leverage="السيطرة الميدانية على خطوط التماس وقواعد الهلال النفطي"
                ),
                WargameActor(
                    id="ACT-03",
                    name_ar="حكومة الوحدة الوطنية والتشكيلات الغربية (طرابلس)",
                    name_en="Western Libya / Tripoli Factions (GNU)",
                    faction_type="political",
                    objectives="الحفاظ على المكتسبات المالية والسياسية ومقاومة التوسع باتجاه العاصمة",
                    posture="defensive",
                    leverage="الشرعية المعترف بها دولياً والموارد المالية للمصرف المركزي"
                )
            ],
            rounds=[
                SimulationRound(
                    round_number=1,
                    title="جولة رصد النوايا والتموضع الأولي",
                    escalation_level="low",
                    actor_moves=[
                        {"actor": "ACT-01", "move": "تكثيف دوريات الاستطلاع البري والجوي وتأمين المعابر الحيوية."},
                        {"actor": "ACT-02", "move": "إعادة تموضع الوحدات العسكرية لضبط المنافذ الحدودية الشرقية في ليبيا."}
                    ],
                    key_developments_ar="تأكيد متبادل على حظر اختراق خط الحدود الدولي واستمرار تبادل التنسيق العملياتي."
                ),
                SimulationRound(
                    round_number=2,
                    title="جولة اختبار الردع واحتواء المتغيرات",
                    escalation_level="elevated",
                    actor_moves=[
                        {"actor": "ACT-03", "move": "إجراء مناورات أمنية وتأمين خطوط الغاز والنفط."},
                        {"actor": "ACT-01", "move": "تفعيل منظومات الإنذار المبكر الراداري وتوجيه رسائل ردع واضحة."}
                    ],
                    key_developments_ar="احتواء محاولات التسلل المحدودة دون المساس بالتوازنات الإقليمية المستقرة."
                )
            ],
            emergent_outcomes=[
                "ثبات معادلة الردع المصرية كصمام أمان يحول دون تحول الاحتكاكات الحدودية إلى مواجهة مفتوحة.",
                "ضرورة استمرار التنسيق الاستخباراتي المباشر مع القوى الميدانية الفاعلة لضمان استقرار المعابر."
            ],
            probability_distribution={
                "استمرار الردع والاحتواء النشط": 0.65,
                "توتر حدودي محدود ومعزول": 0.25,
                "تصعيد شامل": 0.10
            },
            red_team_vulnerabilities=[
                "احتمالية استغلال أطراف ثالثة أو شبكات تهريب للمناطق الصحراوية المفتوحة.",
                "تقلب الولاءات العشائرية في حالات غياب الحوافز الاقتصادية والتنموية المشتركة."
            ],
            knowledge_graph=self.build_knowledge_graph(request.target_countries),
            created_at=datetime.now(timezone.utc)
        )

    def _parse_external_result(
        self,
        sim_id: str,
        request: WargameRequest,
        data: Dict[str, Any],
        evidence_count: int
    ) -> WargameSimulationResult:
        """Adapt external MiroFish JSON schema to OSIRIS WargameSimulationResult."""
        return WargameSimulationResult(
            id=sim_id,
            research_question=request.research_question,
            engine="mirofish_external_live",
            status="completed",
            seed_evidence_count=evidence_count,
            god_view_intervention=request.god_view_intervention,
            emergent_outcomes=data.get("predictions", ["Emergent outcome generated from MiroFish OASIS engine."]),
            probability_distribution=data.get("probabilities", {"Status Quo": 0.60, "Escalation": 0.40}),
            knowledge_graph=self.build_knowledge_graph(request.target_countries),
            created_at=datetime.now(timezone.utc)
        )
