"""Strategic OSIRIS - Admiralty Code Verification Engine.
Implements NATO Admiralty Code standards for rating source reliability (A-F)
and information credibility (1-6).
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from packages.schemas.models import (
    AdmiraltyCredibility,
    AdmiraltyReliability,
    Claim,
    ConfidenceLevel,
    DocumentEvidence,
)

RELIABILITY_SCORES: Dict[AdmiraltyReliability, float] = {
    AdmiraltyReliability.A: 1.0,
    AdmiraltyReliability.B: 0.8,
    AdmiraltyReliability.C: 0.6,
    AdmiraltyReliability.D: 0.4,
    AdmiraltyReliability.E: 0.2,
    AdmiraltyReliability.F: 0.5,
}

CREDIBILITY_SCORES: Dict[AdmiraltyCredibility, float] = {
    AdmiraltyCredibility.ONE: 1.0,
    AdmiraltyCredibility.TWO: 0.8,
    AdmiraltyCredibility.THREE: 0.6,
    AdmiraltyCredibility.FOUR: 0.3,
    AdmiraltyCredibility.FIVE: 0.1,
    AdmiraltyCredibility.SIX: 0.5,
}


class AdmiraltyEvaluator:
    @staticmethod
    def calculate_confidence(
        reliability: AdmiraltyReliability,
        credibility: AdmiraltyCredibility
    ) -> ConfidenceLevel:
        """Combine reliability and credibility into an overall analytical confidence score."""
        r_score = RELIABILITY_SCORES.get(reliability, 0.5)
        c_score = CREDIBILITY_SCORES.get(credibility, 0.5)
        combined = (r_score * 0.45) + (c_score * 0.55)
        
        if combined >= 0.75:
            return ConfidenceLevel.HIGH
        elif combined >= 0.45:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    @staticmethod
    def evaluate_source(source_type: str, domain: str) -> AdmiraltyReliability:
        """Estimate source reliability by tier."""
        st = source_type.lower()
        if "official" in st or "military" in st or "defense" in st:
            return AdmiraltyReliability.A
        elif "thinktank" in st or "wire" in st or "reuters" in domain or "afp" in domain:
            return AdmiraltyReliability.B
        elif "news" in st or "regional" in st:
            return AdmiraltyReliability.C
        elif "social" in st or "telegram" in st:
            return AdmiraltyReliability.D
        return AdmiraltyReliability.F


class ClaimVerifier:
    def __init__(self, evidence_store: Dict[str, DocumentEvidence]):
        self.evidence_store = evidence_store

    def extract_evidence_ids(self, text: str) -> List[str]:
        """Find all [EVD-xxx] references in the text."""
        return list(dict.fromkeys(re.findall(r"\[EVD-[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*\]", text)))

    def verify_analyst_text(self, text: str) -> Tuple[bool, List[str], List[str]]:
        """Check whether the analyst's text properly cites existing evidence.
        Returns:
            (is_valid, valid_citations, missing_citations)
        """
        cited_tags = self.extract_evidence_ids(text)
        valid_citations = []
        missing_citations = []

        for tag in cited_tags:
            evd_id = tag.strip("[]")
            if evd_id in self.evidence_store:
                valid_citations.append(evd_id)
            else:
                missing_citations.append(evd_id)

        has_any_citation = len(cited_tags) > 0
        all_valid = len(missing_citations) == 0 and has_any_citation
        return all_valid, valid_citations, missing_citations
