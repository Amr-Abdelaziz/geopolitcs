"""Strategic OSIRIS - Pydantic Data Contracts and Domain Models.
Defines schemas for the 14 agents, evidence tracking, Admiralty Code evaluation,
strategic assessments, and early warning indicators.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdmiraltyReliability(str, enum.Enum):
    """Source Reliability rating according to the Admiralty Code (NATO standard)."""
    A = "A"  # Completely reliable
    B = "B"  # Usually reliable
    C = "C"  # Fairly reliable
    D = "D"  # Not usually reliable
    E = "E"  # Unreliable
    F = "F"  # Reliability cannot be judged


class AdmiraltyCredibility(int, enum.Enum):
    """Information Credibility rating according to the Admiralty Code (NATO standard)."""
    ONE = 1    # Confirmed by other independent sources
    TWO = 2    # Probably true
    THREE = 3  # Possibly true
    FOUR = 4   # Doubtful
    FIVE = 5   # Improbable
    SIX = 6    # Truth cannot be judged


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AlertSeverity(str, enum.Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentID(str, enum.Enum):
    A01_CHIEF_STRATEGIST = "A01"
    A02_OSINT_COLLECTOR = "A02"
    A03_VERIFICATION = "A03"
    A04_MILITARY = "A04"
    A05_POLITICAL = "A05"
    A06_ECONOMIC = "A06"
    A07_GEOPOLITICAL = "A07"
    A08_DEFENSE_TECH = "A08"
    A09_GEOINT = "A09"
    A10_COUNTRY_INTEL = "A10"
    A11_FORECAST = "A11"
    A12_EARLY_WARNING = "A12"
    A13_RED_TEAM = "A13"
    A14_REPORT = "A14"


class AssessmentMode(str, enum.Enum):
    STRATEGIC_ASSESSMENT = "strategic_assessment"
    DAILY_BRIEF = "daily_brief"
    COUNTRY_PROFILE = "country_profile"
    DEFENSE_INDUSTRY = "defense_industry"
    REGIONAL_SECURITY = "regional_security"
    TECHNOLOGY = "technology"
    CRISIS_ASSESSMENT = "crisis_assessment"
    SCENARIO_ANALYSIS = "scenario_analysis"
    COMPARATIVE_COUNTRY = "comparative_country"
    EARLY_WARNING = "early_warning"


# --- Evidence and Source Registry ---

class Source(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    source_type: str = Field(default="news", description="official, news, thinktank, social, academic, osiris")
    reliability: AdmiraltyReliability = AdmiraltyReliability.B
    license: str = Field(default="open_access")
    notes: Optional[str] = None


class DocumentEvidence(BaseModel):
    id: str
    source_id: str
    source_name: str
    title: str
    url: Optional[str] = None
    content_snippet: str
    published_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=utc_now)
    reliability: AdmiraltyReliability = AdmiraltyReliability.B
    credibility: AdmiraltyCredibility = AdmiraltyCredibility.TWO
    countries_mentioned: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    content_hash: Optional[str] = None


class Claim(BaseModel):
    id: str
    statement: str
    stated_by_agent: AgentID
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    is_verified: bool = False
    verification_notes: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# --- Agent Definitions and State ---

class AgentDefinition(BaseModel):
    id: AgentID
    name_ar: str
    name_en: str
    role_description_ar: str
    role_description_en: str
    default_model: str = "meta-llama/llama-3.3-70b-instruct"
    temperature: float = 0.2
    is_active: bool = True
    assigned_tools: List[str] = Field(default_factory=list)


class AnalystFinding(BaseModel):
    agent_id: AgentID
    agent_name_ar: str
    domain: str
    key_judgment: str
    detailed_analysis: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    created_at: datetime = Field(default_factory=utc_now)


class ScenarioItem(BaseModel):
    title: str
    description: str
    probability_estimate: float = Field(ge=0.0, le=1.0)
    drivers: List[str] = Field(default_factory=list)
    indicators_to_watch: List[str] = Field(default_factory=list)
    strategic_implications: str


class RedTeamCritique(BaseModel):
    agent_id: AgentID = AgentID.A13_RED_TEAM
    verdict: str = Field(description="accepted | needs_revision | insufficient")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    counter_evidence: List[str] = Field(default_factory=list)
    alternative_hypotheses: List[str] = Field(default_factory=list)
    key_assumptions_challenged: List[str] = Field(default_factory=list)
    recommendations_for_chief: str


# --- Strategic Assessment Model ---

class StrategicAssessment(BaseModel):
    id: str
    research_question: str
    reference_country: str = "Egypt"
    target_countries: List[str] = Field(default_factory=lambda: ["Egypt", "Libya", "Israel"])
    time_horizon: str = "6-12 months"
    assessment_mode: AssessmentMode = AssessmentMode.STRATEGIC_ASSESSMENT
    
    # Synthesis
    executive_summary_ar: str = ""
    executive_summary_en: str = ""
    key_judgments: List[str] = Field(default_factory=list)
    
    # Detailed Domain Assessments
    military_assessment: Optional[str] = None
    political_assessment: Optional[str] = None
    economic_assessment: Optional[str] = None
    geopolitical_assessment: Optional[str] = None
    defense_tech_assessment: Optional[str] = None
    geoint_assessment: Optional[str] = None
    country_intel_assessment: Optional[str] = None
    
    # Egypt-Centric National Interest Assessment
    national_interest_implications: Optional[str] = None
    risks_and_opportunities: Optional[str] = None
    
    # Forward-Looking
    scenarios: List[ScenarioItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    intelligence_gaps: List[str] = Field(default_factory=list)
    
    # Quality & Assurance
    findings: List[AnalystFinding] = Field(default_factory=list)
    red_team_critique: Optional[RedTeamCritique] = None
    citations: List[DocumentEvidence] = Field(default_factory=list)
    
    # Governance & Approval
    status: AssessmentStatus = AssessmentStatus.DRAFT
    approval_reviewer: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# --- Early Warning & Indicator Engine ---

class IndicatorDefinition(BaseModel):
    id: str
    name: str
    region: str
    country: str
    description: str
    metric_type: str = "incident_count"
    baseline_value: float = 3.0
    current_value: float = 3.0
    window_days: int = 7
    threshold_ratio: float = 2.0  # Alert if current / baseline >= threshold_ratio
    is_active: bool = True


class WarningAlert(BaseModel):
    id: str
    indicator_id: str
    indicator_name: str
    region: str
    country: str
    severity: AlertSeverity
    title: str
    description: str
    ratio_to_baseline: float
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    triggered_at: datetime = Field(default_factory=utc_now)
    requires_human_review: bool = True
    is_dismissed: bool = False


# --- API Requests & Actions ---

class AssessmentRequest(BaseModel):
    research_question: str
    reference_country: str = "Egypt"
    target_countries: List[str] = Field(default_factory=lambda: ["Egypt", "Libya", "Israel"])
    time_horizon: str = "6-12 months"
    assessment_mode: AssessmentMode = AssessmentMode.STRATEGIC_ASSESSMENT
    selected_agents: Optional[List[AgentID]] = None
    model_override: Optional[str] = None


class ApprovalAction(BaseModel):
    action: str = Field(description="approve | reject | request_changes")
    reviewer: str
    notes: Optional[str] = None
