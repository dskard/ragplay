"""Demonstrate the direct LLM invocation pattern.

This script is a runnable example, not the CLI entrypoint. It shows how to call
``invoke_llm`` to send a single prompt straight to the Claude Agent SDK without
allowing any tools and without going through the LangGraph workflow.

The CLI for implementing GitHub issues lives in ``langgraph_claude_agents.cli``
and is exposed as the ``langgraph-claude-agents`` console script.
"""

import asyncio

from langgraph_claude_agents.agent import invoke_llm


DEMO_PROMPT = "Say hello in one short sentence."


async def main() -> None:
    response = await invoke_llm(DEMO_PROMPT)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
