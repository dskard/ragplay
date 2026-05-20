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


_NODE_MOCK_RESPONSES = {
    "setup": json.dumps({"issue_title": "t", "issue_body": "b"}),
    "plan_behaviors": json.dumps([]),
    "tdd_behavior": json.dumps({"status": "success"}),
}


@pytest.mark.parametrize("name", NODE_NAMES)
async def test_node_returns_partial_state(name):
    fn = getattr(nodes, name)
    state = {
        "issue_number": 1,
        "issue_title": "test",
        "issue_body": "body",
        "behaviors": ["a behavior"],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    mock_response = _NODE_MOCK_RESPONSES.get(name, "{}")
    with patch("langgraph_claude_agents.nodes.run_agent", new=AsyncMock(return_value=mock_response)):
        if name == "teardown":
            with pytest.raises(SystemExit):
                await fn(state)
        else:
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


async def test_tdd_behavior_calls_run_agent_with_correct_tools():
    behaviors = ["implement feature X"]
    state = make_state(behaviors=behaviors, current_behavior_index=0)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=json.dumps({"status": "success"})),
    ) as mock_run:
        await nodes.tdd_behavior(state)

    mock_run.assert_called_once()
    assert set(mock_run.call_args.kwargs.get("allowed_tools", [])) == {
        "Bash", "Read", "Write", "Edit"
    }


async def test_tdd_behavior_increments_index_on_success():
    behaviors = ["implement feature X", "implement feature Y"]
    state = make_state(behaviors=behaviors, current_behavior_index=0)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=json.dumps({"status": "success"})),
    ):
        result = await nodes.tdd_behavior(state)

    assert result["current_behavior_index"] == 1


async def test_tdd_behavior_sets_error_and_does_not_increment_on_failure():
    behaviors = ["implement feature X"]
    state = make_state(behaviors=behaviors, current_behavior_index=0)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=json.dumps({"error": "test could not be made green"})),
    ):
        result = await nodes.tdd_behavior(state)

    assert result.get("error") == "test could not be made green"
    assert "current_behavior_index" not in result


async def test_tdd_behavior_sets_error_when_index_out_of_bounds():
    state = make_state(behaviors=["only one"], current_behavior_index=5)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="{}"),
    ) as mock_run:
        result = await nodes.tdd_behavior(state)

    mock_run.assert_not_called()
    assert "error" in result
    assert result["error"]


async def test_tdd_behavior_sets_error_on_non_json_agent_response():
    behaviors = ["implement feature X"]
    state = make_state(behaviors=behaviors, current_behavior_index=0)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="not valid json"),
    ):
        result = await nodes.tdd_behavior(state)

    assert "error" in result
    assert "non-JSON" in result["error"]
    assert "current_behavior_index" not in result


async def test_tdd_behavior_sets_error_on_unexpected_json_type():
    behaviors = ["implement feature X"]
    state = make_state(behaviors=behaviors, current_behavior_index=0)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="[]"),
    ):
        result = await nodes.tdd_behavior(state)

    assert "error" in result
    assert result["error"]
    assert "current_behavior_index" not in result


async def test_verify_ac_skips_run_agent_when_no_acceptance_criteria():
    state = make_state(acceptance_criteria=[], behaviors=["b1"], current_behavior_index=1)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(),
    ) as mock_run:
        result = await nodes.verify_ac(state)

    mock_run.assert_not_called()
    assert isinstance(result, dict)
    assert "error" not in result or not result["error"]


async def test_verify_ac_calls_run_agent_with_bash_and_read_when_ac_exist():
    ac = ["tool is available", "output is parsed"]
    state = make_state(acceptance_criteria=ac)
    agent_response = json.dumps({"all_covered": True, "uncovered": []})
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=agent_response),
    ) as mock_run:
        await nodes.verify_ac(state)

    mock_run.assert_called_once()
    called_tools = set(mock_run.call_args.kwargs.get("allowed_tools", []))
    assert "Bash" in called_tools
    assert "Read" in called_tools


async def test_verify_ac_returns_empty_dict_when_all_covered():
    ac = ["tool is available"]
    state = make_state(acceptance_criteria=ac)
    agent_response = json.dumps({"all_covered": True, "uncovered": []})
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=agent_response),
    ):
        result = await nodes.verify_ac(state)

    assert result == {}


