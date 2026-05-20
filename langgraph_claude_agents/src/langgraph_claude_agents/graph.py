from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
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


def build_graph(db: str = "checkpoints.sqlite", restart: bool = False) -> CompiledStateGraph:
    graph = StateGraph(IssueState)

    graph.add_node("setup", nodes.setup)
    graph.add_node("plan_behaviors", nodes.plan_behaviors)
    graph.add_node("tdd_behavior", nodes.tdd_behavior)
    graph.add_node("verify_ac", nodes.verify_ac)
    graph.add_node("full_test", nodes.full_test)
    graph.add_node("branch_review", nodes.branch_review)
    graph.add_node("teardown", nodes.teardown)

    graph.add_edge(START, "setup")

    graph.add_conditional_edges(
        "setup",
        _route_or_error("plan_behaviors"),
        ["plan_behaviors", "teardown"],
    )
    graph.add_conditional_edges(
        "plan_behaviors",
        _route_tdd_or_error,
        ["tdd_behavior", "verify_ac", "teardown"],
    )
    graph.add_conditional_edges(
        "tdd_behavior",
        _route_tdd_or_error,
        ["tdd_behavior", "verify_ac", "teardown"],
    )
    graph.add_conditional_edges(
        "verify_ac",
        _route_or_error("full_test"),
        ["full_test", "teardown"],
    )
    graph.add_conditional_edges(
        "full_test",
        _route_or_error("branch_review"),
        ["branch_review", "teardown"],
    )
    graph.add_edge("branch_review", "teardown")
    graph.add_edge("teardown", END)

    return graph.compile()
