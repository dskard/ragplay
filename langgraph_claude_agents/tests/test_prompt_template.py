from langgraph_claude_agents.prompt_template import PromptTemplate


def test_prompt_template_formats_input_variables_into_prompt():
    template = PromptTemplate("Hello, {name}! You are {age} years old.")
    result = template.format(name="Ada", age=37)
    assert result == "Hello, Ada! You are 37 years old."
