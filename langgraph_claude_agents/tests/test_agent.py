from unittest.mock import patch
import pytest
from claude_agent_sdk.types import ResultMessage, AssistantMessage, TextBlock
from langgraph_claude_agents import agent


async def make_async_iter(items):
    for item in items:
        yield item


def make_result_message(result: str) -> ResultMessage:
    return ResultMessage(
        subtype="success",
        duration_ms=100,
        duration_api_ms=100,
        is_error=False,
        num_turns=1,
        session_id="test-session",
        result=result,
    )


async def test_run_agent_returns_final_text():
    messages = [
        make_result_message("the answer"),
    ]

    async def fake_query(**kwargs):
        return make_async_iter(messages)

    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await agent.run_agent("hello", ["tool1"])

    assert result == "the answer"
