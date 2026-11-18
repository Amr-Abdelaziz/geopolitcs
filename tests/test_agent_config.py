"""Tests for Agent Configuration, Prompt Modification, and Dynamic Model Routing."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app
from packages.openrouter.client import OpenRouterClient
from packages.prompts.registry import (
    AgentConfigManager,
    agent_config_manager,
    build_system_prompt,
)
from packages.schemas.models import AgentID, AgentUpdateRequest


def test_modify_agent_model_and_temperature(tmp_path):
    """Verify that changing an agent's model and temperature updates routing."""
    config_file = str(tmp_path / "agents_config.json")
    mgr = AgentConfigManager(config_path=config_file)

    # 1. Update A04 Military model & temp
    update = AgentUpdateRequest(
        default_model="openai/gpt-4o",
        temperature=0.4
    )
    updated = mgr.update_agent(AgentID.A04_MILITARY, update)
    assert updated.default_model == "openai/gpt-4o"
    assert updated.temperature == 0.4
    assert updated.is_customized is True

    # 2. Reset back
    reset = mgr.reset_agent(AgentID.A04_MILITARY)
    assert reset.default_model == "anthropic/claude-haiku-5.5"
    assert reset.is_customized is False


def test_modify_agent_prompt_and_parameter_injection(tmp_path):
    """Verify modifying agent prompt updates rendered prompt and preserves parameter injection."""
    config_file = str(tmp_path / "agents_config.json")
    mgr = AgentConfigManager(config_path=config_file)

    custom_text = "تعليمات مخصصة مشددة للغاية للمحلل السياسي [EVD-CUSTOM]"
    mgr.update_agent(
        AgentID.A05_POLITICAL,
        AgentUpdateRequest(system_prompt=custom_text)
    )

    prompt = mgr.build_system_prompt(
        agent_id=AgentID.A05_POLITICAL,
        research_question="تداعيات التغييرات السياسية",
        reference_country="مصر"
    )
    assert custom_text in prompt
    assert "تداعيات التغييرات السياسية" in prompt
    assert "مصر" in prompt


def test_config_persistence_and_reload(tmp_path):
    """Verify that customizations persist to disk and reload accurately."""
    config_file = str(tmp_path / "test_agents.json")
    mgr1 = AgentConfigManager(config_path=config_file)

    mgr1.update_agent(
        AgentID.A07_GEOPOLITICAL,
        AgentUpdateRequest(
            default_model="google/gemini-2.0-flash-001",
            temperature=0.55,
            system_prompt="تعليمات جيوسياسية جديدة ومحدثة"
        )
    )

    # Reload in fresh manager instance
    mgr2 = AgentConfigManager(config_path=config_file)
    agent = mgr2.get_agent(AgentID.A07_GEOPOLITICAL)
    assert agent is not None
    assert agent.default_model == "google/gemini-2.0-flash-001"
    assert agent.temperature == 0.55
    assert agent.is_customized is True
    assert "تعليمات جيوسياسية جديدة" in mgr2.get_prompt(AgentID.A07_GEOPOLITICAL)


@pytest.mark.asyncio
async def test_api_modify_and_reset_agent_lifecycle():
    """Verify API endpoints for modifying and resetting agents."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch available models
        models_res = await client.get("/api/agents/models")
        assert models_res.status_code == 200
        models = models_res.json()
        assert "anthropic/claude-haiku-5.5" in models
        assert "anthropic/claude-3.5-sonnet" in models
        assert "openai/gpt-4o" in models

        # 2. Modify A04 Military via PUT
        payload = {
            "default_model": "openai/gpt-4o",
            "temperature": 0.45,
            "system_prompt": "تعليمات اختبارية للوكيل العسكري عبر الـ API"
        }
        put_res = await client.put("/api/agents/A04", json=payload)
        assert put_res.status_code == 200
        data = put_res.json()
        assert data["metadata"]["default_model"] == "openai/gpt-4o"
        assert data["metadata"]["temperature"] == 0.45
        assert data["is_customized"] is True
        assert "تعليمات اختبارية" in data["system_prompt"]

        # 3. GET check
        get_res = await client.get("/api/agents/A04")
        assert get_res.status_code == 200
        assert get_res.json()["metadata"]["default_model"] == "openai/gpt-4o"

        # 4. Reset A04 back to default
        reset_res = await client.post("/api/agents/A04/reset")
        assert reset_res.status_code == 200
        reset_data = reset_res.json()
        assert reset_data["metadata"]["default_model"] == "anthropic/claude-haiku-5.5"
        assert reset_data["is_customized"] is False
