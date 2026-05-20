"""Verify main.py demonstrates the direct LLM invocation pattern.

main.py is a runnable demo (not the CLI entrypoint) that shows how to call
``invoke_llm`` from ``langgraph_claude_agents.agent`` to send a single prompt
straight to the Claude Agent SDK without going through the LangGraph workflow.
"""

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"


def test_main_py_exists():
    assert MAIN_PY.is_file(), "main.py should exist at the project root as a demo"


def test_main_py_imports_invoke_llm():
    source = MAIN_PY.read_text()
    tree = ast.parse(source)
    imports_invoke_llm = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "langgraph_claude_agents.agent" in node.module:
                if any(alias.name == "invoke_llm" for alias in node.names):
                    imports_invoke_llm = True
    assert imports_invoke_llm, (
        "main.py must import invoke_llm from langgraph_claude_agents.agent"
    )


def test_main_py_calls_invoke_llm():
    source = MAIN_PY.read_text()
    tree = ast.parse(source)
    calls_invoke_llm = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == "invoke_llm":
                calls_invoke_llm = True
    assert calls_invoke_llm, "main.py must call invoke_llm to demonstrate the pattern"


def test_main_py_runs_demo_via_invoke_llm(capsys):
    """Executing main.py as a script should drive invoke_llm and print its result."""
    import runpy

    async def fake_invoke_llm(prompt):
        assert isinstance(prompt, str) and prompt, "demo must pass a non-empty prompt"
        return "demo response"

    with patch("langgraph_claude_agents.agent.invoke_llm", new=fake_invoke_llm):
        runpy.run_path(str(MAIN_PY), run_name="__main__")

    captured = capsys.readouterr()
    assert "demo response" in captured.out, (
        "main.py should print the response returned by invoke_llm"
    )
