# RULE-006: uv Venv Hygiene
<!-- type: RULE -->
<!-- created: 2026-02-19 -->
<!-- tags: uv, venv, dependencies, Python, Windows, MCP, operational -->
<!-- links: LEARN-041, CODE-001, LEARN-030 -->

## Problem
uv virtual environments lose packages silently. Observed causes:
1. `.venv` recreated by `uv` when Python version or platform changes
2. Manual deletion of `.venv` (cleanup, disk space)
3. Antivirus quarantining packages (Windows Defender)
4. `uv sync` not re-run after `.venv` recreate
5. Working from wrong directory (uv resolves pyproject.toml from cwd)

Symptoms are insidious: the server/tool starts fine but specific features fail silently (especially with lazy imports inside functions).

## Rules

### 1. Verify venv after any session gap
At the start of any session that uses Python tools (brain.py, MCP server), run:
```bash
cd <project-dir> && uv run python -c "from rank_bm25 import BM25Okapi; print('deps OK')"
```
If it fails, run `uv sync` in the project directory.

### 2. Always use `uv run` not bare `python`
`uv run` ensures the correct venv is activated. Bare `python` may use the system Python or a different venv.

### 3. After `uv sync`, restart consumers
MCP servers cache their Python process. After `uv sync`, restart Claude Code (or any other MCP client) to pick up the restored packages.

### 4. Pin `uv` version in CI/automation
`uv` updates can change venv resolution behavior. Pin the version when automating.

### 5. `--directory` flag in MCP registration
When registering MCP servers, always use `uv --directory <project-dir> run` so uv finds the right pyproject.toml regardless of Claude Code's working directory.

## Diagnostic Checklist
When a Python-based tool fails or hangs:
1. Is the `.venv` present? → `ls <project-dir>/.venv/`
2. Are deps installed? → `uv --directory <project-dir> pip list | grep <package>`
3. Can the import succeed? → `uv --directory <project-dir> run python -c "import <package>"`
4. If no → `uv --directory <project-dir> sync` + restart consumers

## Known Issues
- uv does not warn when recreating a venv — packages vanish silently
- No lock file validation on `uv run` (it assumes venv is current)
