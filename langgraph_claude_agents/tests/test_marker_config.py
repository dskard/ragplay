# Tests that the pytest configuration is correctly set up for the integration marker.
# Functions tested: pyproject.toml [tool.pytest.ini_options] markers configuration.
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
