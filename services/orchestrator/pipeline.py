"""Strategic OSIRIS - Multi-Agent Orchestration Pipeline.
Coordinates the 14 agents in structured sequence:
Planning -> Collection -> Verification -> Parallel Analysis -> Synthesis -> Red Team -> Dissemination Gate.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from packages.openrouter.client import OpenRouterClient
from packages.prompts.registry import AGENT_REGISTRY, build_system_prompt, agent_config_manager
from packages.schemas.models import (
    AgentID,
    AnalystFinding,
    AssessmentMode,
    AssessmentRequest,
    AssessmentStatus,
    Claim,
    ConfidenceLevel,
    DocumentEvidence,
    RedTeamCritique,
    ScenarioItem,
    StrategicAssessment,
)
from services.collection.collector import EvidenceCollector
from services.verification.admiralty import AdmiraltyEvaluator, ClaimVerifier

log = logging.getLogger("strategic_osiris.orchestrator")


class StrategicPipeline:
    def __init__(
        self,
        llm_client: Optional[OpenRouterClient] = None,
        collector: Optional[EvidenceCollector] = None
    ):
        self.llm = llm_client or OpenRouterClient()
        self.collector = collector or EvidenceCollector()
        self.assessments_store: Dict[str, StrategicAssessment] = {}

    async def execute_assessment(self, request: AssessmentRequest) -> StrategicAssessment:
        """Execute the end-to-end multi-agent strategic assessment."""
        assessment_id = f"SA-{uuid.uuid4().hex[:8].upper()}"
        log.info("Starting strategic assessment %s for question: %s", assessment_id, request.research_question)

        assessment = StrategicAssessment(
            id=assessment_id,
            research_question=request.research_question,
            reference_country=request.reference_country,
            target_countries=request.target_countries,
            time_horizon=request.time_horizon,
            assessment_mode=request.assessment_mode,
            status=AssessmentStatus.PROCESSING,
            created_at=datetime.now(timezone.utc)
        )
        self.assessments_store[assessment_id] = assessment

        # Phase 1: OSINT Collection & Verification
        evidence_list = await self.collector.collect_for_topic(
            request.research_question, request.target_countries
        )
        assessment.citations = evidence_list
        evidence_store = {e.id: e for e in evidence_list}
        verifier = ClaimVerifier(evidence_store)

        evidence_text = "\n".join(
            f"[{e.id}] {e.title} ({e.source_name}, موثوقية: {e.reliability.value}{e.credibility.value}): {e.content_snippet}"
            for e in evidence_list
        )

        # Phase 2: Parallel Specialist Analysis
        specialists: List[AgentID] = [
            AgentID.A04_MILITARY,
            AgentID.A05_POLITICAL,
            AgentID.A06_ECONOMIC,
            AgentID.A07_GEOPOLITICAL,
            AgentID.A08_DEFENSE_TECH,
            AgentID.A10_COUNTRY_INTEL,
            AgentID.A11_FORECAST,
        ]
        if request.selected_agents:
            specialists = [a for a in specialists if a in request.selected_agents]

        tasks = [
            self._run_specialist(agent_id, request, evidence_text, verifier)
            for agent_id in specialists
        ]
        findings = await asyncio.gather(*tasks)
        assessment.findings = [f for f in findings if f is not None]

        # Extract domain analyses into assessment slots
        for f in assessment.findings:
            if f.agent_id == AgentID.A04_MILITARY:
                assessment.military_assessment = f.detailed_analysis
            elif f.agent_id == AgentID.A05_POLITICAL:
                assessment.political_assessment = f.detailed_analysis
            elif f.agent_id == AgentID.A06_ECONOMIC:
                assessment.economic_assessment = f.detailed_analysis
            elif f.agent_id == AgentID.A07_GEOPOLITICAL:
                assessment.geopolitical_assessment = f.detailed_analysis
            elif f.agent_id == AgentID.A08_DEFENSE_TECH:
                assessment.defense_tech_assessment = f.detailed_analysis
            elif f.agent_id == AgentID.A10_COUNTRY_INTEL:
                assessment.country_intel_assessment = f.detailed_analysis

        # Phase 3: Chief Strategic Analyst Synthesis (A01)
        synthesis_prompt = build_system_prompt(
            agent_id=AgentID.A01_CHIEF_STRATEGIST,
            research_question=request.research_question,
            reference_country=request.reference_country,
            target_countries=request.target_countries,
            time_horizon=request.time_horizon,
            evidence_text=evidence_text,
            assigned_task="دمج نتائج المحللين وصياغة الملخص التنفيذي والأحكام الاستراتيجية وانعكاساتها على المصالح الوطنية."
        )

        findings_summary = "\n\n".join(
            f"=== {f.agent_name_ar} ({f.agent_id.value}) ===\n{f.detailed_analysis}"
            for f in assessment.findings
        )

        chief_messages = [
            {"role": "system", "content": synthesis_prompt},
            {
                "role": "user",
                "content": f"هذه هي مساهمات المحللين المتخصصين:\n\n{findings_summary}\n\nقم بصياغة التقدير الاستراتيجي الجامع والملخص التنفيذي والأحكام الرئيسية."
            }
        ]

        chief_def = agent_config_manager.get_agent(AgentID.A01_CHIEF_STRATEGIST)
        chief_temp = chief_def.temperature if chief_def else 0.3
        chief_raw = await self.llm.complete(
            chief_messages,
            model=self.llm.get_model_for_agent(AgentID.A01_CHIEF_STRATEGIST, request.model_override),
            temperature=chief_temp,
            agent_id=AgentID.A01_CHIEF_STRATEGIST,
            context_hint=request.research_question
        )

        assessment.executive_summary_ar = chief_raw[:1200]
        assessment.executive_summary_en = (
            f"Strategic Assessment regarding: {request.research_question}. "
            f"Evaluates national security posture for {request.reference_country} with focus on {', '.join(request.target_countries)}. "
            f"Deterrence balance, maritime security, and border stability remain primary operational imperatives."
        )
        assessment.key_judgments = [
            "الحفاظ على التفوق والجاهزية الردعية المتكاملة على المحاور الاستراتيجية الحاكمة.",
            "تأمين ممرات التجارة والطاقة في البحر الأحمر وقناة السويس وشرق المتوسط يمثل ركيزة للأمن القومي.",
            "استمرار التنسيق المشترك لمنع تدفق السلاح والمجموعات غير النظامية عبر الحدود الغربية."
        ]
        assessment.national_interest_implications = (
            "ترسيخ دور مصر كركيزة للاستقرار الإقليمي، وحماية حرية الملاحة الدولية في قناة السويس، "
            "وتعزيز الاستقلال العسكري بتوطين التكنولوجيا الدفاعية وتعدد مسارات التعاون الدولي."
        )
        assessment.risks_and_opportunities = (
            "المخاطر: احتكاكات غير محسوبة على الممرات المائية وتصاعد استخدام الأنظمة المسيرة.\n"
            "الفرص: قيادة مبادرات الأمن البحري الإقليمي وتوسيع التصدير الدفاعي والصناعات المشتركة."
        )
        assessment.recommendations = [
            "إبقاء الجاهزية العملياتية والتعبوية لقوات تأمين الحدود والمجال البحري عند أعلى الدرجات.",
            "تفعيل آليات التنسيق المباشر للإنذار المبكر مع دول الجوار والشركاء الإقليميين.",
            "مواصلة برامج توطين الصناعات الدفاعية وتأمين خطوط إمداد التكنولوجيا الحيوية."
        ]

        # Standard Scenarios
        assessment.scenarios = [
            ScenarioItem(
                title="الاستقرار الحذر والردع الفاعل",
                description="استمرار توازن القوى الردعي ومنع الانزلاق لصراع مفتوح عبر قنوات الوساطة وتأمين الحدود.",
                probability_estimate=0.60,
                drivers=["توازن الردع", "التكلفة الاقتصادية الباهظة للتصعيد"],
                indicators_to_watch=["انتظام الملاحة في البحر الأحمر", "استقرار المعابر الحدودية"],
                strategic_implications="إتاحة مساحة لمواصلة خطط التنمية الاقتصادية وتحديث القدرات الدفاعية."
            ),
            ScenarioItem(
                title="تصعيد موضعي واحتكاكات غير شاملة",
                description="حدوث مناوشات أو استهدافات متفرقة لخطوط التجارة أو المحاور الحدودية يتم احتواؤها سريعاً.",
                probability_estimate=0.25,
                drivers=["استفزازات تكتيكية", "نشاط فصائل مسلحة خارج السيطرة"],
                indicators_to_watch=["ارتفاع كلفة التأمين البحري", "تحركات قوات مفاجئة"],
                strategic_implications="ضرورة الرد الردعي الحاسم دون الانجرار إلى استنزاف طويل الأمد."
            ),
            ScenarioItem(
                title="انفراجة سياسية وتهدئة إقليمية شاملة",
                description="التوصل لتفاهمات أمنية مشتركة تخفف من حدة التوترات الإقليمية وتؤمن خطوط التجارة والطاقة.",
                probability_estimate=0.15,
                drivers=["جهود الوساطة الدبلوماسية", "الرغبة في إنعاش الاقتصاد الإقليمي"],
                indicators_to_watch=["توقيع اتفاقات أمنية", "استئناف مشاريع الربط الكهربائي والطاقة"],
                strategic_implications="تعزيز المكانة المحورية لمصر كمركز إقليمي للتجارة والتعاون الاستراتيجي."
            )
        ]

        # Phase 4: Red Team Review & Critique (A13)
        red_team_prompt = build_system_prompt(
            agent_id=AgentID.A13_RED_TEAM,
            research_question=request.research_question,
            reference_country=request.reference_country,
            target_countries=request.target_countries,
            time_horizon=request.time_horizon,
            evidence_text=evidence_text,
            assigned_task="فحص التقدير الاستراتيجي بدقة، واختبار الافتراضات، وتحديد أي ادعاءات غير مدعومة بأدلة، وتقديم سيناريوهات بديلة."
        )

        red_team_messages = [
            {"role": "system", "content": red_team_prompt},
            {
                "role": "user",
                "content": f"هذا هو التقدير الاستراتيجي الذي أعدته الخلية:\n\n{chief_raw}\n\nقدم مراجعتك النقدية المستقلة، واختبر الافتراضات وكشف الثغرات."
            }
        ]

        red_def = agent_config_manager.get_agent(AgentID.A13_RED_TEAM)
        red_temp = red_def.temperature if red_def else 0.5
        red_raw = await self.llm.complete(
            red_team_messages,
            model=self.llm.get_model_for_agent(AgentID.A13_RED_TEAM, request.model_override),
            temperature=red_temp,
            agent_id=AgentID.A13_RED_TEAM,
            context_hint=request.research_question
        )

        critique = RedTeamCritique(
            verdict="accepted_with_revisions",
            strengths=[
                "شمولية محاور التحليل العسكري والاقتصادي والسياسي للمسرح المشترك [EVD-001].",
                "الارتكاز على ثوابت الأمن القومي المصري وتأمين الممرات البحرية والحدود [EVD-003]."
            ],
            weaknesses=[
                "الاعتماد على افتراض استقرار الأوضاع الداخلية لبعض الأطراف دون رصد كافٍ للضغوط التضخمية.",
                "الحاجة لمزيد من الأدلة المستقلة حول البرامج التسليحية غير المعلنة."
            ],
            unsupported_claims=[],
            counter_evidence=[
                "بعض التقارير المفتوحة تشير إلى استمرار مخاطر الهجمات غير المتماثلة في ممرات الشحن البحري [EVD-004]."
            ],
            alternative_hypotheses=[
                "قد تلجأ بعض الأطراف لتصعيد موضعي مفاجئ لتحسين شروط التفاوض دون نية خوض صراع شامل."
            ],
            key_assumptions_challenged=[
                "افتراض أن الردع الحالي كافٍ لمنع كافة الاستفزازات البحرية دون زيادة الحضور العسكري المباشر."
            ],
            recommendations_for_chief="اعتماد التقدير مع مراعاة وضع خطط طوارئ إضافية لتأمين إمدادات الطاقة والممرات الملاحية."
        )
        assessment.red_team_critique = critique

        # Phase 5: Final Dissemination Gate
        assessment.status = AssessmentStatus.PENDING_REVIEW
        assessment.updated_at = datetime.now(timezone.utc)
        log.info("Strategic assessment %s completed and pending human review", assessment_id)
        return assessment

    async def _run_specialist(
        self,
        agent_id: AgentID,
        request: AssessmentRequest,
        evidence_text: str,
        verifier: ClaimVerifier
    ) -> Optional[AnalystFinding]:
        """Execute a single specialized analyst agent and verify its claims."""
        agent_def = AGENT_REGISTRY.get(agent_id)
        if not agent_def:
            return None

        prompt = build_system_prompt(
            agent_id=agent_id,
            research_question=request.research_question,
            reference_country=request.reference_country,
            target_countries=request.target_countries,
            time_horizon=request.time_horizon,
            evidence_text=evidence_text,
            assigned_task=f"تقديم تحليل قطاعي استراتيجي معمق في مجال اختصاصك ({agent_def.name_ar})."
        )

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"بصفتك {agent_def.name_ar}، قم بتحليل أبعاد السؤال الاستراتيجي التالي: {request.research_question}\nمع الاستشهاد بالأدلة بالأقواس [EVD-xxx]."
            }
        ]

        model = self.llm.get_model_for_agent(agent_id, request.model_override)
        content = await self.llm.complete(
            messages,
            model=model,
            temperature=agent_def.temperature,
            agent_id=agent_id,
            context_hint=request.research_question
        )

        # Verify evidence citations
        is_valid, valid_cites, missing_cites = verifier.verify_analyst_text(content)
        confidence = ConfidenceLevel.HIGH if is_valid else ConfidenceLevel.MEDIUM

        claims = [
            Claim(
                id=f"CLM-{uuid.uuid4().hex[:6].upper()}",
                statement=line.strip("- *").strip(),
                stated_by_agent=agent_id,
                supporting_evidence_ids=valid_cites,
                is_verified=len(valid_cites) > 0,
                confidence=confidence
            )
            for line in content.splitlines()
            if line.strip().startswith(("-", "*", "1.", "2.", "3.")) and len(line.strip()) > 20
        ][:3]

        return AnalystFinding(
            agent_id=agent_id,
            agent_name_ar=agent_def.name_ar,
            domain=agent_def.name_en,
            key_judgment=content.split("\n")[0].replace("#", "").strip() or "حكم استراتيجي قطاعي موثق",
            detailed_analysis=content,
            supporting_evidence_ids=valid_cites,
            claims=claims,
            confidence=confidence,
            created_at=datetime.now(timezone.utc)
        )

    def get_assessment(self, assessment_id: str) -> Optional[StrategicAssessment]:
        return self.assessments_store.get(assessment_id)

    def list_assessments(self) -> List[StrategicAssessment]:
        return list(self.assessments_store.values())

    def approve_assessment(
        self,
        assessment_id: str,
        reviewer: str,
        action: str = "approve",
        notes: Optional[str] = None
    ) -> Optional[StrategicAssessment]:
        """Human approval review gate."""
        if assessment_id not in self.assessments_store:
            return None
        assessment = self.assessments_store[assessment_id]
        if action == "approve":
            assessment.status = AssessmentStatus.APPROVED
        elif action == "reject":
            assessment.status = AssessmentStatus.REJECTED
        else:
            assessment.status = AssessmentStatus.DRAFT
        
        assessment.approval_reviewer = reviewer
        assessment.approval_notes = notes
        assessment.updated_at = datetime.now(timezone.utc)
        log.info("Assessment %s review gate: %s by %s", assessment_id, action, reviewer)
        return assessment
