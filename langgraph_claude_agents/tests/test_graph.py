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
        "error": "something failed",
        "status": "running",
    }
    result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert result["error"] == "something failed"


async def test_happy_path_with_behaviors_loops_tdd_until_exhausted():
    graph = build_graph()
    state = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": ["behavior one", "behavior two"],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    result = await graph.ainvoke(state)
    assert result["status"] == "done"
    assert result["error"] == ""
    assert result["current_behavior_index"] == 2
