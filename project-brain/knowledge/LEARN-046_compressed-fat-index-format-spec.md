# LEARN-046 — Compressed Fat Index Format Specification
<!-- type: LEARN -->
<!-- tags: fat-index, compression, token-efficiency, format-spec, INDEX-MASTER, architecture -->
<!-- created: 2026-02-19 -->
<!-- status: ACTIVE -->
<!-- backlinks: SPEC-000, LEARN-044, LEARN-030 -->

## What This Is
A token-optimized fat index format that achieves ~70% token reduction over the original markdown format while preserving all information. Designed for LLM-only consumption — human readability is not a constraint (any LLM can reverse-render to pretty markdown on demand).

## Format Specification

### Entry Format
```
ID|tags|→outlinks|←inlinks|summary|d:decisions|i:interface|!issues
```

### Field Rules
- **ID**: Abbreviated — `L001`=LEARN-001, `S000`=SPEC-000, `C001`=CODE-001, `R001`=RULE-001, `G001`=LOG-001
- **tags**: Comma-separated, no spaces after commas
- **→**: Forward links (outbound). Use abbreviated IDs. `∅` if none.
- **←**: Backlinks (inbound). Use abbreviated IDs. `∅` if none. Hub indicators: `(37←hub)` for high-inbound files.
- **summary**: Dense natural language. Use symbols: `≠` (not equal), `→` (leads to/becomes), `>` (greater than), `+` (and), `~` (approximately). No markdown formatting.
- **d:**: Key decisions. Omit field entirely if none (research-only files).
- **i:**: Interface/contract. Omit if N/A (most LEARNs).
- **!**: Known issues/open items. Always include — tells LLM whether file has answers or gaps.

### Structural Sections
Non-entry sections (Open Questions, Tensions, Clusters) use pipe-delimited tables with abbreviated headers.

### Sub-Index Reference Format
```
@SUB:name|file|member-count|member-IDs|summary
```

### Retired File Format
```
~ID|retired-date|reason
```

### Derivable Fields (omitted to save tokens)
- **Type**: First letter of ID (L=LEARN, S=SPEC, etc.)
- **File path**: `{type_dir}/{ID}_{slug}.md` — derivable from ID + brain convention
- **Interface: N/A**: Default assumption — only include when interface exists

## Token Economics
- Current markdown format: ~380 tokens/entry average
- Compressed format: ~112 tokens/entry average
- **Savings: 70% per entry, 3.4x more entries per token budget**
- At 56 files: ~6.3K tokens vs ~21.3K tokens (saves ~15K)
- At 500 files: ~56K tokens vs ~190K tokens (fits in context vs doesn't)

## Reverse Rendering
Any LLM can expand compressed format back to human-readable markdown:
```
L044|architecture,RAG|→S000,L001|←∅|Brain≠RAG—context multiplier|d:invest in topology|!no empirical data
```
Becomes:
```markdown
### LEARN-044
- **Type:** LEARN
- **File:** learnings/LEARN-044_brain-as-context-multiplier-not-rag.md
- **Tags:** architecture, RAG
- **Links:** SPEC-000, LEARN-001
- **Backlinks:** _(none)_
- **Summary:** Brain is not RAG — it's a context multiplier.
- **Key decisions:** Invest in topology.
- **Known issues:** No empirical data.
```

## Migration Notes
- BM25 search (brain.py, brain-mcp-server.py) parses INDEX-MASTER for summaries — parser needs update to handle pipe-delimited format
- `/brain-deposit` skill generates fat index entries — template needs update
- `/brain-status` reads INDEX-MASTER for cluster/vitality analysis — parser needs update

## Known Issues
- brain.py and brain-mcp-server.py parsers assume markdown format — must update before switching
- Abbreviated IDs require consistent convention across all brains
- Sub-index format not yet tested at scale
