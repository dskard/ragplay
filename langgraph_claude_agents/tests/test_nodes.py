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
    valid_response = json.dumps({"issue_title": "t", "issue_body": "b"})
    with patch("langgraph_claude_agents.nodes.run_agent", new=AsyncMock(return_value=valid_response)):
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
    assert mock_run.call_args.kwargs.get("allowed_tools") == ["Bash"]
    assert result["issue_title"] == "My Issue"
    assert result["issue_body"] == "Body text"
    assert result["status"] == "setup_done"


async def test_setup_sets_error_when_tool_unavailable():
    error_output = json.dumps({"error": "gh not found in PATH"})
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=error_output),
    ):
        result = await nodes.setup(make_state())

    assert result.get("error") == "gh not found in PATH"
    assert "issue_title" not in result


async def test_setup_sets_error_on_malformed_agent_output():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="not valid json"),
    ):
        result = await nodes.setup(make_state())

    assert "error" in result
    assert result["error"]


_ISSUE_BODY_WITH_AC = """
## Acceptance Criteria

- [ ] tool is available
- [ ] output is parsed
"""


async def test_plan_behaviors_happy_path():
    behaviors = ["check tool available", "parse output"]
    agent_output = json.dumps(behaviors)
    state = make_state(issue_body=_ISSUE_BODY_WITH_AC)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=agent_output),
    ) as mock_run:
        result = await nodes.plan_behaviors(state)

    mock_run.assert_called_once()
    assert result["behaviors"] == behaviors
    assert result["current_behavior_index"] == 0
    assert result["acceptance_criteria"] == ["tool is available", "output is parsed"]


async def test_plan_behaviors_sets_error_on_invalid_json():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="not json"),
    ):
        result = await nodes.plan_behaviors(make_state())

    assert "error" in result
    assert result["error"]


async def test_plan_behaviors_sets_error_when_agent_returns_object_not_array():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"key": "value"}'),
    ):
        result = await nodes.plan_behaviors(make_state())

    assert "error" in result
    assert result["error"]
