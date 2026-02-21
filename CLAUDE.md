# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

**Index Research Brain** — persistent knowledge base investigating how indexes work across domains (graph DBs, search engines, knowledge graphs, LLM context). Goal: design an optimized index format for LLM-consumed knowledge bases (the "fat index").

@project-brain/INIT.md

## Architecture

All brain files live in `project-brain/` with three spaces: `identity/` (SPECs + RULEs), `knowledge/` (LEARNs + CODEs), `ops/` (LOGs + session state). Fat indexes in `knowledge/indexes/INDEX-MASTER.md`.

Two Python tools in `project-brain/`: `brain.py` (CLI) and `brain-mcp-server.py` (MCP server via FastMCP, imports from brain.py). Dependencies managed with `uv` in `project-brain/`'s own venv. Key deps: `rank_bm25`, `mcp[cli]`.

## Commands

```bash
uv run project-brain/brain.py search "query"
uv run project-brain/brain.py status
uv run project-brain/brain.py validate all
uv run project-brain/brain.py reindex
```

## Workflow — MANDATORY

1. **Search brain first** — never duplicate existing knowledge.
2. **Research** — read URLs, extract structured knowledge.
3. **Deposit** — write a LEARN file + fat index entry per finding.
4. **Synthesize** — after every 3-5 deposits, update INDEX-MASTER with cross-links.

Deposit/research protocol details are in `.claude/rules/brain.md`.

## Verify Before Claiming Done

Never claim something is complete, working, or fixed without a smoke test. Run the code, check the output, confirm the result. If you can't verify it (e.g., requires a session restart), say so explicitly. "It should work" is not verification.

## Stop Rules

- Two failures on same approach → stop, explain, ask for direction.
- Going in circles → write SESSION-HANDOFF.md, tell the user.
- If you haven't searched the brain, you haven't started.
- If a URL is paywalled/inaccessible, report immediately — don't guess.

## Scope Guard

This brain is about **indexes and indexing**. Reject tangents unless the user explicitly asks to expand scope.
