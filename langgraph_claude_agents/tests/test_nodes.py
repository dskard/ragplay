import inspect
import json
from unittest.mock import AsyncMock, patch
import pytest
from langgraph_claude_agents import nodes


NODE_NAMES = [
    "setup",
    "plan_behaviors",
    "tdd_behavior",
    "verify_ac",
    "full_test",
    "branch_review",
    "teardown",
]


@pytest.mark.parametrize("name", NODE_NAMES)
def test_node_exists_and_is_async(name):
    fn = getattr(nodes, name)
    assert inspect.iscoroutinefunction(fn), f"{name} must be async"


@pytest.mark.parametrize("name", NODE_NAMES)
async def test_node_returns_partial_state(name):
    fn = getattr(nodes, name)
    state = {
        "issue_number": 1,
        "issue_title": "test",
        "issue_body": "body",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    with patch("langgraph_claude_agents.nodes.run_agent", new=AsyncMock(return_value="{}")):
        result = await fn(state)
    assert isinstance(result, dict)


def make_state(**overrides):
    base = {
        "issue_number": 7,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    base.update(overrides)
    return base


async def test_setup_happy_path_updates_state():
    agent_output = json.dumps({"issue_title": "My Issue", "issue_body": "Body text"})
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=agent_output),
    ) as mock_run:
        result = await nodes.setup(make_state())

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("allowed_tools") == ["Bash"] or mock_run.call_args.args[1] == ["Bash"]
    assert result["issue_title"] == "My Issue"
    assert result["issue_body"] == "Body text"
    assert result["status"] == "setup_done"
