import tomllib
from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent


def test_main_py_does_not_exist():
    assert not (_ROOT / "main.py").exists(), "main.py should be deleted; CLI lives in langgraph_claude_agents.cli"


def test_justfile_run_uses_registered_script():
    justfile = (_ROOT / "Justfile").read_text()
    assert "uv run langgraph-claude-agents --issue" in justfile


def test_pyproject_declares_console_script():
    with open(_ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    scripts = data.get("project", {}).get("scripts", {})
    assert scripts.get("langgraph-claude-agents") == "langgraph_claude_agents.cli:cli"
