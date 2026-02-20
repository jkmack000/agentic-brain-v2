# LEARN-023 — QMD: Local Hybrid Search Engine for Markdown Knowledge Bases
<!-- type: LEARN -->
<!-- tags: qmd, search, BM25, vector-search, reranking, hybrid-search, MCP, local-first, competitive-analysis, sqlite, node-llama-cpp -->
<!-- created: 2026-02-15 -->
<!-- source: https://github.com/tobi/qmd — full repo analysis (store.ts, qmd.ts, llm.ts, mcp.ts, collections.ts, package.json, README) -->
<!-- links: LEARN-002, LEARN-021, LEARN-013, SPEC-000 -->

## Discovery
QMD (Query Markup Documents) is a local-first CLI search engine for markdown by Tobi Lütke (Shopify founder). MIT licensed, v0.9.9, 8,259 GitHub stars (6,580 added in the last 30 days — rapid adoption). Combines BM25 full-text search, vector semantic search, and LLM re-ranking — all on-device via node-llama-cpp with GGUF models. Ships an MCP server. Directly relevant as both a competitor and a reference implementation for brain search improvements we identified in LEARN-021.

## Context
Researched as competitive intelligence after user request. Analyzed: README, store.ts (SQLite schema), qmd.ts (search pipeline), llm.ts (LLM integration), mcp.ts (MCP server), collections.ts (config), package.json. Cross-referenced against existing brain knowledge to identify what's genuinely novel vs what confirms LEARN-021 patterns.

## Evidence

### Architecture Overview

```
User Query
    │
    ├─ search    → BM25 (FTS5) only → ranked results
    ├─ vsearch   → Vector similarity only → ranked results
    └─ query     → Full hybrid pipeline:
                   ├─ Smart signal detection (skip expansion if BM25 confident)
                   ├─ Query expansion (1.7B model → lex/vec/hyde variants)
                   ├─ Parallel BM25 + vector on original + expanded queries
                   ├─ Reciprocal Rank Fusion with position bonuses
                   ├─ Top-30 → LLM reranker (0.6B model)
                   └─ Position-aware score blending → final ranked results
```

### Three Local Models (Auto-Downloaded, ~2.1GB Total)

| Model | Size | Purpose | Details |
|-------|------|---------|---------|
| embedding-gemma-300M Q8_0 | ~300MB | Vector embeddings | Nomic-style task prefixes, ~143MB per context, parallelized across CPU cores |
| qwen3-reranker-0.6B Q8_0 | ~640MB | Re-ranking | Yes/no logprobs scoring, 2048-token context (17x memory reduction vs default), flash attention |
| qmd-query-expansion-1.7B Q4_K_M | ~1.1GB | Query variation generation | Grammar-constrained decoding, outputs typed variants |

### Typed Query Expansion (Novel Pattern)

The expansion model generates three types of query variants via grammar-constrained decoding:
- **`lex:`** — keyword reformulation (for BM25)
- **`vec:`** — semantic rephrasing (for vector search)
- **`hyde:`** — hypothetical answer (HyDE technique — generate what the answer would look like, then search for documents similar to that answer)

This is more specific than LEARN-021's abstract "multi-query retrieval" (#3). The typed approach ensures each search backend gets a query optimized for its strengths. Falls back to simple variants if generation fails.

### Hybrid Fusion: Position-Aware RRF (Novel Implementation Detail)

Standard Reciprocal Rank Fusion: `score = Σ(1/(k+rank+1))` where k=60.

QMD adds two innovations on top:
1. **Top-rank bonuses**: +0.05 for rank 1, +0.02 for ranks 2-3 across any search backend. Preserves high-confidence matches.
2. **Position-aware blending**: After RRF + reranking, the final score blends retrieval and reranker scores with weights that vary by position:
   - Top-3 results: retrieval weight 75%, reranker weight 40% (trusts initial retrieval more)
   - Lower results: reranker gets more influence
   - Prevents the reranker from demoting results that BM25/vector strongly agreed on

This is a non-obvious design choice. Naive approaches let the reranker fully reorder, which can destroy high-confidence keyword matches that the reranker's small model doesn't understand as well.

### Smart Signal Detection (Novel Pattern)

Before running the expensive expansion+rerank pipeline, QMD monitors BM25 scores. If BM25 alone returns high-confidence results, it **skips query expansion entirely**. The `querySearch()` function exposes `onStrongSignal` hooks to log this decision.

This is an elegant cost optimization: don't pay for LLM expansion when keyword search already found what you need. Applicable to our brain search — if BM25 returns a score above a threshold, skip any future LLM-based enhancement.

### Content-Addressable Storage (Confirms LEARN-021 #2)

SQLite schema uses SHA-256 content hashing:
```
content table:  hash (PK) → doc, created_at
documents table: id, collection, path, title → hash (FK to content)
```

Documents stored by content hash — identical content across different paths is stored once. The `documents` table is a filesystem mapping layer. Triggers auto-sync the FTS5 index on insert/update/delete.

