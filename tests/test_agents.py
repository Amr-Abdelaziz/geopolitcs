"""Tests for Agent Registry and Prompt Builder."""
import pytest
from packages.prompts.registry import AGENT_REGISTRY, build_system_prompt
from packages.schemas.models import AgentID


def test_all_14_agents_registered():
    """Verify that all 14 strategic intelligence agents are registered."""
    assert len(AGENT_REGISTRY) == 14
    for aid in AgentID:
        assert aid in AGENT_REGISTRY
        agent_def = AGENT_REGISTRY[aid]
        assert agent_def.name_ar
        assert agent_def.name_en
        assert agent_def.role_description_ar
        assert agent_def.role_description_en
        assert agent_def.default_model


def test_build_system_prompt_parameter_substitution():
    """Verify parameter injection in Arabic prompts."""
    prompt = build_system_prompt(
        agent_id=AgentID.A04_MILITARY,
        research_question="تقييم القدرات العسكرية والتوازنات في مسرح العمليات",
        reference_country="مصر",
        target_countries=["مصر", "ليبيا", "إسرائيل"],
        time_horizon="6 أشهر"
    )
    assert "تقييم القدرات العسكرية والتوازنات في مسرح العمليات" in prompt
    assert "مصر" in prompt
    assert "ليبيا" in prompt
    assert "إسرائيل" in prompt
    assert "أنت عضو في منظومة OSIRIS" in prompt
    assert "المحلل العسكري والدفاعي" in prompt
