# Tests that the pytest configuration is correctly set up for the integration marker.
# Functions tested: pyproject.toml [tool.pytest.ini_options] markers configuration,
#                   tests/test_integration.py scaffold structure.
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


def test_integration_test_file_imports_agent_and_nodes():
    # Verify that test_integration.py contains the required module imports.
    test_integration_path = Path(__file__).parent / "test_integration.py"
    content = test_integration_path.read_text()
    assert "langgraph_claude_agents.agent" in content, (
        "Expected test_integration.py to import from langgraph_claude_agents.agent"
    )
    assert "langgraph_claude_agents.nodes" in content, (
        "Expected test_integration.py to import from langgraph_claude_agents.nodes"
    )


def test_integration_test_file_has_marked_test():
    # Verify that test_integration.py contains at least one @pytest.mark.integration test.
    test_integration_path = Path(__file__).parent / "test_integration.py"
    content = test_integration_path.read_text()
    assert "@pytest.mark.integration" in content, (
        "Expected test_integration.py to have at least one @pytest.mark.integration test"
    )
