# CODE-001 — Brain MCP Server Implementation
<!-- type: CODE -->
<!-- tags: MCP, server, brain-search, tools, resources, prompts, stdio, BM25, implementation -->
<!-- created: 2026-02-17 -->
<!-- links: LEARN-013, LEARN-028, LEARN-030, LEARN-040, SPEC-000 -->

## Purpose
MCP server that exposes the Project Brain to Claude Code via tools, resources, and prompts. Transforms brain access from "load files into context" to "query knowledge on demand" — the highest-leverage memory improvement identified in LEARN-040.

## Architecture

### Transport: stdio
- Python server registered via `claude mcp add --scope user brain -- uv run brain-mcp-server.py`
- Scope `user` = available in all projects (brain is cross-project)
- No HTTP needed — local-only, single-user

### Dependencies
- `mcp[cli]>=1.26.0` — official MCP Python SDK (FastMCP)
- `rank-bm25>=0.2.2` — already in brain.py
- No additional deps

### Tools (3 tools — LLM-callable)

| Tool | Purpose | Token Budget |
|------|---------|-------------|
| `search_brain` | BM25 search over fat indexes, returns ranked results | ~2K max |
| `read_file` | Read a specific brain file by ID, with optional section filter | ~8K max |
| `get_index` | Return full INDEX-MASTER fat index for orientation | ~5K max |

### Resources (URI-based, @-mentionable)

| Resource | URI Pattern | Returns |
|----------|------------|---------|
| Master index | `brain://index` | Full INDEX-MASTER.md |
| Brain file by ID | `brain://file/{file_id}` | Full file content |
| Handoff | `brain://handoff` | SESSION-HANDOFF.md |

### Prompts (slash commands)

| Prompt | Invocation | Action |
|--------|-----------|--------|
| search | `/mcp__brain__search <query>` | Search and format results |
| status | `/mcp__brain__status` | File counts + index health |

## Implementation

### File: `project-brain/brain-mcp-server.py`

