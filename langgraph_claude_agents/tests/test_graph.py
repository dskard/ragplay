import json
from unittest.mock import AsyncMock, patch
import pytest
from langgraph_claude_agents.graph import build_graph


def _setup_ok(issue_number=1, title="Test Issue", body=""):
    return json.dumps({"issue_title": title, "issue_body": body})



def test_graph_compiles():
    graph = build_graph()
    assert graph is not None


def test_graph_has_all_seven_nodes():
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {"setup", "plan_behaviors", "tdd_behavior", "verify_ac",
                "full_test", "branch_review", "teardown"}
    assert expected.issubset(node_names)


async def test_happy_path_no_behaviors_routes_to_done():
    graph = build_graph()
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    mock = AsyncMock(side_effect=[_setup_ok(), "[]", '{"status": "success"}'])
    with patch("langgraph_claude_agents.nodes.run_agent", new=mock):
        result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert result["error"] == ""


async def test_error_in_setup_routes_to_teardown():
    graph = build_graph()
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    error_output = json.dumps({"error": "something failed"})
    mock = AsyncMock(return_value=error_output)
    with patch("langgraph_claude_agents.nodes.run_agent", new=mock):
        result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert result["error"] == "something failed"


async def test_error_in_plan_behaviors_routes_to_teardown():
    graph = build_graph()
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    mock = AsyncMock(side_effect=[_setup_ok(), "not valid json"])
    with patch("langgraph_claude_agents.nodes.run_agent", new=mock):
        result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert result["error"]


async def test_happy_path_with_behaviors_loops_tdd_until_exhausted():
    graph = build_graph()
    behaviors_json = json.dumps(["behavior one", "behavior two"])
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    tdd_ok = json.dumps({"status": "success"})
    full_test_ok = json.dumps({"status": "success"})
    mock = AsyncMock(side_effect=[_setup_ok(), behaviors_json, tdd_ok, tdd_ok, full_test_ok])
    with patch("langgraph_claude_agents.nodes.run_agent", new=mock):
        result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert result["error"] == ""
    assert result["current_behavior_index"] == 2


def test_build_graph_raises_for_custom_db():
    with pytest.raises(NotImplementedError):
        build_graph(db="other.sqlite")


def test_build_graph_raises_for_restart():
    with pytest.raises(NotImplementedError):
        build_graph(restart=True)


async def test_verify_ac_all_covered_routes_to_full_test():
    graph = build_graph()
    ac = ["criterion one"]
    behaviors_json = json.dumps(["behavior one"])
    verify_ac_response = json.dumps({"all_covered": True, "uncovered": []})
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "## Acceptance Criteria\n\n- [ ] criterion one\n",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    tdd_ok = json.dumps({"status": "success"})
    full_test_ok = json.dumps({"status": "success"})
    mock = AsyncMock(side_effect=[_setup_ok(body="## Acceptance Criteria\n\n- [ ] criterion one\n"), behaviors_json, tdd_ok, verify_ac_response, full_test_ok])
    with patch("langgraph_claude_agents.nodes.run_agent", new=mock):
        result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert not result["error"]


async def test_verify_ac_uncovered_loops_back_to_tdd_behavior():
    graph = build_graph()
    behaviors_json = json.dumps(["behavior one"])
    verify_ac_uncovered = json.dumps({"all_covered": False, "uncovered": ["criterion two"]})
    verify_ac_all_covered = json.dumps({"all_covered": True, "uncovered": []})
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "## Acceptance Criteria\n\n- [ ] criterion two\n",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    tdd_ok = json.dumps({"status": "success"})
    full_test_ok = json.dumps({"status": "success"})
    side_effects = [
        _setup_ok(body="## Acceptance Criteria\n\n- [ ] criterion two\n"),
        behaviors_json,
        tdd_ok,
        verify_ac_uncovered,
        tdd_ok,
        verify_ac_all_covered,
        full_test_ok,
    ]
    mock = AsyncMock(side_effect=side_effects)
    with patch("langgraph_claude_agents.nodes.run_agent", new=mock):
        result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert not result["error"]
    assert mock.call_count == len(side_effects), (
        f"expected {len(side_effects)} run_agent calls (loop-back to tdd_behavior), "
        f"got {mock.call_count}"
    )
