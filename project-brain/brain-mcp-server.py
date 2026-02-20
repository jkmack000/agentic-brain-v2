"""
Brain MCP Server — Exposes Project Brain to Claude Code via MCP protocol.

Register: claude mcp add --scope user brain -- uv --directory <brain-dir> run brain-mcp-server.py
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
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

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
sys.path.insert(0, str(Path(__file__).parent))
from brain import (  # noqa: E402
    find_brain_root,
    collect_all_entries,
    score_entries_bm25,
    read_file as brain_read_file,
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


def _extract_section(content: str, section_name: str) -> str | None:
    """Extract a section by heading name from markdown content.

    Returns the heading line + all content until the next heading of same
    or higher level, or None if the section is not found.
    """
    lines = content.split("\n")
    start_idx = None
    start_level = 0

    for i, line in enumerate(lines):
        heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if title.lower() == section_name.lower():
                start_idx = i
                start_level = level
                break

    if start_idx is None:
        return None

    # Collect lines until next heading of same or higher level
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        heading_match = re.match(r"^(#{1,6})\s+", lines[i])
        if heading_match and len(heading_match.group(1)) <= start_level:
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx]).strip()


def _resolve_file_id(brain_root: Path, file_id: str) -> Path | None:
    """Resolve a file ID (e.g., 'LEARN-013') to its full path."""
    file_id_upper = file_id.upper()
    for type_prefix, info in FILE_TYPES.items():
        if file_id_upper.startswith(type_prefix):
            type_dir = brain_root / info["dir"]
            if type_dir.exists():
                for f in type_dir.glob(f"{type_prefix}-*.md"):
                    if f.stem.split("_")[0].upper() == file_id_upper:
                        return f
    # Special files
    special = {
        "INDEX-MASTER": brain_root / INDEX_MASTER,
        "SESSION-HANDOFF": brain_root / "ops" / "SESSION-HANDOFF.md",
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
        "\nUse read_file(file_id) to load the full content of any result."
    )
    return "\n".join(lines)


@mcp.tool()
def read_file(file_id: str, section: str = "") -> str:
    """Read a specific brain file by its ID.

    Returns the full markdown content of the file. Optionally filter to a
    specific section by heading name to reduce token cost.

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
        extracted = _extract_section(content, section)
        if extracted is not None:
            content = extracted
            tokens = estimate_tokens(content)
        else:
            headings = re.findall(r"^#{1,3}\s+(.+)", content, re.MULTILINE)
            content = (
                f"Section '{section}' not found in {file_id}.\n"
                f"Available sections: {', '.join(headings)}"
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
    handoff = brain_root / "ops" / "SESSION-HANDOFF.md"
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
