from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_project_scaffolding_files_exist():
    expected = ["pyproject.toml", "uv.lock", ".envrc.example", "README.md", "Justfile"]
    missing = [name for name in expected if not (PROJECT_ROOT / name).is_file()]
    assert not missing, f"Missing scaffolding files: {missing}"
