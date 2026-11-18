"""Tests for Admiralty Code and Claim Verification."""
import pytest
from packages.schemas.models import (
    AdmiraltyCredibility,
    AdmiraltyReliability,
    ConfidenceLevel,
    DocumentEvidence,
)
from services.verification.admiralty import AdmiraltyEvaluator, ClaimVerifier


def test_admiralty_confidence_calculation():
    """Verify Admiralty Code confidence derivation."""
    # A1 -> HIGH
    assert AdmiraltyEvaluator.calculate_confidence(AdmiraltyReliability.A, AdmiraltyCredibility.ONE) == ConfidenceLevel.HIGH
    # B2 -> HIGH
    assert AdmiraltyEvaluator.calculate_confidence(AdmiraltyReliability.B, AdmiraltyCredibility.TWO) == ConfidenceLevel.HIGH
    # D4 -> LOW
    assert AdmiraltyEvaluator.calculate_confidence(AdmiraltyReliability.D, AdmiraltyCredibility.FOUR) == ConfidenceLevel.LOW
    # E5 -> LOW
    assert AdmiraltyEvaluator.calculate_confidence(AdmiraltyReliability.E, AdmiraltyCredibility.FIVE) == ConfidenceLevel.LOW


def test_claim_verification_with_citations():
    """Verify that cited claims are validated against the evidence store."""
    evidence_store = {
        "EVD-001": DocumentEvidence(
            id="EVD-001",
            source_id="S1",
            source_name="Official Defense Release",
            title="Readiness Drills",
            content_snippet="Armed forces conduct border security drills."
        ),
        "EVD-002": DocumentEvidence(
            id="EVD-002",
            source_id="S2",
            source_name="Maritime Authority",
            title="Suez Patrol",
            content_snippet="Naval patrols secure sea lanes."
        )
    }

    verifier = ClaimVerifier(evidence_store)

    # Valid text citing EVD-001
    valid_text = "تؤكد المناورات الجاهزية العالية [EVD-001] لحماية الحدود."
    is_valid, valid_cites, missing_cites = verifier.verify_analyst_text(valid_text)
    assert is_valid is True
    assert "EVD-001" in valid_cites
    assert len(missing_cites) == 0

    # Text citing non-existent evidence
    invalid_text = "تم رصد أسلحة سرية [EVD-999] دون تأكيد."
    is_valid, valid_cites, missing_cites = verifier.verify_analyst_text(invalid_text)
    assert is_valid is False
    assert "EVD-999" in missing_cites

    # Text with zero citations
    empty_text = "تحليل عام بدون أي استشهاد بالأدلة."
    is_valid, valid_cites, missing_cites = verifier.verify_analyst_text(empty_text)
    assert is_valid is False
