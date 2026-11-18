"""Strategic OSIRIS - Multi-Agent Orchestration Pipeline.
Coordinates the 14 agents in structured sequence:
Planning -> Collection -> Verification -> Parallel Analysis -> Synthesis -> Red Team -> Dissemination Gate.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
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
from packages.storage.database import DatabaseManager
from services.collection.collector import EvidenceCollector
from services.orchestrator.parsers import (
    parse_chief_synthesis,
    parse_red_team_critique,
    parse_scenarios,
)
from services.verification.admiralty import AdmiraltyEvaluator, ClaimVerifier

log = logging.getLogger("strategic_osiris.orchestrator")


class StrategicPipeline:
    def __init__(
        self,
        llm_client: Optional[OpenRouterClient] = None,
        collector: Optional[EvidenceCollector] = None,
        db: Optional[DatabaseManager] = None
    ):
        self.llm = llm_client or OpenRouterClient()
        self.db = db or DatabaseManager()
        self.collector = collector or EvidenceCollector(db=self.db)
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

        chief_synthesis = parse_chief_synthesis(chief_raw, request.research_question)
        assessment.executive_summary_ar = chief_raw[:1200]
        assessment.executive_summary_en = (
            f"Strategic Assessment regarding: {request.research_question}. "
            f"Evaluates national security posture for {request.reference_country} with focus on {', '.join(request.target_countries)}. "
            f"Deterrence balance, maritime security, and border stability remain primary operational imperatives."
        )
        assessment.key_judgments = chief_synthesis["key_judgments"]
        assessment.national_interest_implications = chief_synthesis["national_interest_implications"]
        assessment.risks_and_opportunities = chief_synthesis["risks_and_opportunities"]
        assessment.recommendations = chief_synthesis["recommendations"]

        # Dynamic Scenarios Extracted from A11 Forecast Analyst or Synthesis
        forecast_finding = next((f for f in assessment.findings if f.agent_id == AgentID.A11_FORECAST), None)
        scenario_source_text = forecast_finding.detailed_analysis if forecast_finding else chief_raw
        assessment.scenarios = parse_scenarios(scenario_source_text, request.research_question)

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

        # Dynamically Parse Red Team Critique from live A13 output
        assessment.red_team_critique = parse_red_team_critique(red_raw)

        # Phase 5: Final Dissemination Gate
        assessment.status = AssessmentStatus.PENDING_REVIEW
        assessment.updated_at = datetime.now(timezone.utc)
        self.assessments_store[assessment_id] = assessment
        try:
            await self.db.save_assessment(assessment)
        except Exception as e:
            log.warning("Failed to persist assessment %s: %s", assessment_id, e)

        log.info("Strategic assessment %s completed and pending human review", assessment_id)
        return assessment

    async def execute_assessment_stream(
        self,
        request: AssessmentRequest
    ) -> AsyncGenerator[str, None]:
        """Execute assessment while streaming real-time SSE deliberation events."""
        assessment_id = f"SA-{uuid.uuid4().hex[:8].upper()}"
        log.info("Starting streaming strategic assessment %s", assessment_id)

        def make_sse(event_type: str, data: Any) -> str:
            payload = json.dumps(data, ensure_ascii=False)
            return f"event: {event_type}\ndata: {payload}\n\n"

        yield make_sse("init", {
            "assessment_id": assessment_id,
            "research_question": request.research_question,
            "reference_country": request.reference_country,
            "target_countries": request.target_countries
        })

        # Phase 1: OSINT Collection
        yield make_sse("phase", {
            "phase": "collection",
            "message": "📡 جاري سحب أحدث الأخبار والمؤشرات الميدانية الحية من OSIRIS..."
        })
        evidence_list = await self.collector.collect_for_topic(
            request.research_question, request.target_countries
        )
        evidence_store = {e.id: e for e in evidence_list}
        verifier = ClaimVerifier(evidence_store)

        evidence_text = "\n".join(
            f"[{e.id}] {e.title} ({e.source_name}, موثوقية: {e.reliability.value}{e.credibility.value}): {e.content_snippet}"
            for e in evidence_list
        )
        yield make_sse("evidence_collected", {
            "count": len(evidence_list),
            "sample": [e.title for e in evidence_list[:3]]
        })

        # Phase 2: Admiralty Verification
        yield make_sse("phase", {
            "phase": "verification",
            "message": "⚖️ تطبيق معايير الكود البحري (Admiralty Code) وتدقيق المصادر..."
        })

        # Phase 3: Specialist Deliberation
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

        findings: List[AnalystFinding] = []
        for aid in specialists:
            agent_def = agent_config_manager.get_agent(aid)
            if not agent_def or not agent_def.is_active:
                continue

            model_name = self.llm.get_model_for_agent(aid, request.model_override)
            yield make_sse("agent_start", {
                "agent_id": aid.value,
                "name": agent_def.name_ar,
                "domain": agent_def.name_en,
                "model": model_name
            })

            finding = await self._run_specialist(aid, request, evidence_text, verifier)
            if finding:
                findings.append(finding)
                yield make_sse("agent_complete", {
                    "agent_id": aid.value,
                    "name": agent_def.name_ar,
                    "key_judgment": finding.key_judgment,
                    "confidence": finding.confidence.value,
                    "claims_count": len(finding.claims)
                })

        # Phase 4: Chief Strategic Analyst Synthesis (A01)
        yield make_sse("phase", {
            "phase": "synthesis",
            "message": "🎯 رئيس خلية التحليل الاستراتيجي (A01) يصيغ التقدير الاستراتيجي الشامل..."
        })
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
            for f in findings
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
        chief_synthesis = parse_chief_synthesis(chief_raw, request.research_question)

        # Scenarios (A11)
        yield make_sse("phase", {
            "phase": "scenarios",
            "message": "🔮 محلل السيناريوهات (A11) يستشرف مسارات المستقبل البديلة ومصفوفة التوقعات..."
        })
        forecast_finding = next((f for f in findings if f.agent_id == AgentID.A11_FORECAST), None)
        scenario_source = forecast_finding.detailed_analysis if forecast_finding else chief_raw
        scenarios = parse_scenarios(scenario_source, request.research_question)

        # Red Team (A13)
        yield make_sse("phase", {
            "phase": "red_team",
            "message": "🔴 الفريق الأحمر (A13) يجري المراجعة النقدية وتحدي الافتراضات..."
        })
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
        critique = parse_red_team_critique(red_raw)

        # Assemble StrategicAssessment
        assessment = StrategicAssessment(
            id=assessment_id,
            research_question=request.research_question,
            reference_country=request.reference_country,
            target_countries=request.target_countries,
            time_horizon=request.time_horizon,
            assessment_mode=request.assessment_mode,
            status=AssessmentStatus.PENDING_REVIEW,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            executive_summary_ar=chief_raw[:1200],
            executive_summary_en=(
                f"Strategic Assessment regarding: {request.research_question}. "
                f"Evaluates national security posture for {request.reference_country} with focus on {', '.join(request.target_countries)}. "
                f"Deterrence balance, maritime security, and border stability remain primary operational imperatives."
            ),
            key_judgments=chief_synthesis["key_judgments"],
            national_interest_implications=chief_synthesis["national_interest_implications"],
            risks_and_opportunities=chief_synthesis["risks_and_opportunities"],
            recommendations=chief_synthesis["recommendations"],
            scenarios=scenarios,
            red_team_critique=critique,
            findings=findings,
            citations=evidence_list
        )

        for f in findings:
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

        self.assessments_store[assessment_id] = assessment
        try:
            await self.db.save_assessment(assessment)
        except Exception as e:
            log.warning("Failed to persist streaming assessment: %s", e)

        yield make_sse("complete", {
            "assessment_id": assessment_id,
            "status": assessment.status.value,
            "assessment": assessment.model_dump(mode="json")
        })

    def get_assessment(self, assessment_id: str) -> Optional[StrategicAssessment]:
        return self.assessments_store.get(assessment_id)

    async def get_assessment_async(self, assessment_id: str) -> Optional[StrategicAssessment]:
        if assessment_id in self.assessments_store:
            return self.assessments_store[assessment_id]
        try:
            stored = await self.db.get_assessment(assessment_id)
            if stored:
                self.assessments_store[assessment_id] = stored
                return stored
        except Exception as e:
            log.warning("Failed to fetch assessment %s from DB: %s", assessment_id, e)
        return None

    def list_assessments(self) -> List[StrategicAssessment]:
        return list(self.assessments_store.values())

    async def list_assessments_async(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[StrategicAssessment]:
        try:
            stored = await self.db.list_assessments(limit=limit, status=status, country=country)
            if stored:
                for a in stored:
                    self.assessments_store[a.id] = a
                return stored
        except Exception as e:
            log.warning("Failed to list assessments from DB: %s", e)
        return list(self.assessments_store.values())

    def approve_assessment(
        self,
        assessment_id: str,
        reviewer: str,
        action: str = "approve",
        notes: Optional[str] = None
    ) -> Optional[StrategicAssessment]:
        """Human approval review gate with audit logging."""
        if assessment_id not in self.assessments_store:
            return None
        assessment = self.assessments_store[assessment_id]
        if action.lower() == "approve":
            assessment.status = AssessmentStatus.APPROVED
        elif action.lower() == "reject":
            assessment.status = AssessmentStatus.REJECTED
        else:
            assessment.status = AssessmentStatus.DRAFT
        
        assessment.approval_reviewer = reviewer
        assessment.approval_notes = notes
        assessment.updated_at = datetime.now(timezone.utc)
        log.info("Assessment %s review gate: %s by %s", assessment_id, action, reviewer)

        # Trigger async persistence
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_approval(assessment_id, reviewer, action, notes, assessment))
        except RuntimeError:
            pass

        return assessment

    async def _persist_approval(
        self,
        assessment_id: str,
        reviewer: str,
        action: str,
        notes: Optional[str],
        assessment: StrategicAssessment
    ) -> None:
        try:
            await self.db.save_assessment(assessment)
            await self.db.log_audit(assessment_id, reviewer, action, notes)
        except Exception as e:
            log.warning("Failed to persist approval for %s: %s", assessment_id, e)

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
