# LEARN-041: MCP Server Development Gotchas
<!-- type: LEARN -->
<!-- created: 2026-02-18 -->
<!-- updated: 2026-02-19 -->
<!-- tags: MCP, FastMCP, stdio, development, gotchas, regex, registration, claude-code -->
<!-- links: CODE-001, LEARN-013, LEARN-019 -->

## Context
Discovered during development and registration of the Brain MCP Server (CODE-001). Eight practical gotchas (with sub-gotchas 2a and 6a) that affect anyone building MCP servers for Claude Code.

## Discoveries

### 1. MCP SDK Version & FastMCP Location
- **MCP SDK v1.26.0** is current as of Feb 2026
- **FastMCP is part of the official `mcp` package** — import as `from mcp.server.fastmcp import FastMCP`
- No separate `fastmcp` package needed; the official SDK includes it

### 2. stdio Servers Must Never Print to stdout
- stdio MCP transport uses stdout for JSON-RPC communication
- **Any `print()` call to stdout corrupts the JSON-RPC stream** and breaks the server silently
- Symptoms: server appears to start but tools never appear, or tools return garbage
- Fix: use `logging` module (writes to stderr by default) or explicitly `print(..., file=sys.stderr)`
- This applies to ALL stdio MCP servers, not just Python
- **2a. Module-level stdout wrapping in imported libraries breaks MCP stdio.** If your MCP server imports a library that does `sys.stdout = io.TextIOWrapper(...)` at module level (e.g., to force UTF-8 on Windows where stdout defaults to cp1252), it replaces FastMCP's JSON-RPC pipe. The server starts, some tools may work (simpler responses fit buffers), but larger responses deadlock indefinitely. Fix: guard stdout wrapping with `if __name__ == "__main__"` so it only runs in CLI mode, not on import.

### 3. FastMCP `instructions` Field Enables Tool Search Discovery
- The `instructions` parameter in `FastMCP(name=..., instructions=...)` is critical for **Tool Search discoverability**
- Claude Code's Tool Search feature (activates at ~10% context usage) uses these instructions to decide when to surface MCP tools
- Without a clear `instructions` field, your MCP tools may never be auto-activated by Tool Search
- Write instructions that describe WHEN the tools should be used, not just what they do

### 4. `claude mcp add` Cannot Run Inside a Claude Code Session
- Running `claude mcp add` from within a Claude Code Bash tool fails — it attempts to start a nested Claude session which is blocked
- **Must be run from a normal terminal** (PowerShell, cmd, bash) outside of Claude Code
- The command modifies `~/.claude/settings.json` (user scope) or `.claude/settings.local.json` (project scope)
- Workaround: manually edit the settings JSON file directly from within Claude Code

### 5. Regex DOTALL+MULTILINE Unreliable for Markdown Section Extraction
- Python `re.DOTALL | re.MULTILINE` regex patterns for extracting markdown sections (between `## headings`) are fragile
- Edge cases: empty sections, last section (no following heading), headings inside code blocks, inconsistent heading levels
- **Robust alternative: line-by-line heading parser** — iterate lines, detect heading boundaries, collect content between them
- Pattern: accumulate lines into current section buffer, flush when next heading encountered
- This applies broadly to any markdown processing, not just MCP servers

### 6. Missing Dependencies = Silent Server Death
- If the MCP server's Python dependencies aren't installed in its venv, the server **dies silently on startup**
- Claude Code does NOT surface MCP server startup errors — tools simply don't appear
- Root cause in our case: `mcp[cli]>=1.26.0` was in `pyproject.toml` but `uv sync` had never been run after adding it
- **Diagnosis:** Check `.venv/Lib/site-packages/` for the expected package dist-info
- **Fix:** Run `uv --directory <project-dir> sync` from a normal terminal, then restart Claude Code
- This is the most common "tools don't appear" failure — check dependencies first
- **6a. Lazy imports turn missing deps into per-tool hangs, not startup failures.** If a dependency is imported inside a tool function (e.g., `from rank_bm25 import BM25Okapi` inside `search_brain`) rather than at module level, the server starts fine and other tools work — but the tool using the missing dep hangs indefinitely instead of returning an error. FastMCP's stdio transport swallows the `ModuleNotFoundError`. This is especially insidious because the venv may have been valid previously — `uv sync` can lose packages if the `.venv` is recreated. Symptoms: one specific tool hangs (0 tokens consumed) while others work fine.

### 7. `claude mcp add` Registration ≠ Server Functional
- `claude mcp add` succeeding (or saying "already exists") only means the registration entry is stored
- It does NOT validate that the server can actually start or that its dependencies are installed
- Always verify end-to-end: registration exists AND server starts AND tools appear in session

### 8. `claude mcp add --scope user` Config Location is Opaque
- User-scope MCP registrations are NOT stored in `~/.claude/settings.json` or `~/.claude/.mcp.json`
- The actual storage location is internal to Claude Code (possibly in a SQLite DB or internal config)
- Project-scope registrations go to `.mcp.json` in the project root
- If you need to inspect/edit user-scope registrations, `claude mcp list` from a normal terminal is the only reliable method

## Key Takeaway
MCP server development has a steep "last mile" — the protocol is well-documented but stdio transport, Tool Search integration, dependency management, and registration workflow have undocumented gotchas that cost hours to diagnose. **Check dependencies first** when tools don't appear.

## Known Issues
- None of these are bugs to report — they're design constraints requiring awareness
- Gotcha #2 (stdout corruption) and #6 (silent dependency failure) are the most dangerous — both completely silent failure modes
