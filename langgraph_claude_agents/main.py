import asyncio
import sys
import click
from langgraph_claude_agents.graph import build_graph


@click.command()
@click.option("--issue", required=True, type=int, help="GitHub issue number to implement")
@click.option("--restart", is_flag=True, default=False, help="Restart from scratch, ignoring checkpoints")
@click.option("--db", default="checkpoints.sqlite", show_default=True, help="Path to the checkpoint database")
def cli(issue: int, restart: bool, db: str) -> None:
    try:
        graph = build_graph(db=db, restart=restart)
    except NotImplementedError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
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
    try:
        asyncio.run(graph.ainvoke(initial_state))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
