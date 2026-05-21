# Integration test scaffold for langgraph_claude_agents.
# Tests marked @pytest.mark.integration cover two categories:
#   1. Tests that require a live LLM API (real external service calls).
#   2. Tests that exercise the full node→run_agent→query integration path
#      with query patched — no live network calls needed, but kept under
#      this marker so all integration-layer tests run together.
# Run with: pytest -m integration
# Skip with: pytest -m "not integration"
import json
import uuid
from unittest.mock import patch

import pytest

from claude_agent_sdk.types import ResultMessage
from langgraph_claude_agents import agent, nodes
from langgraph_claude_agents.agent import run_agent
from langgraph_claude_agents.graph import graph
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


def make_state(**overrides):
    # Build a minimal IssueState dict for node tests, with optional field overrides.
    base = {
        "issue_number": 7,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
        "model": None,
    }
    base.update(overrides)
    return base


def make_query_returning(result_text):
    # Return an async generator function that yields a single ResultMessage with result_text.
    async def fake_query(**kwargs):
        yield make_result_message(result_text)
    return fake_query


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_setup_happy_path_updates_state_via_query():
    # Scenario: query yields a ResultMessage whose result is valid setup JSON.
    # Function(s): setup (via run_agent via query)
    # Verifies setup returns correct State fields when query produces valid output.
    result_json = json.dumps({"issue_title": "My Issue", "issue_body": "Body text"})
    with patch("langgraph_claude_agents.agent.query", new=make_query_returning(result_json)):
        result = await nodes.setup(make_state())

    assert result["issue_title"] == "My Issue"
    assert result["issue_body"] == "Body text"
    assert result["status"] == "setup_done"
    assert "error" not in result


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_plan_behaviors_happy_path_updates_state_via_query():
    # Scenario: query yields a ResultMessage whose result is a valid JSON array of behaviors.
    # Function(s): plan_behaviors (via run_agent via query)
    # Verifies plan_behaviors returns behaviors and resets index when query produces valid output.
    behaviors = ["check tool available", "parse output"]
    issue_body = "## Acceptance Criteria\n\n- [ ] tool is available\n- [ ] output is parsed\n"
    result_json = json.dumps(behaviors)
    with patch(
        "langgraph_claude_agents.agent.query",
        new=make_query_returning(result_json),
    ):
        result = await nodes.plan_behaviors(make_state(issue_body=issue_body))

    assert result["behaviors"] == behaviors
    assert result["current_behavior_index"] == 0
    assert result["acceptance_criteria"] == ["tool is available", "output is parsed"]
    assert "error" not in result


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_tdd_behavior_happy_path_increments_index_via_query():
    # Scenario: query yields a ResultMessage whose result is {"status": "success"}.
    # Function(s): tdd_behavior (via run_agent via query)
    # Verifies tdd_behavior increments current_behavior_index when query produces valid output.
    result_json = json.dumps({"status": "success"})
    state = make_state(behaviors=["implement feature X"], current_behavior_index=0)
    with patch("langgraph_claude_agents.agent.query", new=make_query_returning(result_json)):
        result = await nodes.tdd_behavior(state)

    assert result["current_behavior_index"] == 1
    assert "error" not in result


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_verify_ac_happy_path_returns_empty_dict_via_query():
    # Scenario: query yields a ResultMessage with all_covered=True.
    # Function(s): verify_ac (via run_agent via query)
    # Verifies verify_ac returns {} when all acceptance criteria are covered.
    result_json = json.dumps({"all_covered": True, "uncovered": []})
    state = make_state(acceptance_criteria=["tool is available"])
    with patch("langgraph_claude_agents.agent.query", new=make_query_returning(result_json)):
        result = await nodes.verify_ac(state)

    assert result == {}


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_full_test_happy_path_returns_empty_dict_via_query():
    # Scenario: query yields a ResultMessage with {"status": "success"}.
    # Function(s): full_test (via run_agent via query)
    # Verifies full_test returns {} when all tests pass.
    result_json = json.dumps({"status": "success"})
    with patch("langgraph_claude_agents.agent.query", new=make_query_returning(result_json)):
        result = await nodes.full_test(make_state())

    assert result == {}


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_branch_review_happy_path_returns_empty_dict_via_query():
    # Scenario: query yields a ResultMessage with {"status": "success"}.
    # Function(s): branch_review (via run_agent via query)
    # Verifies branch_review returns {} when the review passes.
    result_json = json.dumps({"status": "success"})
    with patch("langgraph_claude_agents.agent.query", new=make_query_returning(result_json)):
        result = await nodes.branch_review(make_state())

    assert result == {}


