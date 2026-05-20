from langgraph_claude_agents.state import IssueState


async def setup(state: IssueState) -> dict:
    return {}


async def plan_behaviors(state: IssueState) -> dict:
    return {}


async def tdd_behavior(state: IssueState) -> dict:
    return {"current_behavior_index": state.get("current_behavior_index", 0) + 1}


async def verify_ac(state: IssueState) -> dict:
    return {}


async def full_test(state: IssueState) -> dict:
    return {}


async def branch_review(state: IssueState) -> dict:
    return {}


async def teardown(state: IssueState) -> dict:
    return {"status": "done"}
