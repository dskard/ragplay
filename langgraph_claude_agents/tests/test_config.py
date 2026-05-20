import tomllib
from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_declares_console_script():
    with open(_ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    scripts = data.get("project", {}).get("scripts", {})
    assert scripts.get("langgraph-claude-agents") == "langgraph_claude_agents.cli:cli"
