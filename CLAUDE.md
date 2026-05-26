# ragplay

## Package management

These projects use `uv`. Never call `pip` directly to install packages. Use `uv add <package>` instead.

## Running Python

Always run Python scripts with `uv run python3` instead of calling `python3` directly.

## Git commands

When running git in a specific directory, use `git -C <dir> <args>` instead of `cd <dir> && git <args>`.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`dskard/ragplay`), managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical label strings (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
