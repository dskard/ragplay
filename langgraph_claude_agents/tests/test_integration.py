# Integration test scaffold for langgraph_claude_agents.
# Tests marked @pytest.mark.integration require external services (LLM API).
# Run with: pytest -m integration
# Skip with: pytest -m "not integration"
from unittest.mock import patch

import pytest

from claude_agent_sdk.types import ResultMessage
from langgraph_claude_agents import agent
from langgraph_claude_agents.agent import run_agent
from langgraph_claude_agents.nodes import setup


def make_result_message(result):
    # Build a ResultMessage with the given result value for use in tests.
    return ResultMessage(
        subtype="success",
        duration_ms=100,
        duration_api_ms=100,
        is_error=False,
        num_turns=1,
        session_id="test-session",
        result=result,
    )


@pytest.mark.integration
def test_integration_marker_wiring():
    # Placeholder test to confirm the integration marker is correctly wired.
    # pytest -m integration must collect this test; pytest -m "not integration" must skip it.
    assert run_agent is not None
    assert setup is not None


@pytest.mark.integration
async def test_run_agent_returns_result_field_from_valid_result_message():
    # Scenario: query yields a ResultMessage with a non-empty result string.
    # Function(s): run_agent
    # Verifies that run_agent extracts and returns the result field value.
    async def fake_query(**kwargs):
        yield make_result_message("expected answer")

    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await agent.run_agent("prompt", [])

    assert result == "expected answer"


@pytest.mark.integration
async def test_run_agent_returns_empty_string_when_query_yields_no_result_message():
    # Scenario: query yields no messages at all (empty async generator).
    # Function(s): run_agent
    # Verifies that run_agent returns "" when the generator is exhausted with no messages.
    async def fake_query(**kwargs):
        # Empty generator — returns immediately without yielding anything.
        return
        yield  # make this an async generator

    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await agent.run_agent("prompt", [])

    assert result == ""


@pytest.mark.integration
async def test_run_agent_returns_empty_string_when_result_message_has_none_result():
    # Scenario: query yields a ResultMessage but its result field is None.
    # Function(s): run_agent
    # Verifies that run_agent returns "" instead of propagating None.
    async def fake_query(**kwargs):
        yield make_result_message(None)

    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await agent.run_agent("prompt", [])

    assert result == ""
