from typing import Any

from langgraph_claude_agents.lcel import Runnable


class PromptTemplate(Runnable):
    """Format input variables into a prompt string."""

    def __init__(self, template: str) -> None:
        self.template = template

    def format(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)

    async def ainvoke(self, input: Any) -> str:
        if not isinstance(input, dict):
            raise TypeError(
                "PromptTemplate.ainvoke expects a dict of template variables; "
                f"got {type(input).__name__}"
            )
        return self.format(**input)
