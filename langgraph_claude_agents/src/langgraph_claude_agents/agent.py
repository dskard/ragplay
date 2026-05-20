from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage


async def run_agent(prompt: str, allowed_tools: list[str]) -> str:
    options = ClaudeAgentOptions(allowed_tools=allowed_tools)
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            return message.result or ""
    return ""
