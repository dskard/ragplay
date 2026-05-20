"""Verify project-level .envrc.example inherits env config from the repo-root.

Behavior: Environment variable configuration is documented via .envrc.example
files at both the top-level (repo root) and in the project package directory.
The project-level file should `source_up` so secrets declared once at the
top-level (e.g. ANTHROPIC_API_KEY) flow into the project's direnv environment.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent


def test_project_envrc_example_sources_up_to_top_level():
    top_level = REPO_ROOT / ".envrc.example"
    project_level = PROJECT_ROOT / ".envrc.example"

    assert top_level.is_file(), f"Top-level .envrc.example missing at {top_level}"
    assert project_level.is_file(), f"Project-level .envrc.example missing at {project_level}"

    project_text = project_level.read_text()
    assert "source_up" in project_text, (
        "Project-level .envrc.example must `source_up` to inherit env config "
        "documented in the repo-root .envrc.example"
    )
