import asyncio
import click
from langgraph_claude_agents.graph import build_graph


@click.command()
@click.option("--issue", required=True, type=int, help="GitHub issue number to implement")
@click.option("--restart", is_flag=True, default=False, help="Restart from scratch, ignoring checkpoints")
@click.option("--db", default="checkpoints.sqlite", help="Path to the checkpoint database")
def cli(issue: int, restart: bool, db: str) -> None:
    graph = build_graph()
    initial_state = {
        "issue_number": issue,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": "",
        "status": "running",
    }
    asyncio.run(graph.ainvoke(initial_state))


if __name__ == "__main__":
    cli()
