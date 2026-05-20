from pathlib import Path


def test_readme_exists():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    assert readme.is_file(), f"Expected README.md at {readme}"


def test_readme_has_project_name_h1():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    lines = readme.read_text().splitlines()
    h1s = [line[2:].strip() for line in lines if line.startswith("# ")]
    assert "LangGraph Claude Agents" in h1s, (
        f"Expected a level-1 heading 'LangGraph Claude Agents' in README.md; found {h1s}"
    )
