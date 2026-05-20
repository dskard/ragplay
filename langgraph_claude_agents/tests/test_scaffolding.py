from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent


def test_project_scaffolding_files_exist():
    expected = ["pyproject.toml", "uv.lock", ".envrc.example", "README.md", "Justfile"]
    missing = [name for name in expected if not (PROJECT_ROOT / name).is_file()]
    assert not missing, f"Missing scaffolding files: {missing}"


def test_envrc_examples_document_required_env_vars():
    """Both top-level and project-level .envrc.example must document required env vars.

    The project depends on claude_agent_sdk, which requires ANTHROPIC_API_KEY.
    The top-level .envrc.example must declare it, and the project-level
    .envrc.example must either declare it directly or `source_up` the parent
    so the variable is available when the project's direnv loads.
    """
    top_level = REPO_ROOT / ".envrc.example"
    project_level = PROJECT_ROOT / ".envrc.example"

    if not top_level.is_file():
        pytest.skip(f"Top-level .envrc.example not found at {top_level}")

    top_text = top_level.read_text()
    project_text = project_level.read_text()

    assert "ANTHROPIC_API_KEY" in top_text, (
        "Top-level .envrc.example must document ANTHROPIC_API_KEY"
    )

    inherits_parent = "source_up" in project_text
    declares_directly = "ANTHROPIC_API_KEY" in project_text
    assert inherits_parent or declares_directly, (
        "Project-level .envrc.example must either `source_up` from the "
        "repo-root .envrc or declare ANTHROPIC_API_KEY directly"
    )
