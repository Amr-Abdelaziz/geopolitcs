"""End-to-end Pipeline & Acceptance Tests for Strategic OSIRIS."""
import pytest
from packages.schemas.models import (
    AssessmentMode,
    AssessmentRequest,
    AssessmentStatus,
)
from services.orchestrator.pipeline import StrategicPipeline
from services.reporting.generator import ReportGenerator


@pytest.mark.asyncio
async def test_acceptance_strategic_assessment():
    """Verify the acceptance scenario defined in Section 8 of the design plan:
    'Assess defense industry development, international partnerships and strategic implications for Egypt.'
    """
    pipeline = StrategicPipeline()
    
    request = AssessmentRequest(
        research_question="Assess defense industry development, international defense partnerships and strategic implications for Egypt, Libya, and Israel over the next five years.",
        reference_country="Egypt",
        target_countries=["Egypt", "Libya", "Israel"],
        time_horizon="2-5 years",
        assessment_mode=AssessmentMode.STRATEGIC_ASSESSMENT
    )

    assessment = await pipeline.execute_assessment(request)

    # 1. Verification of generated fields
    assert assessment.id.startswith("SA-")
    assert assessment.research_question == request.research_question
    assert len(assessment.citations) > 0
    assert len(assessment.findings) >= 5
    assert len(assessment.key_judgments) >= 3
    assert assessment.military_assessment is not None
    assert assessment.political_assessment is not None
    assert assessment.economic_assessment is not None
    assert assessment.geopolitical_assessment is not None
    assert assessment.defense_tech_assessment is not None
    assert assessment.national_interest_implications is not None

    # 2. Red Team critique must be present and substantive
    assert assessment.red_team_critique is not None
    assert len(assessment.red_team_critique.strengths) > 0
    assert len(assessment.red_team_critique.weaknesses) > 0
    assert assessment.red_team_critique.recommendations_for_chief != ""

    # 3. Scenarios must be generated
    assert len(assessment.scenarios) >= 3
    for s in assessment.scenarios:
        assert s.title != ""
        assert 0.0 <= s.probability_estimate <= 1.0

    # 4. Mandatory Human Dissemination Gate: Must be pending review initially
    assert assessment.status == AssessmentStatus.PENDING_REVIEW
    assert assessment.approval_reviewer is None

    # 5. Perform Human Review Action
    approved = pipeline.approve_assessment(
        assessment_id=assessment.id,
        reviewer="Major General / Chief Strategic Reviewer",
        action="approve",
        notes="Approved for strategic operational dissemination."
    )
    assert approved.status == AssessmentStatus.APPROVED
    assert approved.approval_reviewer == "Major General / Chief Strategic Reviewer"

    # 6. Verify Report Generation
    md_report = ReportGenerator.to_arabic_markdown(approved)
    assert "تقدير موقف استراتيجي" in md_report
    assert "الملخص التنفيذي" in md_report
    assert "المراجعة النقدية المستقلة (الفريق الأحمر" in md_report
    assert "سجل الأدلة والمصادر الموثقة" in md_report
    assert approved.id in md_report

    html_report = ReportGenerator.to_html(approved)
    assert "<html lang=\"ar\" dir=\"rtl\">" in html_report
    assert approved.id in html_report
