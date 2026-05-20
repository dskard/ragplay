from unittest.mock import patch
import pytest
from claude_agent_sdk.types import ResultMessage
from langgraph_claude_agents import agent


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
    messages = [make_result_message("the answer")]

    async def fake_query(**kwargs):
        for msg in messages:
            yield msg

    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await agent.run_agent("hello", ["tool1"])

    assert result == "the answer"


async def test_invoke_llm_returns_response_text():
    messages = [make_result_message("direct response")]

    async def fake_query(**kwargs):
        for msg in messages:
            yield msg

    with patch("langgraph_claude_agents.agent.query", new=fake_query):
        result = await agent.invoke_llm("ping")

    assert result == "direct response"


async def test_run_agent_propagates_iterator_exceptions():
    async def fake_query(**kwargs):
        raise RuntimeError("sdk failure")
        yield  # make it an async generator

    with pytest.raises(RuntimeError, match="sdk failure"):
        with patch("langgraph_claude_agents.agent.query", new=fake_query):
            await agent.run_agent("hello", [])
