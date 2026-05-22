from contextlib import asynccontextmanager
from typing import AsyncIterator
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph_claude_agents.state import IssueState
from langgraph_claude_agents import nodes


def _route_or_error(next_node: str):
    def _router(state: IssueState) -> str:
        if state.get("error"):
            return "teardown"
        return next_node
    return _router


def _route_tdd_or_error(state: IssueState) -> str:
    if state.get("error"):
        return "teardown"
    behaviors = state.get("behaviors", [])
    idx = state.get("current_behavior_index", 0)
    if idx < len(behaviors):
        return "tdd_behavior"
    return "verify_ac"


def _route_verify_ac(state: IssueState) -> str:
    if state.get("error"):
        return "teardown"
    behaviors = state.get("behaviors", [])
    idx = state.get("current_behavior_index", 0)
    if idx < len(behaviors):
        return "tdd_behavior"
    return "full_test"


def _make_graph(checkpointer) -> CompiledStateGraph:
    g = StateGraph(IssueState)

    g.add_node("setup", nodes.setup)
    g.add_node("plan_behaviors", nodes.plan_behaviors)
    g.add_node("tdd_behavior", nodes.tdd_behavior)
    g.add_node("verify_ac", nodes.verify_ac)
    g.add_node("full_test", nodes.full_test)
    g.add_node("branch_review", nodes.branch_review)
    g.add_node("teardown", nodes.teardown)

    g.add_edge(START, "setup")

    g.add_conditional_edges(
        "setup",
        _route_or_error("plan_behaviors"),
        ["plan_behaviors", "teardown"],
    )
    g.add_conditional_edges(
        "plan_behaviors",
        _route_tdd_or_error,
        ["tdd_behavior", "verify_ac", "teardown"],
    )
    g.add_conditional_edges(
        "tdd_behavior",
        _route_tdd_or_error,
        ["tdd_behavior", "verify_ac", "teardown"],
    )
    g.add_conditional_edges(
        "verify_ac",
        _route_verify_ac,
        ["tdd_behavior", "full_test", "teardown"],
    )
    g.add_conditional_edges(
        "full_test",
        _route_or_error("branch_review"),
        ["branch_review", "teardown"],
    )
    g.add_edge("branch_review", "teardown")
    # LangGraph requires an explicit edge to END.
    g.add_edge("teardown", END)

    return g.compile(checkpointer=checkpointer)


@asynccontextmanager
async def build_graph(
    db: str = ".langgraph_checkpoints.db",
) -> AsyncIterator[CompiledStateGraph]:
    async with AsyncSqliteSaver.from_conn_string(db) as checkpointer:
        yield _make_graph(checkpointer)


graph = _make_graph(None)
