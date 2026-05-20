from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner
from main import cli


def _make_mock_graph(error: str = ""):
    mock_graph = AsyncMock()
    mock_graph.checkpointer = MagicMock()
    mock_graph.checkpointer.adelete_thread = AsyncMock()
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


def _mock_build(mock_graph=None, db_calls=None):
    if mock_graph is None:
        mock_graph = _make_mock_graph()

    @asynccontextmanager
    async def _build(db):
        if db_calls is not None:
            db_calls.append(db)
        yield mock_graph

    return _build


def test_cli_requires_issue_flag():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code != 0
    assert "Missing option '--issue'" in result.output


def test_cli_accepts_issue_flag():
    runner = CliRunner()
    with patch("main.build_graph", _mock_build()):
        result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 0


def test_cli_accepts_restart_flag():
    runner = CliRunner()
    mock_graph = _make_mock_graph()
    with patch("main.build_graph", _mock_build(mock_graph)):
        result = runner.invoke(cli, ["--issue", "1", "--restart"])
    assert result.exit_code == 0
    mock_graph.checkpointer.adelete_thread.assert_called_once_with("issue-1")


def test_cli_accepts_db_flag():
    runner = CliRunner()
    with patch("main.build_graph", _mock_build()):
        result = runner.invoke(cli, ["--issue", "1", "--db", "mydb.sqlite"])
    assert result.exit_code == 0


def test_cli_completes_when_graph_invokes_successfully():
    runner = CliRunner()
    with patch("main.build_graph", _mock_build()):
        result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 0


def test_cli_passes_db_to_build_graph():
    runner = CliRunner()
    db_calls = []
    with patch("main.build_graph", _mock_build(db_calls=db_calls)):
        runner.invoke(cli, ["--issue", "1", "--db", "custom.sqlite"])
    assert db_calls == ["custom.sqlite"]


def test_cli_exits_nonzero_when_graph_raises_exception():
    runner = CliRunner()
    mock_graph = _make_mock_graph()
    mock_graph.ainvoke.side_effect = RuntimeError("sdk failure")
    with patch("main.build_graph", _mock_build(mock_graph)):
        result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 1
    assert "sdk failure" in result.output


def test_cli_exits_nonzero_when_graph_returns_error_in_state():
    runner = CliRunner()
    mock_graph = _make_mock_graph(error="tdd step failed unrecoverably")
    with patch("main.build_graph", _mock_build(mock_graph)):
        result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 1
    assert "tdd step failed unrecoverably" in result.output
