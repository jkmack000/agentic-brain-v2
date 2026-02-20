# LEARN-050 — Ars Contexta: Agent-Native Knowledge Management Architecture
<!-- type: LEARN -->
<!-- tags: knowledge-management,architecture,pipeline,zettelkasten,MOC,subagents,hooks,schema-validation,derivation,claude-code,plugin,processing-pipeline,backward-pass -->
<!-- created: 2026-02-20 -->
<!-- source: https://github.com/agenticnotetaking/arscontexta (v0.8.0, MIT). Accessed 2026-02-20. -->
<!-- links: L031, L024, L034, L009, R001, L023, S000 -->

## Discovery
Ars Contexta is a Claude Code plugin that generates personalized KM systems through conversation rather than templates. Three novel architectural patterns: (1) invariant three-space separation (self/notes/ops), (2) a 6-phase processing pipeline extending Cornell's 5 Rs with a backward-pass "Reweave" phase, and (3) a derivation engine that reasons from 249 research-backed claims to generate domain-specific architectures. Every primitive traces to cognitive science grounding.

## Context
Reviewing agent-native KM tools for indexing research. Ars Contexta represents the most architecturally opinionated Claude Code KM plugin found so far — it doesn't just store notes, it generates an entire processing pipeline with hooks, skills, subagents, and schema enforcement.

## Evidence

### Three-Space Architecture (Invariant)
All generated systems enforce this separation:

| Space | Purpose | Growth | Brain Equivalent |
|-------|---------|--------|-----------------|
| `self/` | Agent identity, methodology, goals | Slow (tens of files) | CLAUDE.md + .claude/rules/ (implicit, not separated) |
| `notes/` | Knowledge graph (primary content) | Steady (10-50/week) | project-brain/learnings/ + specs/ etc. |
| `ops/` | Operational state, queue, sessions | Fluctuating | SESSION-HANDOFF.md + logs/ (implicit, not separated) |

Space names adapt to domain (notes/ → reflections/, claims/, decisions/) but the three-way separation is invariant. **Key insight**: our brain merges self/ and ops/ into the notes space. Explicit separation could reduce noise in search results — identity files don't need to compete with knowledge files in BM25 ranking.

### 6 Rs Processing Pipeline
Extends Cornell Note-Taking's 5 Rs with meta-cognitive layer:

1. **Record** — Zero-friction capture into inbox (manual)
2. **Reduce** — Extract insights from raw captures into domain-native categories (/reduce)
3. **Reflect** — Find connections, update MOCs (/reflect)
4. **Reweave** — Backward pass: update OLDER notes with context from NEW notes (/reweave)
5. **Verify** — Schema validation + health checks (/verify)
6. **Rethink** — Meta-analysis challenging system assumptions (/rethink)

**Reweave is the novel phase.** Standard KM links new→old but rarely updates old notes when new information arrives. Our brain has no explicit backward-update step — when depositing LEARN-049, we didn't go back to update L044 or L030 with the new hypertext indexing connections. Reweave formalizes this as a pipeline stage.

### Fresh Context Per Phase
Each pipeline phase spawns a fresh subagent:
```
/ralph 5
  |-- Read queue, find next unblocked task
  |-- Spawn subagent (fresh context)
  |   +-- Runs skill, updates task, returns handoff
  |-- Parse handoff, capture learnings
  |-- Advance phase in queue
  +-- Repeat for 5 tasks
```
Rationale: prevents LLM attention degradation across phases. Each subagent gets clean context with only the relevant instructions. Validates our L009 finding (subagent context isolation) and L024 (Anthropic's 10-20x compression from sub-agents). Ars Contexta applies this as a deliberate pipeline design pattern rather than ad-hoc delegation.

### Schema Enforcement on Writes
- Note templates contain `_schema` blocks defining required fields
- PostToolUse hook on Write tool validates every note against its schema
- Schema is single source of truth — templates are derived from schema, not vice versa
- Our R001 documents hook patterns but we don't enforce note structure via hooks

### Derivation Engine (Not Templates)
Setup is a 6-phase conversational process:
1. Detection — environment analysis
2. Understanding — 2-4 turns about user's domain
3. Derivation — maps signals to 8 configuration dimensions with confidence scoring
4. Proposal — shows what will be generated in user's vocabulary
5. Generation — produces files, folders, templates, skills, hooks, manual
6. Validation — checks 15 kernel primitives, runs smoke test

Every architectural choice traces to one of 249 research claims spanning zettelkasten, Cornell notes, extended mind theory, spreading activation, small-world topology, and agent architecture. Claims are queryable: `/arscontexta:ask "Why does my system use atomic notes?"`.

### 15 Kernel Primitives
Defined in kernel.yaml — every system must include:
- MOC hierarchy structure
- Description fields (progressive disclosure)
- Wiki link connections (spreading activation)
- Schema validation blocks
- Template definitions
- Context files
- Plus 9 others (not enumerated in README)

### QMD Integration
Optional semantic search via QMD (L023) — validates our assessment that QMD is a natural fit for markdown-based KM. System works without it using ripgrep + MOC traversal as fallback.

## Impact

### Patterns to Consider Adopting
1. **Reweave/backward pass**: Formalize updating old files when new knowledge arrives. Currently ad-hoc — we sometimes update INDEX-MASTER backlinks but don't systematically revisit old LEARNs. Could be a /brain-reweave skill.
2. **Three-space separation**: Separating identity (CLAUDE.md, rules) from knowledge (LEARNs, SPECs) from operations (SESSION-HANDOFF, logs) in the search index could improve BM25 precision by filtering space before searching.
3. **Schema enforcement via hooks**: PostToolUse hook validating brain file structure on write would catch malformed deposits before they enter the system.

### Patterns We Already Have (Corroboration)
- MOC hierarchy = INDEX-MASTER + sub-indexes (L031)
- Session capture = SESSION-HANDOFF.md (L034)
- Subagent isolation = L009, L024
- Hook automation = R001
- Progressive disclosure = L044
- Research-grounded architecture = L032 (quorum sensing from biology)

### Architectural Difference
Ars Contexta generates per-user systems (derivation engine customizes everything). Our brain is a single hand-crafted architecture. Their approach scales to more users; ours is deeper for one project. The 249-claim research base is impressive but unverifiable without reading the methodology/ directory.

## Action Taken
Deposited as LEARN-050. Three actionable patterns flagged: backward-pass reweave, three-space separation for search, schema enforcement via hooks.
