import asyncio
import sys
import click
from langgraph_claude_agents.graph import build_graph


@click.command()
@click.option("--issue", required=True, type=int, help="GitHub issue number to implement")
@click.option("--restart", is_flag=True, default=False, help="Restart from scratch, ignoring checkpoints")
@click.option("--db", default=".langgraph_checkpoints.db", show_default=True, help="Path to the checkpoint database")
def cli(issue: int, restart: bool, db: str) -> None:
    async def _run() -> None:
        async with build_graph(db=db) as graph:
            thread_id = f"issue-{issue}"
            if restart:
                await graph.checkpointer.adelete_thread(thread_id)
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
            config = {"configurable": {"thread_id": thread_id}}
            await graph.ainvoke(initial_state, config=config)

    try:
        asyncio.run(_run())
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