@pytest.mark.integration  # grouped with other node integration tests per issue AC
async def test_teardown_happy_path_returns_done_status():
    # Scenario: state has no error set.
    # Function(s): teardown
    # Verifies teardown returns {"status": "done"} when there is no error in state.
    result = await nodes.teardown(make_state(error=""))

    assert result == {"status": "done"}


def make_empty_query():
    # Return an async generator function that yields nothing (no ResultMessage).
    async def fake_query(**kwargs):
        return
        yield  # make this an async generator
    return fake_query


def make_sequential_query(*result_texts):
    # Return (fake_query, call_count) where fake_query yields a different ResultMessage
    # per call. Raises IndexError if called more times than responses provided (over-call
    # detection). Callers should assert call_count[0] == len(result_texts) afterwards
    # to catch under-call (skipped nodes).
    call_count = [0]

    async def fake_query(**kwargs):
        idx = call_count[0]
        if idx >= len(result_texts):
            raise IndexError(
                f"make_sequential_query called {idx + 1} times but only "
                f"{len(result_texts)} responses provided"
            )
        call_count[0] += 1
        yield make_result_message(result_texts[idx])

    return fake_query, call_count


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_setup_sets_error_when_query_yields_no_result_message():
    # Scenario: query yields no messages, so run_agent returns "".
    # Function(s): setup (via run_agent via query)
    # Verifies setup sets error in State when run_agent returns empty string.
    with patch("langgraph_claude_agents.agent.query", new=make_empty_query()):
        result = await nodes.setup(make_state())

    assert "error" in result
    assert result["error"]


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_plan_behaviors_sets_error_when_query_yields_no_result_message():
    # Scenario: query yields no messages, so run_agent returns "".
    # Function(s): plan_behaviors (via run_agent via query)
    # Verifies plan_behaviors sets error in State when run_agent returns empty string.
    with patch("langgraph_claude_agents.agent.query", new=make_empty_query()):
        result = await nodes.plan_behaviors(make_state())

    assert "error" in result
    assert result["error"]


@pytest.mark.integration  # exercises node→run_agent→query integration path
async def test_tdd_behavior_sets_error_when_query_yields_no_result_message():
    # Scenario: query yields no messages, so run_agent returns "".
    # Function(s): tdd_behavior (via run_agent via query)
    # Verifies tdd_behavior sets error in State when run_agent returns empty string.
    state = make_state(behaviors=["implement feature X"], current_behavior_index=0)
    with patch("langgraph_claude_agents.agent.query", new=make_empty_query()):
        result = await nodes.tdd_behavior(state)

    assert "error" in result
    assert result["error"]


@pytest.mark.integration
async def test_graph_end_to_end_all_nodes_in_sequence():
    # Scenario: all six run_agent nodes execute in order with a stubbed query that
    #   returns a distinct ResultMessage per call; teardown follows with no agent call.
    # Function(s): graph.ainvoke (module-level graph backed by MemorySaver)
    # Verifies the final State has status=="done" with all expected fields populated
    # when the behavior list contains exactly one item so the TDD cycle fires once.

    issue_body = "## Acceptance Criteria\n\n- [ ] criterion one\n"

    # Six sequential responses, one per node that calls run_agent:
    #   1. setup        -> JSON with issue_title and issue_body
    #   2. plan_behaviors -> JSON array with exactly one behavior
    #   3. tdd_behavior -> {"status": "success"}
    #   4. verify_ac    -> {"all_covered": true, "uncovered": []}
    #   5. full_test    -> {"status": "success"}
    #   6. branch_review -> {"status": "success"}
    responses = [
        json.dumps({"issue_title": "Test Issue", "issue_body": issue_body}),
        json.dumps(["behavior one"]),
        json.dumps({"status": "success"}),
        json.dumps({"all_covered": True, "uncovered": []}),
        json.dumps({"status": "success"}),
        json.dumps({"status": "success"}),
    ]

    initial_state = {
        "issue_number": 99,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
        "model": None,
    }

    # Use a unique thread ID each run to prevent MemorySaver checkpoint contamination.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    fake_query, call_count = make_sequential_query(*responses)
    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await graph.ainvoke(initial_state, config=config)

    # Verify all six nodes actually fired — catches silent node-skipping regressions.
    assert call_count[0] == len(responses)
    assert result["status"] == "done"
    assert result["issue_title"] == "Test Issue"
    assert result["issue_body"] == issue_body
    assert result["behaviors"] == ["behavior one"]
    assert result["current_behavior_index"] == 1
    assert result["acceptance_criteria"] == ["criterion one"]
    assert not result.get("error")
