# LEARN-002 — Competitive Landscape: LLM Memory & Indexing Systems (Feb 2026)
<!-- type: LEARN -->
<!-- tags: competitive-analysis, memory-systems, indexing, MCP, RAPTOR, GraphRAG, Letta, Mem0, context-engineering -->
<!-- created: 2026-02-14 -->
<!-- source: Web research Feb 2026 — arxiv papers, product blogs, GitHub repos -->
<!-- links: SPEC-000, LEARN-001, LOG-001 -->

## Discovery
Comprehensive survey of LLM memory/indexing systems reveals our Project Brain architecture independently converged with Letta's Context Repositories (Feb 2026) — git-backed, file-based, progressive disclosure. Our 44:1 compression ratio beats automated approaches (6-20x typical) because we do extraction (keep relevant) not compression (keep everything at lower fidelity).

## Key Systems Evaluated

### Tier 1: Directly Comparable
- **Letta Context Repositories (Feb 2026):** Git-backed files, agent can rewrite its own memory, progressive disclosure via folder/file names. Near-identical to SPEC-000. Validates our architecture. Gap: they auto-commit every memory change with structured messages.
- **Basic Memory (MCP-based):** Markdown files + SQLite entity graph + MCP interface. Simpler structure than ours but has native MCP integration — the LLM calls memory tools directly without CLI.
- **Mem0:** Three-stage pipeline (extract → consolidate → retrieve) with ADD/UPDATE/DELETE/NOOP operations. Their consolidation protocol formalizes what our dedup process does informally.

### Tier 2: Complementary Approaches
- **RAPTOR:** Recursive tree of summaries — leaf nodes are chunks, higher nodes are progressive abstractions. Our INDEX-MASTER + full files = a manually curated two-level RAPTOR tree. At scale (75+ files), sub-indexes create a three-level tree.
- **Microsoft GraphRAG/LazyGraphRAG:** Knowledge graph + community detection. LazyGraphRAG defers LLM summarization to query time (0.1% of GraphRAG's indexing cost). Relevant for automated `brain ingest` paid tier.
- **Zep/Graphiti:** Temporal knowledge graph — tracks when facts were true and how they change. Our gap: no temporal provenance on individual facts.

### Tier 3: Validated Concepts
- **ACE (Agentic Context Engineering):** Generator/Reflector/Curator pattern prevents "context collapse" where iterative rewriting erodes detail. Validates our append-then-consolidate approach.
- **LLMLingua:** Token-level compression (drop unimportant tokens). Orthogonal to our approach, marginal gains on already-dense fat index entries.
- **"Lost in the Middle" research (MIT 2025):** LLMs degrade 15-47% on info in the middle of context. Critical info should go at TOP and BOTTOM of loaded context.

## Top 10 Actionable Improvements (Ranked by Impact/Effort)

### Must-Do
1. **MCP Server wrapper for brain.py** — Entire ecosystem converging on MCP. Let the LLM call brain_search/deposit as native tools. Eliminates manual CLI workflow. (HIGH impact, MEDIUM effort)
2. **Formalize consolidation as ADD/UPDATE/DELETE/NOOP** — From Mem0. Replaces vague "scan and compare" with repeatable decision framework. (HIGH impact, LOW effort)
3. **Git-commit every deposit** — From Letta. Structured messages like `[ADD] LEARN-008: description`. Rollback + audit trail. (MEDIUM impact, LOW effort)

### Should-Do
4. **Position-aware context loading** — From MIT research. Restructure RESET/INDEX templates: critical info at TOP and BOTTOM, supporting context in MIDDLE. (MEDIUM impact, LOW effort)
5. **Revision history metadata** — From Zep. Add `<!-- revised: -->` and `<!-- revision-note: -->` to templates. Zero-infrastructure temporal provenance. (LOW-MEDIUM impact, LOW effort)
6. **Link-chain traversal in brain search** — Follow the Links: field N hops deep. Graph-like navigation without a graph database. (MEDIUM impact, MEDIUM effort)

### Nice-to-Have
7. **Three-level hierarchy for sub-indexes** — From RAPTOR. Add theme summary atop each sub-index when implementing the 75-file threshold. (MEDIUM impact, LOW effort)
8. **Lazy ingestion for paid tier** — From LazyGraphRAG. Draft entries with quick NLP extraction, LLM refinement on-demand when queried. (MEDIUM impact, HIGHER effort)
9. **Consolidation session template** — From ACE's Curator role. Formal RESET-CONSOLIDATION.md for the periodic cleanup pass. (LOW-MEDIUM impact, LOW effort)
10. **LLM can propose edits to existing files** — From Letta. Currently append-only; allowing updates (with human review) prevents knowledge fragmentation. (MEDIUM impact, LOW effort)

## Our Competitive Advantages
- **Zero infrastructure** — no vector DB, embeddings, graph store, or API calls for retrieval
- **44:1 compression ratio** — extraction beats compression (6-20x automated typical)
- **Human-auditable** — markdown files, not opaque embeddings
- **Session handoff pattern** — more explicit than most programmatic approaches
- **Obsidian-compatible** — any markdown editor works
- **Portable** — works with any LLM that can read files

## Our Gaps
- No MCP integration (biggest gap — #1 priority)
- No automated ingestion pipeline yet
- No temporal provenance on facts
- No graph traversal of link relationships
- Consolidation process not formalized

## Impact
- **Validates SPEC-000 architecture** — Letta's independent convergence is strong signal
- **MCP wrapper is the #1 priority** for the brain system itself (after Donchian bot proves the concept)
- **Brain Hub (LOG-001) validated** — MemOS and OpenMemory show market demand for cross-project knowledge sharing
- **LEARN-001 compression findings confirmed** — automated approaches get 6-20x, our manual extraction gets 44x

## Action Taken
Documented. Top 3 improvements (MCP wrapper, consolidation protocol, git-commit workflow) flagged for implementation after Donchian bot MVP proves the core concept.
