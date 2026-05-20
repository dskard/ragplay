import json
from unittest.mock import AsyncMock, patch
import pytest
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph_claude_agents.graph import build_graph

_CONFIG = {"configurable": {"thread_id": "test-thread"}}


def _setup_ok(issue_number=1, title="Test Issue", body=""):
    return json.dumps({"issue_title": title, "issue_body": body})


async def test_graph_compiles():
    async with build_graph(db=":memory:") as graph:
        assert graph is not None


async def test_graph_has_all_seven_nodes():
    async with build_graph(db=":memory:") as graph:
        node_names = set(graph.nodes.keys())
    expected = {"setup", "plan_behaviors", "tdd_behavior", "verify_ac",
                "full_test", "branch_review", "teardown"}
    assert expected.issubset(node_names)


async def test_build_graph_uses_async_sqlite_saver(tmp_path):
    db = str(tmp_path / "test.db")
    async with build_graph(db=db) as graph:
        assert isinstance(graph.checkpointer, AsyncSqliteSaver)


async def test_checkpoint_persisted_to_sqlite_after_node(tmp_path):
    db = str(tmp_path / "checkpoints.db")
    config = {"configurable": {"thread_id": "issue-42"}}
    state = {
        "issue_number": 42,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    mock_run = AsyncMock(side_effect=[
        _setup_ok(), "[]",
        '{"status": "success"}',
        '{"status": "success"}',
    ])
    async with build_graph(db=db) as graph:
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            await graph.ainvoke(state, config=config)
        checkpoints = [c async for c in graph.checkpointer.alist(config)]
    assert len(checkpoints) > 0


async def test_restart_clears_checkpoint(tmp_path):
    db = str(tmp_path / "checkpoints.db")
    config = {"configurable": {"thread_id": "issue-42"}}
    state = {
        "issue_number": 42,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    mock_run = AsyncMock(side_effect=[
        _setup_ok(), "[]",
        '{"status": "success"}',
        '{"status": "success"}',
    ])
    async with build_graph(db=db) as graph:
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            await graph.ainvoke(state, config=config)
        await graph.checkpointer.adelete_thread("issue-42")
        checkpoints = [c async for c in graph.checkpointer.alist(config)]
    assert len(checkpoints) == 0


async def test_happy_path_no_behaviors_routes_to_done():
    async with build_graph(db=":memory:") as graph:
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
        mock_run = AsyncMock(side_effect=[
            _setup_ok(), "[]",
            '{"status": "success"}',
            '{"status": "success"}',
        ])
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            result = await graph.ainvoke(state, config=_CONFIG)
    assert result["status"] == "done"
    assert not result.get("error")


async def test_error_in_setup_routes_to_teardown():
    async with build_graph(db=":memory:") as graph:
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
        mock_run = AsyncMock(return_value=error_output)
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            result = await graph.ainvoke(state, config=_CONFIG)
    assert result["status"] == "error"
    assert result.get("error")


async def test_error_in_plan_behaviors_routes_to_teardown():
    async with build_graph(db=":memory:") as graph:
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
        mock_run = AsyncMock(side_effect=[_setup_ok(), "not valid json"])
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            result = await graph.ainvoke(state, config=_CONFIG)
    assert result["status"] == "error"
    assert result.get("error")


async def test_happy_path_with_behaviors_loops_tdd_until_exhausted():
    async with build_graph(db=":memory:") as graph:
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
        branch_review_ok = json.dumps({"status": "success"})
        mock_run = AsyncMock(side_effect=[_setup_ok(), behaviors_json, tdd_ok, tdd_ok, full_test_ok, branch_review_ok])
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            result = await graph.ainvoke(state, config=_CONFIG)
    assert result["status"] == "done"
    assert not result.get("error")


async def test_verify_ac_all_covered_routes_to_full_test():
    async with build_graph(db=":memory:") as graph:
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
        branch_review_ok = json.dumps({"status": "success"})
        mock_run = AsyncMock(side_effect=[
            _setup_ok(body="## Acceptance Criteria\n\n- [ ] criterion one\n"),
            behaviors_json, tdd_ok, verify_ac_response, full_test_ok, branch_review_ok,
        ])
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            result = await graph.ainvoke(state, config=_CONFIG)
    assert result["status"] == "done"
    assert not result.get("error")


async def test_verify_ac_uncovered_loops_back_to_tdd_behavior():
    async with build_graph(db=":memory:") as graph:
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
        branch_review_ok = json.dumps({"status": "success"})
        side_effects = [
            _setup_ok(body="## Acceptance Criteria\n\n- [ ] criterion two\n"),
            behaviors_json,
            tdd_ok,
            verify_ac_uncovered,
            tdd_ok,
            verify_ac_all_covered,
            full_test_ok,
            branch_review_ok,
        ]
        mock_run = AsyncMock(side_effect=side_effects)
        with patch("langgraph_claude_agents.nodes.run_agent", new=mock_run):
            result = await graph.ainvoke(state, config=_CONFIG)
    assert result["status"] == "done"
    assert not result.get("error")
    assert mock_run.call_count == len(side_effects), (
        f"expected {len(side_effects)} run_agent calls (loop-back to tdd_behavior), "
        f"got {mock_run.call_count}"
    )