```python
"""
Brain MCP Server — Exposes Project Brain to Claude Code via MCP protocol.

Register: claude mcp add --scope user brain -- uv run brain-mcp-server.py
Test:     uv run mcp dev brain-mcp-server.py

Tools:
  search_brain(query, limit) — BM25 search over fat indexes
  read_file(file_id, section) — Read a brain file by ID
  get_index()                 — Return INDEX-MASTER for orientation

Resources:
  @brain:brain://index          — Master index
  @brain:brain://file/{file_id} — Any brain file by ID
  @brain:brain://handoff        — Latest session handoff

Prompts:
  /mcp__brain__search <query>   — Search and format results
  /mcp__brain__status           — Brain health overview
"""

import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("brain-mcp")

mcp = FastMCP(
    "brain",
    instructions=(
        "Project Brain memory server. Use search_brain to find relevant "
        "knowledge before opening files. Use read_file to load specific "
        "brain files by ID (e.g., 'LEARN-013'). Use get_index for full "
        "brain orientation. Prefer search over read — it saves tokens."
    ),
)

# Import brain.py functions — co-located in same directory
# We import these at module level so the server starts fast
sys.path.insert(0, str(Path(__file__).parent))
from brain import (
    find_brain_root,
    collect_all_entries,
    score_entries_bm25,
    read_file as brain_read_file,
    parse_index_entries,
    estimate_tokens,
    FILE_TYPES,
    INDEX_MASTER,
)


def _get_brain_root() -> Path:
    """Find brain root, raising clear error if not found."""
    root = find_brain_root(Path(__file__).parent)
    if root is None:
        root = find_brain_root()
    if root is None:
        raise FileNotFoundError(
            "No project-brain/ directory found. "
            "Run `brain init` to create one."
        )
    return root


def _resolve_file_id(brain_root: Path, file_id: str) -> Path | None:
    """Resolve a file ID (e.g., 'LEARN-013') to its full path."""
    file_id_upper = file_id.upper()
    # Determine type prefix
    for type_prefix, info in FILE_TYPES.items():
        if file_id_upper.startswith(type_prefix):
            type_dir = brain_root / info["dir"]
            if type_dir.exists():
                for f in type_dir.glob(f"{type_prefix}-*.md"):
                    if f.stem.split("_")[0].upper() == file_id_upper:
                        return f
    # Also check special files
    special = {
        "INDEX-MASTER": brain_root / INDEX_MASTER,
        "SESSION-HANDOFF": brain_root / "SESSION-HANDOFF.md",
        "INIT": brain_root / "INIT.md",
    }
    if file_id_upper in special and special[file_id_upper].exists():
        return special[file_id_upper]
    return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_brain(query: str, limit: int = 10) -> str:
    """Search the Project Brain using BM25 ranking with structural boosts.

    Returns ranked results with file IDs, scores, tags, and summary excerpts.
    Use this FIRST before reading any brain file — it finds what's relevant
    without loading full files into context.

    Args:
        query: Search terms (e.g., "hooks configuration", "MCP server")
        limit: Maximum number of results to return (default 10)
    """
    brain_root = _get_brain_root()
    entries = collect_all_entries(brain_root)

    if not entries:
        return "No brain files found. The brain is empty."

    query_terms = [t.strip() for t in query.split() if t.strip()]
    scored = score_entries_bm25(entries, query_terms)

    if not scored:
        return f'No results for "{query}" across {len(entries)} brain files.'

    results = scored[:limit]
    lines = [f'Search: "{query}" — {len(results)} of {len(scored)} matches\n']

    for rank, (score, entry) in enumerate(results, 1):
        summary = entry.get("summary", "No summary")
        if len(summary) > 200:
            summary = summary[:197] + "..."
        tags = entry.get("tags", "")
        lines.append(
            f"{rank}. **{entry['id']}** (score: {score:.1f})\n"
            f"   Tags: {tags}\n"
            f"   {summary}\n"
        )

    lines.append(
        f"\nUse read_file(file_id) to load the full content of any result."
    )
    return "\n".join(lines)


@mcp.tool()
def read_file(file_id: str, section: str = "") -> str:
    """Read a specific brain file by its ID.

    Returns the full markdown content of the file. Optionally filter to a
    specific section by heading name.

    Args:
        file_id: Brain file ID (e.g., "LEARN-013", "SPEC-001", "RULE-002")
        section: Optional section heading to extract (e.g., "Key Details")
    """
    brain_root = _get_brain_root()
    path = _resolve_file_id(brain_root, file_id)

    if path is None:
        return f"File not found: {file_id}. Use search_brain to find valid IDs."

    content = brain_read_file(path)
    tokens = estimate_tokens(content)

    if section:
        # Extract just the requested section
        import re
        pattern = rf"^(#{1,3}\s+{re.escape(section)}.*?)(?=^#{1,3}\s|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            tokens = estimate_tokens(content)
        else:
            content = (
                f"Section '{section}' not found in {file_id}.\n"
                f"Available sections: "
                + ", ".join(
                    re.findall(r"^#{1,3}\s+(.+)", content, re.MULTILINE)
                )
            )

    header = f"# {file_id} (~{tokens} tokens)\n---\n"
    return header + content


@mcp.tool()
def get_index() -> str:
    """Return the full INDEX-MASTER fat index for brain orientation.

    Load this at session start to understand what knowledge is available.
    Each entry summarizes a brain file — scan summaries to decide which
    files to read in full via read_file().
    """
    brain_root = _get_brain_root()
    master_path = brain_root / INDEX_MASTER
    if not master_path.exists():
        return "INDEX-MASTER.md not found."

    content = brain_read_file(master_path)
    tokens = estimate_tokens(content)
    return f"# INDEX-MASTER (~{tokens} tokens)\n---\n{content}"


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("brain://index")
def resource_index() -> str:
    """The full INDEX-MASTER fat index — brain orientation map."""
    brain_root = _get_brain_root()
    return brain_read_file(brain_root / INDEX_MASTER)


@mcp.resource("brain://file/{file_id}")
def resource_file(file_id: str) -> str:
    """Read any brain file by ID (e.g., LEARN-013, SPEC-001)."""
    brain_root = _get_brain_root()
    path = _resolve_file_id(brain_root, file_id)
    if path is None:
        return f"File not found: {file_id}"
    return brain_read_file(path)


@mcp.resource("brain://handoff")
def resource_handoff() -> str:
    """The latest SESSION-HANDOFF — previous session state."""
    brain_root = _get_brain_root()
    handoff = brain_root / "SESSION-HANDOFF.md"
    if handoff.exists():
        return brain_read_file(handoff)
    return "No SESSION-HANDOFF.md found — this may be a fresh brain."


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@mcp.prompt()
def search(query: str) -> str:
    """Search the brain and format results for review."""
    return (
        f"Use the search_brain tool with query '{query}', then summarize "
        f"the top results and recommend which files to read in full."
    )


@mcp.prompt()
def status() -> str:
    """Show brain health overview."""
    return (
        "Use get_index to load the brain index, then report: "
        "total file count, files by type, any open questions or tensions "
        "from the index, and the date of last update."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Registration

```bash
# One-time setup (user scope = all projects)
claude mcp add --scope user brain -- uv --directory C:\agentic-brain\project-brain run brain-mcp-server.py
```

After registration, Claude Code sessions get:
- Tools: `mcp__brain__search_brain`, `mcp__brain__read_file`, `mcp__brain__get_index`
- Resources: `@brain:brain://index`, `@brain:brain://file/LEARN-013`, `@brain:brain://handoff`
- Prompts: `/mcp__brain__search`, `/mcp__brain__status`

