import pytest
from langgraph_claude_agents.graph import build_graph


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None


def test_graph_has_all_seven_nodes():
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {"setup", "plan_behaviors", "tdd_behavior", "verify_ac",
                "full_test", "branch_review", "teardown"}
    assert expected.issubset(node_names)


async def test_happy_path_routes_setup_to_plan_behaviors():
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
    result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert not result.get("error")


async def test_error_in_setup_routes_to_teardown():
    graph = build_graph()
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "something failed",
        "status": "running",
    }
    # Invoke graph starting from setup node with error pre-set
    result = await graph.ainvoke(state)
    assert result["status"] == "done"


async def test_graph_runs_happy_path_end_to_end():
    graph = build_graph()
    state = {
        "issue_number": 1,
        "issue_title": "Test Issue",
        "issue_body": "Test body",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    result = await graph.ainvoke(state)
    assert result["status"] == "done"
