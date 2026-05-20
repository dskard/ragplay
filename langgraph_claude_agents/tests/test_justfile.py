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
