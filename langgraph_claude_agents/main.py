"""Demonstrate the direct LLM invocation pattern with a PromptTemplate.

This script is a runnable example, not the CLI entrypoint. It shows how to
build a prompt from a ``PromptTemplate`` and then send the formatted prompt to
the Claude Agent SDK via ``invoke_llm`` without allowing any tools and without
going through the LangGraph workflow.

The CLI for implementing GitHub issues lives in ``langgraph_claude_agents.cli``
and is exposed as the ``langgraph-claude-agents`` console script.
"""

import asyncio

from langgraph_claude_agents.agent import invoke_llm
from langgraph_claude_agents.prompt_template import PromptTemplate


GREETING_TEMPLATE = PromptTemplate("Say hello to {name} in one short sentence.")


async def main() -> None:
    prompt = GREETING_TEMPLATE.format(name="world")
    response = await invoke_llm(prompt)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
