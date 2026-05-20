"""Verify environment variable configuration is documented via .envrc.example."""

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ENVRC_EXAMPLE = _ROOT / ".envrc.example"


def test_envrc_example_documents_each_exported_variable():
    """Each `export VAR=` in .envrc.example must be preceded by a comment naming VAR."""
    lines = _ENVRC_EXAMPLE.read_text().splitlines()

    export_re = re.compile(r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=")
    undocumented = []
    for i, line in enumerate(lines):
        match = export_re.match(line)
        if not match:
            continue
        var = match.group(1)
        # Look upward at preceding lines (skipping blanks) for a comment that
        # explicitly mentions this variable name.
        documented = False
        for j in range(i - 1, max(-1, i - 7), -1):
            stripped = lines[j].strip()
            if not stripped:
                continue
            if stripped.startswith("#") and var in stripped:
                documented = True
                break
            if not stripped.startswith("#"):
                break
        if not documented:
            undocumented.append(var)

    assert not undocumented, (
        f"Variables exported in .envrc.example without a documenting comment "
        f"that names them: {undocumented}"
    )
