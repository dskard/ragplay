# Integration test scaffold for langgraph_claude_agents.
# Tests marked @pytest.mark.integration require external services (LLM API).
# Run with: pytest -m integration
# Skip with: pytest -m "not integration"
import pytest

from langgraph_claude_agents.agent import run_agent
from langgraph_claude_agents.nodes import setup


@pytest.mark.integration
def test_integration_marker_wiring():
    # Placeholder test to confirm the integration marker is correctly wired.
    # pytest -m integration must collect this test; pytest -m "not integration" must skip it.
    assert run_agent is not None
    assert setup is not None
