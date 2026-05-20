"""Tests for the project's Justfile."""

import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_JUSTFILE = _ROOT / "Justfile"


def _just_summary() -> list[str]:
    if shutil.which("just") is None:
        pytest.skip("`just` is not installed")
    result = subprocess.run(
        ["just", "--summary"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


def test_justfile_exists():
    assert _JUSTFILE.is_file(), f"Expected Justfile at {_JUSTFILE}"


def test_justfile_provides_setup_target():
    assert "setup" in _just_summary()


def test_justfile_provides_run_target():
    assert "run" in _just_summary()


def test_justfile_setup_target_runs_uv_sync():
    body = _JUSTFILE.read_text()
    assert "uv sync" in body, (
        "Expected the `setup` recipe to invoke `uv sync`; "
        f"Justfile contents:\n{body}"
    )


def _just_dry_run(*args: str) -> str:
    if shutil.which("just") is None:
        pytest.skip("`just` is not installed")
    # `just -n` echoes the recipe commands to stderr.
    result = subprocess.run(
        ["just", "-n", *args],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stderr.strip()


def test_just_setup_dry_run_invokes_uv_sync():
    # Public interface: invoking `just setup` must run `uv sync`.
    assert _just_dry_run("setup") == "uv sync"


def test_just_run_dry_run_forwards_issue_argument():
    # Public interface: invoking `just run <issue>` must forward the issue
    # number to the registered console script via `--issue`.
    assert (
        _just_dry_run("run", "42")
        == "uv run langgraph-claude-agents --issue 42"
    )


def test_justfile_default_recipe_lists_setup_and_run_for_bootstrap():
    # Behavior: the Justfile bootstraps the project. Running `just` with no
    # arguments must surface the `setup` and `run` targets so a new
    # contributor can discover how to get started.
    if shutil.which("just") is None:
        pytest.skip("`just` is not installed")
    result = subprocess.run(
        ["just"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout + result.stderr
    assert "setup" in output, (
        f"Expected default `just` invocation to list `setup`; got:\n{output}"
    )
    assert "run" in output, (
        f"Expected default `just` invocation to list `run`; got:\n{output}"
    )


def test_just_list_documents_setup_and_run_for_bootstrap():
    # Behavior: the Justfile bootstraps the project. `just --list` (the
    # discovery interface for new contributors) must surface human-readable
    # descriptions for both the `setup` and `run` recipes so a newcomer can
    # tell what each bootstrap target does without reading the Justfile.
    if shutil.which("just") is None:
        pytest.skip("`just` is not installed")
    result = subprocess.run(
        ["just", "--list"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout
    setup_line = next(
        (line for line in output.splitlines() if line.strip().startswith("setup")),
        "",
    )
    run_line = next(
        (line for line in output.splitlines() if line.strip().startswith("run")),
        "",
    )
    assert "#" in setup_line, (
        f"Expected `just --list` to show a description for `setup`; got:\n{output}"
    )
    assert "#" in run_line, (
        f"Expected `just --list` to show a description for `run`; got:\n{output}"
    )


def test_just_setup_installs_declared_dependencies():
    # Behavior: invoking `just setup` must install the project's declared
    # runtime dependencies so they are importable via `uv run`. We exercise
    # the public interface (the recipe itself) and then assert that a
    # declared dependency is available in the synced environment.
    if shutil.which("just") is None:
        pytest.skip("`just` is not installed")
    setup_result = subprocess.run(
        ["just", "setup"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert setup_result.returncode == 0, (
        "`just setup` failed:\n"
        f"stdout:\n{setup_result.stdout}\nstderr:\n{setup_result.stderr}"
    )
    import_result = subprocess.run(
        [
            "uv",
            "run",
            "--no-sync",
            "python",
            "-c",
            "import click, langgraph, langgraph_claude_agents",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert import_result.returncode == 0, (
        "Expected declared dependencies to be importable after `just setup`; "
        f"stderr:\n{import_result.stderr}"
    )


def test_justfile_run_target_uses_console_script():
    # main.py has been removed in favour of the langgraph-claude-agents console
    # script (see test_config.test_main_py_does_not_exist). The `run` recipe
    # must therefore invoke the console script rather than `python3 main.py`.
    body = _JUSTFILE.read_text()
    assert "main.py" not in body, (
        "Justfile `run` recipe should not reference `main.py`; "
        f"Justfile contents:\n{body}"
    )
    assert "langgraph-claude-agents" in body, (
        "Expected Justfile `run` recipe to invoke the "
        "`langgraph-claude-agents` console script; "
        f"Justfile contents:\n{body}"
    )
