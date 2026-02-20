# LEARN-045 — checkpoint.af vs Project Brain: State Persistence vs Knowledge Persistence
<!-- type: LEARN -->
<!-- tags: comparison, architecture, checkpoint.af, agent-state, knowledge-persistence, external-tools, Letta -->
<!-- created: 2026-02-19 -->
<!-- source: https://github.com/kianjones9/checkpoint.af -->
<!-- status: ACTIVE -->
<!-- backlinks: SPEC-000, LEARN-002, LEARN-044 -->

## What This Is
Comparison of checkpoint.af (Go CLI for snapshotting Letta AI agent state) against Project Brain (markdown-based LLM knowledge persistence). They solve different layers of the same problem: state vs knowledge.

## checkpoint.af Overview
- Go CLI + API server, v0.0.2 (early stage)
- Saves/versions/migrates snapshots of Letta AI agents as "agentfiles"
- Storage backends: local, S3, GCS, Azure, in-memory (via GoCloud abstraction)
- Rollback and migrate planned but unimplemented
- Docker deployable, uses GoReleaser
- Letta-framework-specific

## Head-to-Head Comparison

| Dimension | checkpoint.af | Project Brain |
|---|---|---|
| **What's persisted** | Agent runtime state (full snapshot blob) | Knowledge (extracted, compressed, indexed insights) |
| **Granularity** | Whole-agent snapshots — opaque blobs | Typed, granular .md files (SPEC, LEARN, RULE, etc.) |
| **Retrieval model** | By agent ID + version number | Fat-index search → load only relevant pieces |
| **Token awareness** | None — not designed around context windows | Core design constraint — every token budgeted |
| **Storage backends** | S3, GCS, Azure, local, in-memory | Local filesystem, git-tracked |
| **Framework scope** | Letta-specific | Framework-agnostic (Claude Code, Cursor, any LLM) |
| **Versioning** | Snapshot versioning with rollback/migrate | Append-only knowledge with dedup + consolidation |
| **Language** | Go | Python CLI + Markdown files |

## Key Architectural Differences

1. **State vs Knowledge** — checkpoint.af captures *what an agent IS* at a point in time. Brain captures *what was learned* across all sessions. Snapshot vs growing knowledge base.

2. **Retrieval cost** — checkpoint.af restores a full agent (all or nothing). Brain's fat indexing loads 5% of knowledge and remains effective — critical when context window is the bottleneck.

3. **Compression** — checkpoint.af stores raw state. Brain enforces extraction over storage — 40-page chapter becomes 5 files at ~6:1 compression. LLMs need distilled knowledge, not raw data.

4. **Cross-session continuity** — checkpoint.af = rollback (go back). Brain = handoff (carry forward). Undo vs build-forward philosophies.

5. **Searchability** — checkpoint.af has no search within snapshots. Brain's entire architecture is built around "find the right 3 files out of 500 without opening any."

## Complementary, Not Competitive
- **checkpoint.af** = save and restore agent runtime (like VM snapshots)
- **Project Brain** = build and query persistent knowledge (like a searchable wiki with token economics)

An ideal system could use both: checkpoint.af for agent state rollback, Brain for knowledge that's searchable and reusable across agents and sessions.

## What Brain Could Adopt
- Multi-backend storage (S3/GCS/Azure) for portability
- Docker packaging for deployment
- "Only save on diff" optimization (--only_on_diff flag)

## What checkpoint.af Could Adopt
- Fat indexing for search within snapshots
- Token-aware partial retrieval
- Knowledge extraction vs raw state storage

## Known Issues
- checkpoint.af is v0.0.2 — rollback/migrate not yet implemented, so versioning story is incomplete
- No empirical data on checkpoint.af's snapshot sizes or restore performance
