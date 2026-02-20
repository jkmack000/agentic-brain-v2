# Index Research Brain

## Identity & Purpose

This is the **Index Research Brain** — a persistent knowledge base investigating how indexes work across domains: graph databases, search engines, knowledge graphs, LLM context management, and hypertext systems. The goal is to design an optimized index format for LLM-consumed knowledge bases (the "fat index").

The brain uses a **three-space architecture** (v2):
- **identity/** — WHO: SPECs (design decisions) + RULEs (constraints)
- **knowledge/** — WHAT: LEARNs (discoveries) + CODEs (implementation docs)
- **ops/** — HOW: LOGs (timeline) + session state

@project-brain/INIT.md

## Mission

Research how indexes work — graph database indexes, search indexes, knowledge graph indexes, LLM context indexes, hypertext — and deposit findings into the project brain. Goal: design an optimized index format for LLM-consumed knowledge bases.

## Session Lifecycle

- **Start:** Check ops/SESSION-HANDOFF.md, then scan knowledge/indexes/INDEX-MASTER.md for relevant prior work
- **During:** Follow the Workflow below
- **End:** Write ops/SESSION-HANDOFF.md + append LOG-002 timeline entry

## Workflow — MANDATORY

1. **Search brain first** — Check what we already know. Never duplicate existing knowledge.
2. **Research** — Read the provided URL(s). Extract structured knowledge.
3. **Deposit** — Write a LEARN file + fat index entry for each substantive finding.
4. **Synthesize** — After every 3-5 deposits, update INDEX-MASTER with cross-links and note emerging patterns.

## Web Research Protocol

When the user gives you a URL or topic:

1. **Fetch** the URL with WebFetch. Extract: core concepts, data structures, tradeoffs, benchmarks, quotes with attribution.
2. **Assess novelty** — Search the brain for overlap. If >80% covered, skip or note as corroboration. If new, proceed.
3. **Deposit as LEARN** — One file per distinct concept (not per URL). A URL with 3 independent insights = 3 LEARN files.
4. **Tag aggressively** — Include both the source domain (e.g., `database`, `search-engine`, `knowledge-graph`) and the index property (e.g., `b-tree`, `inverted-index`, `locality`, `compression`, `token-efficiency`).
5. **Link deliberately** — Every new LEARN must link to at least 3 existing files. If you can't find 3 links, the deposit may be off-topic.

## What to Extract from Sources

For each index type or technique encountered, capture:
- **Data structure** — How it's organized (tree, hash, inverted list, graph, etc.)
- **Query model** — What questions it answers efficiently
- **Write cost** — How expensive inserts/updates are
- **Space overhead** — How much extra storage vs raw data
- **Scaling behavior** — How it degrades as N grows
- **Tradeoffs** — What it sacrifices (write speed, space, freshness, etc.)
- **Relevance to LLM context** — Does this concept translate to our fat-index problem?

## Deposit Rules

- File naming: `LEARN-NNN_descriptive-slug.md`
- Use the LEARN template from `project-brain/templates/TEMPLATE-LEARN.md`
- Source field MUST include the URL and access date
- Index entry format: compressed-v1 per LEARN-046
- Minimum 3 links per deposit (brain quorum rule from SPEC-003)

## Brain Reference

All brain files live in `project-brain/`. Three-space layout:

| Space | Contains | Directory |
|-------|----------|-----------|
| identity | SPECs + RULEs | `identity/` |
| knowledge | LEARNs + CODEs | `knowledge/` |
| ops | LOGs + sessions | `ops/` |

Other directories:
- `knowledge/indexes/` — INDEX-MASTER.md + sub-indexes
- `reset-files/` — Pre-built context packages
- `templates/` — File templates for each type

Session hygiene, fat-index discipline, and ingestion dedup are enforced via `.claude/rules/`.

## Brain Skills

- `/brain-search <query>` — Search fat indexes, return ranked results without opening files
- `/brain-deposit [TYPE] [desc]` — Guided deposit with dedup check
- `/brain-handoff` — Write SESSION-HANDOFF.md immediately
- `/brain-status` — File counts, orphans, index health

## Stop Rules

- Two failures on same approach → stop, explain, ask for direction.
- Going in circles → write SESSION-HANDOFF.md, tell the user.
- If you haven't searched the brain, you haven't started.
- If a URL is paywalled or inaccessible, report it immediately — don't guess at content.

## Scope Guard

This brain is about **indexes and indexing**. Reject tangents unless the user explicitly asks to expand scope. On-topic examples:
- B-trees, LSM trees, skip lists, inverted indexes, bitmap indexes, hypertext, zettelkasten, graph databases
- Search engine internals (Lucene, Elasticsearch, BM25, TF-IDF)
- Knowledge graph indexing (RDF, property graphs, triple stores)
- LLM context management (RAG retrieval, embedding indexes, fat indexes)
- Compression techniques for structured metadata
- Information retrieval theory (precision, recall, ranking)

Off-topic (deposit only if user explicitly requests):
- General database administration
- Specific programming language tutorials
- LLM fine-tuning or training
