from typing import Any

from langgraph_claude_agents.lcel import Runnable


class PromptTemplate(Runnable):
    """Format input variables into a prompt string."""

    def __init__(self, template: str) -> None:
        self.template = template

    def format(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)

    async def ainvoke(self, input: Any) -> str:
        if isinstance(input, dict):
            return self.format(**input)
        return self.format(input=input)
