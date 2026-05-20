from click.testing import CliRunner
from main import cli


def test_cli_requires_issue_flag():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code != 0
    assert "Missing option '--issue'" in result.output


def test_cli_accepts_issue_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--issue", "1"])
    assert result.exit_code == 0


def test_cli_accepts_restart_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--issue", "1", "--restart"])
    assert result.exit_code == 0


def test_cli_accepts_db_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--issue", "1", "--db", "mydb.sqlite"])
    assert result.exit_code == 0
