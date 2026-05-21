from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage


async def run_agent(
    prompt: str, allowed_tools: list[str], *, model: str | None = None
) -> str:
    kwargs = {"allowed_tools": allowed_tools}
    if model is not None:
        kwargs["model"] = model
    options = ClaudeAgentOptions(**kwargs)
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            return message.result or ""
    return ""


async def invoke_llm(prompt: str) -> str:
    return await run_agent(prompt, allowed_tools=[])