## Token Budget Design
- `search_brain`: Returns ~100-200 tokens per result × 10 max = ~2K tokens
- `read_file`: Individual LEARN files are 500-2000 tokens. Hard ceiling at ~8K (warn above 10K per LEARN-013)
- `get_index`: INDEX-MASTER is ~8K tokens currently. Will grow. Monitor.
- Total per-query cost: search (~2K) + 1-2 file reads (~2-4K) = **~4-6K tokens** vs loading all files (~100K+)

## Design Decisions
1. **Reuse brain.py** — import existing BM25 search, file parsing, token estimation. No duplication.
2. **stdio transport** — simplest, no HTTP server needed, Python avoids the Windows `cmd /c` wrapper problem
3. **User scope** — brain is useful across all projects. Register once globally.
4. **Three tools, not more** — LLM tool descriptions consume context. Keep lean. Tool Search activates at 10% context.
5. **Section filtering** — `read_file` supports extracting a single heading section to further reduce token cost
6. **Resources mirror tools** — resources for @-mention convenience, tools for LLM-initiated access. Same data, different access pattern.

## Testing
```bash
# Interactive inspector
uv run mcp dev brain-mcp-server.py

# Verify registration
claude mcp list

# Test in Claude Code
# The LLM should be able to call search_brain("hooks") and get ranked results
```

## Future Enhancements
- **Excerpt mode**: Return only relevant paragraphs from files (not whole files) — requires semantic chunking
- **Write tools**: `deposit_learning`, `update_handoff` — currently read-only for safety
- **Sub-index awareness**: Search specific sub-indexes when specified
- **list_changed notifications**: Emit when brain files change during session
- **Vector search**: Add embedding-based search alongside BM25 (LEARN-030 Phase 3)

## Open Issues
- brain.py imports `rank_bm25` lazily — MCP server needs it at startup or first search call
- Large INDEX-MASTER (~8K tokens) may trigger Tool Search context threshold warnings
- Resources with template parameters (`brain://file/{file_id}`) — verify Claude Code renders these in autocomplete
