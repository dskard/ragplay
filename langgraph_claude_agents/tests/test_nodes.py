import inspect
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
    result = await fn(state)
    assert isinstance(result, dict)
