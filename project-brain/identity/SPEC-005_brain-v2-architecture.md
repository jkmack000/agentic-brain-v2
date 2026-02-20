# SPEC-005 — Brain v2 Architecture
<!-- type: SPEC -->
<!-- tags: architecture,brain-v2,three-space,link-index,pipeline,reweave,schema-enforcement,search,hypertext,knowledge-management,migration -->
<!-- created: 2026-02-20 -->
<!-- source: Synthesis of 63+ brain files. Key inputs: S000 (current arch), L048/L049 (hypertext indexing), L050 (Ars Contexta), L051 (transformer attention as indexing), L031 (zettelkasten), L032/S003 (quorum sensing), L030 (BM25), L040 (memory strategies), L034 (capture gap), L033 (topology), L044 (context multiplier), C001 (MCP server), R005 (user prime directive). -->
<!-- links: S000, L048, L049, L050, L051, L031, L032, S003, L033, L030, L040, L034, L044, C001, R005, L046, L024, L009, L023, R001 -->

## Problem Statement

The current brain (S000) works but has six known friction points:

1. **Search is link-blind** — BM25 finds keywords within files (L048's case i) but can't answer "what files about X link to files about Y?" (cases ii/iii from L049)
2. **No backward pass** — depositing new files doesn't update older files that should reference the new knowledge (L050's Reweave insight)
3. **Hub concentration** — S000 has 33 backlinks, L002 has 12. Search and navigation over-depend on hubs (L033). Analogous to the γ² problem in hypertext indexing (L049)
4. **Mixed spaces** — identity (CLAUDE.md, rules), knowledge (LEARNs, SPECs), and operations (SESSION-HANDOFF, logs) compete in the same search index (L050's three-space insight)
5. **Manual deposit bottleneck** — ~4 items go undeposited per session (L034)
6. **INDEX-MASTER is monolithic** — approaching token limits, only one sub-index exists (S003)

### Core Insight

We've been building a **document store with an index** when the research says we should be building a **hypertext with a search engine**. The link index and multi-hop search are what turn a collection of files into a navigable knowledge graph.

## Design Principles

| Principle | Source | Current | v2 |
|-----------|--------|---------|-----|
| Topological > temporal decay | L032 | Implemented (vitality scoring) | Keep |
| Fat index > thin index | S000, L046 | Implemented (compressed-v1) | Keep + layer |
| Organized+trackable+provable > tokens | R005 | Guiding rule | Keep |
| Search is access pattern, not storage | L040 | Partially (MCP server) | Full multi-layer |
| Prefix-free nodes = best search | L049 | Accidentally true (distinct summaries) | Enforce explicitly |
| Three-space separation | L050 | Not implemented | Adopt |
| Backward pass as pipeline stage | L050 | Not implemented | Adopt |
| Fresh context per phase | L050, L024 | Ad hoc (subagents) | Formalize |
| Schema enforcement on writes | L050, R001 | Not implemented | Adopt |
| Fat index = hard attention pre-filter (n² → n·log n) | L051 | Implicit | Make explicit — quantify per-layer token budgets |
| Load order = attention priority (U-shaped curve) | L051 | Not considered | Adopt — return results by relevance, not ID order |

## Architecture

### Three Spaces

```
project-brain/
├── identity/                    # SLOW growth (tens of files)
│   ├── SPEC-*.md               # Architecture decisions
│   ├── RULE-*.md               # Constraints and patterns
│   └── IDENTITY.md             # Agent self-model (new)
│
├── knowledge/                   # STEADY growth (the graph)
│   ├── LEARN-*.md              # Discoveries
│   ├── CODE-*.md               # Implementation docs
│   └── indexes/                # Sub-indexes by cluster
│       ├── INDEX-MASTER.md     # Root fat index (knowledge only)
│       └── INDEX-*.md          # Cluster sub-indexes
│
├── ops/                         # FLUCTUATING (operational state)
│   ├── SESSION-HANDOFF.md      # Current session state
│   ├── LOG-*.md                # Timeline, decisions
│   ├── QUEUE.md                # Pending deposits, reweaves
│   └── sessions/               # Session archives
│
└── templates/                   # STATIC
```

**Why this matters for search**: When you search for "BM25 ranking algorithms," you don't want SESSION-HANDOFF or RULE-004 (hook safety) polluting results. Space-scoped search: `search_brain(query, space="knowledge")` filters before ranking. Identity files are loaded by rules/CLAUDE.md, not searched. Ops files are only relevant at session boundaries.

**Space assignment rules**:
- SPECs and RULEs → identity/ (they define what the brain IS, not what it knows)
- LEARNs and CODEs → knowledge/ (they are the knowledge graph)
- LOGs and SESSION-HANDOFF → ops/ (they are transient operational state)
- INDEX-MASTER → knowledge/indexes/ (it indexes the knowledge graph)
- Templates → templates/ (static, rarely changes)

### Index Architecture: Three Layers (Cascading Pre-Filter)

Inspired by the hypertext index's dual forward/reverse design (L048), our fat index format (L046), and the transformer attention analysis (L051).

**Core framing (L051):** Self-attention costs O(n²) over all tokens in context. Every token loaded but not needed wastes quadratic compute. The three index layers form a **cascading pre-filter** — each layer narrows what gets loaded, reducing n before the n² cost kicks in. Naive loading of all 65 files (~100K tokens) costs ~10¹⁰ attention ops. The cascade targets ~5-8K tokens loaded = ~10⁷ ops, a **~400x reduction**.

**Token budget per layer:**

| Layer | Purpose | Budget | Cumulative |
|-------|---------|--------|------------|
| Cluster index | Narrow to relevant cluster | ~500 tok | ~500 tok |
| Fat index | Select specific files | ~2K tok | ~2.5K tok |
| Link index | Traverse without loading intermediates | ~1K tok | ~3.5K tok |
| File read | Actual content (2-4 files) | ~2-5K tok | ~5-8.5K tok |

vs naive: ~100K+ tokens = **12-20x reduction before attention even fires.**

**Layer 1 — Fat Index (orientation layer)**
What we have now, but scoped to knowledge/ space only. Compressed-v1 format. Answers: "should I open this file?" Cost: ~3K tokens for 50 files.

**Layer 2 — Link Index (topology layer)**
New. A dedicated structure mapping edges between files. Each relationship type functions as an **attention head** (L051) — a separate index over the same knowledge graph highlighting different aspects.

```
# LINK-INDEX.md
# Format: source|target|type|hop-depth|context
L048|L049|extends|1|"L049 algorithm operates on L048's data structure"
L048|L044|validates|2|"dual indexing analogous to forward links + backlinks"
L048|S000|implements|1|"hypertext index is a type of fat index"
L031|L032|inspires|2|"zettelkasten principles led to quorum sensing framework"
```

Relationship types: `extends`, `validates`, `contradicts`, `implements`, `inspires`, `supersedes`, `corroborates`.

The `hop-depth` field encodes **topological distance from the nearest hub** (S000, L002, L005 per L033). This is positional encoding for the knowledge graph (L051) — it tells the LLM where a file sits in the topology without loading the full graph. Files at hop-depth 1 are core concepts; files at hop-depth 3+ are specialized leaves.

This enables case (ii) search from L049: "find files about X that link to files about Y" as a single indexed operation. Querying by relationship type is a first-class filter — "show me everything that `contradicts` something about compression" is a single-head attention query over the link index. The link index is the 2D range query analog — edges as queryable points.

**Layer 3 — Cluster Index (navigation layer)**
Sub-indexes auto-generated at squeeze points (S003, already implemented). V2 addition: each cluster index includes its own mini-link-index, so within-cluster traversal is fast without loading the full link index.

**INDEX-MASTER eviction policy (L051 — KV-cache analogy):** INDEX-MASTER grows linearly per deposit, analogous to KV-cache growing per token. When INDEX-MASTER exceeds its token budget (~10K tokens, per C001 warning), entries are **evicted to cluster indexes** — the master index retains only a cluster-level summary line, not per-file entries. This mirrors KV-cache eviction to slower storage and grouped-query attention (GQA) sharing one representation across a group. The compressed-v1 format (L046) is the equivalent of KV-cache quantization — reducing per-entry cost to extend capacity before eviction is needed.

### Processing Pipeline: 5 Phases

Adapting L050's 6 Rs to our context (dropping Record since we capture via /brain-deposit):

| Phase | What | Trigger | Agent | Token Cost |
|-------|------|---------|-------|------------|
| **Deposit** | Write file + fat index entry + link index entries | Manual or auto-detect | Main | ~2K |
| **Connect** | Find 3+ links, write link context with relationship type | During deposit | Main | ~1K |
| **Reweave** | Update OLD files affected by new deposit | After every 3-5 deposits | Subagent (fresh context) | ~5-10K |
| **Verify** | Schema check + orphan detection + vitality scan | After reweave | Subagent | ~3K |
| **Synthesize** | Update cluster indexes, check squeeze points, note patterns | After verify | Subagent | ~3K |

#### Reweave: The Critical Addition

When LEARN-049 is deposited about hypertext pattern matching, reweave would:
1. Read L049's outlinks (L048, S000, L044, L030, L032)
2. For each outlink, check if the target file's content should reference the new insight
3. Update target files' "Impact" or "Evidence" sections if warranted
4. Update backlink entries in the fat index and link index

This is where the hypertext index's suffix/prefix condition verification (L049) maps conceptually: does the new knowledge extend existing paths?

**Reweave scope control**: Only reweave files with direct outlinks from the new deposit (1-hop). Multi-hop reweave risks cascading changes. Budget: max 5 files updated per reweave pass.

#### Fresh Context Per Phase

Reweave, Verify, and Synthesize each spawn a subagent with clean context (L050, L024). Rationale:
- Prevents attention degradation across phases
- Each subagent loads only what it needs (e.g., Verify loads schema + file list, not full knowledge graph)
- Validated by Anthropic's 10-20x compression finding (L024) and Ars Contexta's pipeline design (L050)

### Search: Three Cases

Extending brain.py / MCP server based on the hypertext pattern matching decomposition (L048/L049):

| Case | Query Type | Example | Implementation |
|------|-----------|---------|----------------|
| **(i) Within-file** | Keyword/concept in a single file | "What do we know about BM25?" | BM25 on fat index, scoped to space (current, enhanced) |
| **(ii) Cross-link** | Concept X linked to concept Y | "What files about compression link to files about scaling?" | Link index query: filter by tag intersection across edges |
| **(iii) Cross-chain** | Multi-hop path between files | "Trace from zettelkasten theory to MCP implementation" | BFS on link index with depth limit, relevance-filtered |

MCP server extensions:
```python
# Case (i) — existing, enhanced with space scoping
# IMPORTANT: results returned in descending relevance order, not ID order.
# Highest-relevance file loads first into context (system prompt territory),
# exploiting the U-shaped attention curve (L051) — beginning and end of
# context get disproportionate attention weight, middle gets lost.
search_brain(query: str, space: str = "all", limit: int = 10)

# Case (ii) — new: single-hop link-aware search
# Relationship type is a FIRST-CLASS filter, not afterthought.
# Each relationship type = an attention head (L051) over the knowledge graph.
# "Show contradictions about compression" = single-head query.
search_linked(source_query: str, target_query: str, relationship: str = "any")
# Returns edges where source matches source_query AND target matches target_query

# Case (iii) — new: multi-hop path search
search_path(start: str, end: str, max_hops: int = 3)
# Returns shortest path(s) between two file IDs
# e.g., L031→L032→S003→C001 (zettelkasten→quorum→implementation→MCP server)
```

**Load ordering rule (L051):** All search results and RESET pack contents must be returned in **descending relevance order**. The LLM's attention follows a U-shaped curve over position — tokens at the beginning and end of context get the strongest attention, while the middle suffers "lost in the middle" degradation (L044). Loading the most important file first places it in the system prompt region where attention is strongest.

**Scaling note**: At ~65 files with avg ~3.5 outlinks (L033), the graph is sparse enough that BFS with depth limit is practical. We don't need the full orthogonal range query machinery (L048) until hundreds of files. Reassess at 100+ files (L030 roadmap).

### Schema Enforcement

PostToolUse hook on Write validates every brain file against type-specific schemas:

```yaml
# LEARN schema
required_frontmatter:
  - type: "LEARN"
  - tags: non-empty, comma-separated
  - created: ISO date (YYYY-MM-DD)
  - source: non-empty string
  - links: minimum 3 file IDs
required_sections:
  - Discovery
  - Evidence
  - Impact

# SPEC schema
required_frontmatter:
  - type: "SPEC"
  - tags: non-empty
  - created: ISO date
  - links: minimum 3 file IDs
required_sections:
  - Problem Statement
  - Architecture (or Design or Proposal)

# RULE schema
required_frontmatter:
  - type: "RULE"
  - tags: non-empty
  - created: ISO date
  - links: minimum 1 file ID (RULEs exempt from 3-link minimum per S003)
```

Implementation: PostToolUse hook on Write checks if path matches `project-brain/**/*.md`, parses frontmatter, validates against schema. Rejects write with error message if schema violated. Based on R001 hook patterns and L050's schema-as-source-of-truth approach.

### Quasi-Prefix-Free Enforcement

From L049: the strongest search results require nodes to be quasi-prefix-free — no node's summary is a substring of another's. During the Verify phase:
- Check that no two fat index summaries have >70% token overlap
- If overlap detected: either merge files (consolidation) or differentiate summaries
- This prevents the γ² degradation where similar files pollute search results
- **Attention-theoretic justification (L051):** When two fat index entries are too similar, the LLM's softmax attention **splits weight between them** instead of concentrating on one. Distinct summaries = sharper attention peaks = more decisive retrieval

### Auto-Deposit: Closing the Capture Gap

Addressing the ~4 undeposited items/session finding (L034):

**Layer 1** (exists): deposit-as-you-go rules in .claude/rules/brain.md — 7 triggers for immediate deposit.

**Layer 2** (exists): Chat log review at ~/.claude/projects/<proj>/<session>.jsonl — recovery mechanism.

**Layer 3** (new): SessionEnd hook scans conversation for undeposited knowledge:
- Decisions made? → flag for SPEC or RULE deposit
- Contradictions found? → flag for deposit + tension
- Open questions surfaced? → add to INDEX-MASTER Open Questions
- Implementation produced unexpected results? → flag for LEARN deposit
- Items flagged are written to ops/QUEUE.md for next session's attention

## What Stays the Same

| Component | Reason |
|-----------|--------|
| File types (SPEC, CODE, RULE, LEARN, LOG) | Proven, well-understood, maps to cognitive categories |
| Fat index format (compressed-v1, L046) | 70% savings proven, LLM-native |
| MCP server delivery (C001) | Highest ROI strategy (L040) |
| BM25 as primary ranker | Adequate at current scale, FTS5 next step (L030) |
| Topological vitality scoring | inbound×3 + outbound×1 + tags×0.5 (S003) |
| Session lifecycle (handoff → search → work → handoff) | Reliable, well-practiced |
| 3-link minimum (quorum rule) | Prevents orphans, enforces integration (L032/S003) |
| Sequential file numbering | Simple, collision-free, human-readable |

## Decisions

| Decision | Chosen | Over | Rationale |
|----------|--------|------|-----------|
| Three-space separation | Adopt | Keep flat | Search precision, conceptual clarity (L050) |
| Link index as separate file | Yes | Embedded in fat index | Fat index already dense; link context needs room |
| Reweave as pipeline stage | Yes | Ad hoc updates | Formalizes what we skip today; bounded (1-hop, max 5 files) |
| Schema enforcement via hook | Yes | Trust and review | Catches malformed deposits before they enter system (L050) |
| Space-scoped search | Yes | Global only | Reduces noise; identity/ops files pollute knowledge search |
| Fresh subagent per phase | Yes | Main context | Prevents attention degradation (L024, L050) |
| Relationship-typed links | Yes | Untyped links | Enables richer queries ("show contradictions", "show validations") |
| Case (iii) via BFS not range query | Yes | 2D orthogonal structure | Graph too small (<100 nodes); reassess at scale (L030, L048) |
| Relevance-ordered loading | Yes | ID-ordered | U-shaped attention curve means position matters; most relevant file goes first (L051) |
| Hop-depth in link index | Yes | Flat edges only | Positional encoding for the knowledge graph; tells LLM where file sits topologically without loading graph (L051) |
| INDEX-MASTER eviction to cluster indexes | Yes | Grow indefinitely | KV-cache analogy (L051) — evict entries to sub-indexes when master exceeds budget, keep cluster-level summaries |
| Three-layer cascade as quantified pre-filter | Yes | Informal "orientation" framing | n² attention cost makes the savings concrete: ~400x reduction from 100K→5K tokens (L051) |

## Migration Path

Incremental adoption, not rewrite. Each phase is independently committable:

| Phase | Work | Sessions | Dependency |
|-------|------|----------|------------|
| **1. Three spaces** | Create directories, move files, update all paths in INDEX-MASTER and CLAUDE.md | 1 | None |
| **2. Link index** | Build LINK-INDEX.md from existing INDEX-MASTER backlinks + outlinks, add relationship types | 1 | Phase 1 |
| **3. Schema hook** | Write PostToolUse hook, define schemas per file type, test | 1 | None (parallel with 1-2) |
| **4. /brain-reweave** | Build skill: read new deposit → identify outlinks → check targets → update → update indexes | 1 | Phase 2 |
| **5. MCP server v2** | Add search_linked() and search_path() to brain MCP server, space scoping | 2 | Phase 1-2 |
| **6. Auto-deposit hook** | SessionEnd hook scanning for undeposited knowledge → ops/QUEUE.md | 1 | Phase 1 |

**Total estimated effort**: 7 sessions, parallelizable to ~5.

## Open Questions

| # | Question | Notes |
|---|----------|-------|
| 1 | Should SPECs stay in identity/ or move to knowledge/? | SPECs define architecture (identity) but also contain knowledge about design decisions |
| 2 | Link index format: markdown table vs. compressed-v1 pipe format? | Leaning pipes — now includes hop-depth field (L051 positional encoding). Tables more readable; pipes more token-efficient + consistent with fat index |
| 3 | Reweave depth: always 1-hop, or configurable? | Deeper reweave = more thorough but higher cost and risk of cascading edits |
| 4 | Should IDENTITY.md replace or supplement CLAUDE.md? | CLAUDE.md is loaded automatically; IDENTITY.md would need explicit loading |
| 5 | Verify phase: block deposit on schema failure, or warn and proceed? | Blocking is safer but may slow fast sessions (L034 tension) |

## Risks

- **Migration churn**: Moving 60+ files across directories risks breaking existing links and INDEX-MASTER references
- **Reweave scope creep**: Backward pass could trigger cascading updates if not bounded
- **Schema rigidity**: Too-strict schemas may discourage rapid deposit (tension with L034's "deposit-as-you-go")
- **Complexity budget**: Adding link index + schema hooks + reweave + space scoping adds operational overhead. Must stay below R005's "organized+trackable" threshold without becoming burdensome
