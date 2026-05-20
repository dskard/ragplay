from pathlib import Path


def test_readme_exists():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    assert readme.is_file(), f"Expected README.md at {readme}"
