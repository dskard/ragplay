"""Verify the scaffolding supports dependency management via pyproject.toml + uv.lock.

File existence alone is not enough: the files must actually wire the project
into uv's dependency-management workflow. Specifically:
  * pyproject.toml must declare the project name and at least one runtime
    dependency under `[project]`.
  * uv.lock must reference that same project name, proving the lock was
    generated for this project.
"""

import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_declares_project_and_dependencies():
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml is missing"

    data = tomllib.loads(pyproject_path.read_text())
    project = data.get("project", {})

    assert project.get("name"), "pyproject.toml [project] must declare a name"
    deps = project.get("dependencies", [])
    assert isinstance(deps, list) and deps, (
        "pyproject.toml [project].dependencies must list at least one dependency"
    )


def test_uv_lock_locks_this_project():
    lock_path = PROJECT_ROOT / "uv.lock"
    assert lock_path.is_file(), "uv.lock is missing"

    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    project_name = pyproject["project"]["name"]

    lock_text = lock_path.read_text()
    assert project_name in lock_text, (
        f"uv.lock does not reference project name {project_name!r}; "
        "it may have been generated for a different project."
    )