async def test_verify_ac_appends_uncovered_to_behaviors_and_updates_index():
    ac = ["criterion one", "criterion two"]
    existing_behaviors = ["behavior A", "behavior B"]
    state = make_state(
        acceptance_criteria=ac,
        behaviors=existing_behaviors,
        current_behavior_index=2,
    )
    uncovered = ["criterion two"]
    agent_response = json.dumps({"all_covered": False, "uncovered": uncovered})
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=agent_response),
    ):
        result = await nodes.verify_ac(state)

    assert result["behaviors"] == existing_behaviors + uncovered
    assert result["current_behavior_index"] == len(existing_behaviors)


async def test_verify_ac_sets_error_on_non_json_agent_response():
    ac = ["some criterion"]
    state = make_state(acceptance_criteria=ac)
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="not valid json"),
    ):
        result = await nodes.verify_ac(state)

    assert "error" in result
    assert result["error"]


async def test_verify_ac_deduplicates_uncovered_already_in_behaviors():
    ac = ["criterion one"]
    existing_behaviors = ["behavior A", "criterion one"]
    state = make_state(
        acceptance_criteria=ac,
        behaviors=existing_behaviors,
        current_behavior_index=2,
    )
    agent_response = json.dumps({"all_covered": False, "uncovered": ["criterion one"]})
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value=agent_response),
    ):
        result = await nodes.verify_ac(state)

    assert "behaviors" not in result or result.get("behaviors") == existing_behaviors


async def test_full_test_calls_run_agent_with_bash_and_read():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"status": "success"}'),
    ) as mock_run:
        await nodes.full_test(make_state())

    mock_run.assert_called_once()
    called_tools = set(mock_run.call_args.kwargs.get("allowed_tools", []))
    assert "Bash" in called_tools
    assert "Read" in called_tools


async def test_full_test_returns_empty_dict_on_success():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"status": "success"}'),
    ):
        result = await nodes.full_test(make_state())

    assert result == {}


async def test_full_test_sets_error_when_test_suite_fails():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"error": "tests failed"}'),
    ):
        result = await nodes.full_test(make_state())

    assert result.get("error") == "tests failed"


async def test_full_test_sets_error_on_non_json_agent_response():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="not valid json"),
    ):
        result = await nodes.full_test(make_state())

    assert "error" in result
    assert result["error"]


async def test_full_test_sets_error_on_unexpected_json_type():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="[]"),
    ):
        result = await nodes.full_test(make_state())

    assert "error" in result
    assert result["error"]


async def test_branch_review_calls_run_agent_with_correct_tools():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"status": "success"}'),
    ) as mock_run:
        await nodes.branch_review(make_state())

    mock_run.assert_called_once()
    called_tools = set(mock_run.call_args.kwargs.get("allowed_tools", []))
    assert called_tools == {"Bash", "Read", "Write", "Edit"}


async def test_branch_review_returns_empty_dict_on_success():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"status": "success"}'),
    ):
        result = await nodes.branch_review(make_state())

    assert result == {}


async def test_branch_review_sets_error_when_review_fails():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value='{"error": "review could not be completed"}'),
    ):
        result = await nodes.branch_review(make_state())

    assert result.get("error") == "review could not be completed"


async def test_branch_review_sets_error_on_non_json_agent_response():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="not valid json"),
    ):
        result = await nodes.branch_review(make_state())

    assert "error" in result
    assert result["error"]


async def test_branch_review_sets_error_on_unexpected_json_type():
    with patch(
        "langgraph_claude_agents.nodes.run_agent",
        new=AsyncMock(return_value="[]"),
    ):
        result = await nodes.branch_review(make_state())

    assert "error" in result
    assert result["error"]


async def test_teardown_exits_with_status_1_when_error_set():
    state = make_state(error="something went wrong")
    with pytest.raises(SystemExit) as exc_info:
        await nodes.teardown(state)
    assert exc_info.value.code == 1


async def test_teardown_exits_with_status_0_when_no_error():
    state = make_state(error="")
    with pytest.raises(SystemExit) as exc_info:
        await nodes.teardown(state)
    assert exc_info.value.code == 0


async def test_teardown_prints_error_to_stderr(capsys):
    state = make_state(error="something went wrong")
    with pytest.raises(SystemExit):
        await nodes.teardown(state)
    captured = capsys.readouterr()
    assert "something went wrong" in captured.err
