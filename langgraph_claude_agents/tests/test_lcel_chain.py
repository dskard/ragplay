import pytest

from langgraph_claude_agents.lcel import StrOutputParser
from langgraph_claude_agents.prompt_template import PromptTemplate


async def test_prompt_template_ainvoke_rejects_non_dict_input():
    prompt = PromptTemplate("Say hello to {name}")
    with pytest.raises(TypeError, match="dict of template variables"):
        await prompt.ainvoke("Ada")


async def test_lcel_chain_pipes_prompt_into_model_and_parses_string_output():
    prompt = PromptTemplate("Say hello to {name}")

    async def fake_model(text: str) -> str:
        return f"<response to: {text}>"

    chain = prompt | fake_model | StrOutputParser()
    result = await chain.ainvoke({"name": "Ada"})

    assert result == "<response to: Say hello to Ada>"
