from unittest.mock import AsyncMock, patch
from click.testing import CliRunner
from main import cli


def _make_mock_graph(error: str = ""):
    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = {
        "issue_number": 1,
        "issue_title": "",
        "issue_body": "",
        "behaviors": [],
        "current_behavior_index": 0,
        "acceptance_criteria": [],
        "error": error,
        "status": "done",
    }
    return mock_graph


def test_cli_requires_issue_flag():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code != 0
    assert "Missing option '--issue'" in result.output


def test_cli_accepts_issue_flag():
    runner = CliRunner()
    with patch("main.build_graph", return_value=_make_mock_graph()):
        result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 0


def test_cli_accepts_restart_flag():
    runner = CliRunner()
    with patch("main.build_graph", return_value=_make_mock_graph()):
        result = runner.invoke(cli, ["--issue", "1", "--restart"])
    assert result.exit_code == 0


def test_cli_accepts_db_flag():
    runner = CliRunner()
    with patch("main.build_graph", return_value=_make_mock_graph()):
        result = runner.invoke(cli, ["--issue", "1", "--db", "mydb.sqlite"])
    assert result.exit_code == 0


def test_cli_exits_nonzero_when_graph_returns_error():
    runner = CliRunner()
    with patch("main.build_graph", return_value=_make_mock_graph(error="node failed")):
        result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 1


def test_cli_exits_nonzero_when_build_graph_raises_not_implemented():
    runner = CliRunner()
    with patch("main.build_graph", side_effect=NotImplementedError("not ready")):
        result = runner.invoke(cli, ["--issue", "1", "--restart"])
    assert result.exit_code == 1
    assert "not ready" in result.output


def test_cli_passes_db_and_restart_to_build_graph():
    runner = CliRunner()
    with patch("main.build_graph", return_value=_make_mock_graph()) as mock_build:
        runner.invoke(cli, ["--issue", "1", "--restart", "--db", "custom.sqlite"])
    mock_build.assert_called_once_with(db="custom.sqlite", restart=True)
