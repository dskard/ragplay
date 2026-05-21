# Tests that the pytest configuration is correctly set up for the integration marker.
# Functions tested: pyproject.toml [tool.pytest.ini_options] markers configuration,
#                   pytest collection behavior for the integration marker.
import subprocess
import sys
import tomllib
from pathlib import Path


def test_integration_marker_is_declared_in_pyproject():
    # Read pyproject.toml from the project root (two levels up from tests/).
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    markers = config["tool"]["pytest"]["ini_options"].get("markers", [])
    # At least one marker entry must start with "integration".
    integration_markers = [m for m in markers if m.startswith("integration")]
    assert integration_markers, "Expected 'integration' marker to be declared in pyproject.toml"


def test_integration_test_file_exists():
    # Confirm the integration test scaffold file has been created.
    test_integration_path = Path(__file__).parent / "test_integration.py"
    assert test_integration_path.exists(), "Expected tests/test_integration.py to exist"


def test_integration_tests_are_collected_by_marker():
    # Use pytest --collect-only to verify at least one test is collected under -m integration.
    # This tests actual pytest behavior rather than file content.
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-m", "integration"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    # A non-zero returncode means a collection error or no tests collected — both are failures.
    assert result.returncode == 0, (
        f"pytest -m integration exited with code {result.returncode}. "
        f"Output: {result.stdout + result.stderr}"
    )
    # "test_integration.py::" only appears in collected item lines, not in error messages.
    assert "test_integration.py::" in result.stdout, (
        "Expected pytest -m integration to collect at least one test from test_integration.py. "
        f"Output was: {result.stdout}"
    )


def test_integration_module_imports_are_valid():
    # Import test_integration as a module to verify its imports resolve without errors.
    # This tests actual import behavior rather than checking file contents as text.
    import importlib.util

    test_integration_path = Path(__file__).parent / "test_integration.py"
    spec = importlib.util.spec_from_file_location("test_integration", test_integration_path)
    mod = importlib.util.module_from_spec(spec)
    # Loading the module exercises all top-level imports.
    spec.loader.exec_module(mod)
    assert mod is not None