This confirms the content hashing pattern from LEARN-021 (#2 improvement) and LangChain's RecordManager, but QMD's implementation is cleaner: content table is the immutable source of truth, documents table is the mutable filesystem layer. Worth adopting this two-table pattern if we implement content hashing for brain.py.

### Smart Chunking for Embeddings

Documents split into 900-token chunks with 15% overlap (~135 tokens). Break points are scored:
- Headings score highest
- Blank lines score lower
- Mid-paragraph breaks score lowest

This preserves semantic coherence within chunks better than fixed-size splitting.

### MCP Server Implementation (Confirms LEARN-002 #1, LEARN-013)

6 tools exposed: `search`, `vector_search`, `deep_search`, `get`, `multi_get`, `status`.

**Novel detail — dynamic instruction injection**: The MCP server injects collection metadata and search strategy guidance into the LLM's system prompt. This eliminates redundant "what collections exist?" tool calls. Our brain MCP server spec (LEARN-013) doesn't include this pattern — worth adopting.

**HTTP daemon mode**: `qmd mcp --http --daemon` keeps models loaded across requests, with health endpoint at `GET /health`. Avoids model reload latency (~seconds) per request.

**Claude Code integration**: Available as a plugin via `claude marketplace add tobi/qmd`. Also works as a Claude Desktop MCP server.

### Session & Resource Management

- **Lazy loading**: Models instantiate only on first use
- **Reference-counted sessions**: Prevents model disposal during active operations
- **5-minute inactivity timeout**: Models stay loaded between searches to avoid VRAM thrash
- **Promise guards**: Prevents concurrent model creation race conditions
- **GPU auto-detection**: CUDA > Metal > Vulkan > CPU fallback

### Tech Stack

- **Runtime**: Node.js >=22 or Bun >=1.0
- **Language**: TypeScript
- **Database**: better-sqlite3 + FTS5 + sqlite-vec
- **LLM**: node-llama-cpp with GGUF quantized models
- **MCP**: @modelcontextprotocol/sdk v1.25.1
- **License**: MIT
- **Tests**: Vitest (unit, model, integration suites)

## Unverified Claims

- **"96% token savings"** — A user reported searching 600+ Obsidian notes went from ~15,000 tokens (grepping whole files) to ~500 tokens (QMD returning snippets). Source: single Twitter anecdote ([andrarchy](https://x.com/andrarchy/status/2015783856087929254)). **Not independently verified.** The comparison is also not apples-to-apples: grepping whole files vs. returning ranked snippets is an expected improvement by definition — the interesting question is whether the *right* snippets are returned, not whether fewer tokens are used. Treat as marketing, not evidence, until validated with controlled benchmarks.

## What's Genuinely Novel vs What Confirms Existing Knowledge

### Novel (not in any brain file)
1. **Typed query expansion** (lex/vec/hyde) — concrete implementation of multi-query retrieval
2. **Position-aware score blending** — prevents reranker from destroying high-confidence retrieval results
3. **Smart signal detection** — skip expensive expansion when BM25 is confident
4. **Concrete model stack** — 300M + 0.6B + 1.7B = ~2.1GB total for full hybrid search
5. **Dynamic MCP instruction injection** — collection-aware system prompts
6. **Two-table content-addressable storage** — cleaner than LangChain's RecordManager pattern
7. **Grammar-constrained decoding** for structured query expansion output

### Confirms existing knowledge
- BM25 search value — LEARN-021 #1 (we just implemented this in brain.py)
- Content hashing for dedup — LEARN-021 #2
- Multi-query retrieval concept — LEARN-021 #3
- Hybrid BM25+vector with RRF — LEARN-021 #5
- MCP server for search — LEARN-002 #1, LEARN-013
- Local-first philosophy — SPEC-000 core principle
- Scored chunking — LEARN-001 (semantic compression segmentation)

## Brain-Relevant Takeaways

1. **Smart signal detection is adoptable now** — add a confidence threshold to our BM25 search. If top result scores above X, skip any future LLM enhancement. Zero cost, simple to implement.
2. **Two-table content-addressable storage** is the cleanest dedup pattern we've seen. When implementing content hashing (#2 from LEARN-021), use this schema: immutable content table keyed by SHA-256, mutable documents table as filesystem mapping.
3. **Position-aware blending** is important if we ever add vector search — naive reranking can destroy keyword match quality. Weight early retrieval results more heavily.
4. **Dynamic MCP instruction injection** — when building brain MCP server, inject collection/type metadata into system prompt so the LLM knows what's available without a discovery tool call.
5. **QMD itself is usable as brain search backend** — we could `qmd collection add project-brain/ --name brain` and get hybrid search over our markdown files for free. Worth testing as a complement to brain.py's BM25.
6. **Model sizing benchmark** — ~2.1GB for full hybrid search is the current "good enough" floor. Useful for planning brain system resource requirements.

## Comparison: QMD vs Brain System

| Aspect | QMD | Project Brain |
|--------|-----|---------------|
| Search method | BM25 + vector + LLM reranker | BM25 on fat index (as of today) |
| Index type | Auto-generated (FTS5 + embeddings) | Human-curated fat index summaries |
| Storage | SQLite (~content-addressed) | Markdown files on disk |
| Resource cost | ~2.1GB models, CPU/GPU compute | Zero (text files + Python) |
| Human readability | Low (SQLite DB) | High (markdown, git-friendly) |
| Dedup | Content hashing (SHA-256) | Manual index scan + human judgment |
| MCP server | Ships one (stdio + HTTP) | Planned (LEARN-013) |
| Relationship | Complement (search backend) | Core system (knowledge storage) |

## Known Issues
- QMD is pre-1.0 (v0.9.9) — API may change
- Requires Node.js >=22 or Bun >=1.0
- ~2.1GB model download on first use
- sqlite-vec is alpha (v0.1.7-alpha.2)
- Windows support via optional platform-specific sqlite-vec binaries — may have rough edges
- 96% token savings claim is unverified (see Unverified Claims section)
- QMD evolves rapidly (74 PRs in last 30 days) — analysis is point-in-time Feb 2026
