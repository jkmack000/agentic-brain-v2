# LEARN-028: Context7 Architecture Analysis
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: context7, MCP, library-docs, architecture, search, reranking, coder-brain, upstash, vector-search -->
<!-- links: LEARN-013, LEARN-002, LEARN-023, SPEC-001 -->

## Purpose

Architecture analysis of Context7 (Upstash) — an MCP server providing up-to-date library documentation to AI coding assistants. Directly informs the Coder brain design for Prover.

---

## 1. What Context7 Does

Solves: LLMs generate code from stale training data with hallucinated APIs. Context7 injects version-specific library docs into the LLM's context at query time.

**End-to-end flow:**
1. User writes coding prompt with "use context7"
2. LLM calls `resolve-library-id` with library name → gets Context7 ID
3. LLM calls `get-library-docs` with ID + topic query
4. Backend performs semantic search + reranking against pre-indexed docs
5. Relevant snippets returned (default 5000 tokens, configurable)
6. LLM generates code using accurate, current API references

**Scale:** 33,000+ libraries indexed, crawled on 10-15 day rolling schedule.

---

## 2. Architecture: Thin Client, Thick Backend

### Public (open source)
TypeScript monorepo (pnpm): MCP server (`packages/mcp/`), REST SDK (`packages/sdk/`), Vercel AI SDK tools, CLI.

### Private (proprietary backend)
- **Crawling engine** — auto-crawls 33K+ library doc sites every 10-15 days
- **Parsing engine** — extracts code from MD, MDX, RST, Jupyter notebooks
- **Enrichment pipeline** — LLM adds short explanations to raw snippets
- **Vector store** — Upstash Vector (multiple embedding models by content complexity)
- **Reranker** — `c7score` algorithm (5 metrics: question-snippet comparison, LLM evaluation, formatting, project metadata, initialization penalty)
- **Cache** — Upstash Redis for hot queries

**Key decision:** MCP server is a pass-through (~2 files of real logic). All intelligence lives server-side. Zero local compute, instant updates.

---

## 3. MCP Integration

- **Remote HTTP** (recommended): `https://context7.com/mcp`, OAuth 2.0
- **Local stdio**: `npx @upstash/context7-mcp`, API key via `--api-key`
- Uses `McpServer` from `@modelcontextprotocol/sdk` with Zod schema validation
- `AsyncLocalStorage` for request-scoped context (Node.js) — Python equivalent: `contextvars`

---

## 4. Tool Interface

### `resolve-library-id`
- **Input:** `libraryName` (string), `query` (string)
- **Output:** Ranked list of matching libraries with Context7 IDs
- Equivalent to our fat-index search

### `get-library-docs`
- **Input:** `context7CompatibleLibraryID` (string), `query` (string), `topic` (optional), `tokens` (optional, default 5000)
- **Output:** Relevant doc snippets within token budget
- Equivalent to our brain file read

### REST API
- `GET /v2/libs/search` — library discovery
- `GET /v2/context` — doc retrieval
- Auth: `Authorization: Bearer ctx7sk_...`

---

## 5. Data Pipeline (5-Stage)

```
Source docs → Parse → Enrich → Vectorize → Rerank → Cache
```

1. **Parse:** Extract code + text from MD/MDX/RST/ipynb
2. **Enrich:** LLM adds explanations to raw snippets (key differentiator — transforms docs into LLM-optimized form)
3. **Vectorize:** Multiple embedding models — fast/small for short snippets, high-precision for complex examples
4. **Rerank:** c7score (open-source) — 5 weighted metrics, configurable weights summing to 1.0
5. **Cache:** Redis for popular queries

### Performance (after recent architecture update)
- **65% token reduction** (9.7K → 3.3K average context)
- **38% latency reduction** (24s → 15s)
- **30% tool call reduction** (3.95 → 2.96 calls/task)

Key insight: moved filtering from LLM (expensive, slow, nondeterministic) to backend (cheap, fast, deterministic).

---

## 6. Patterns Transferable to Coder Brain

### Pattern 1: Two-Tool Resolution (resolve then fetch)
Maps to: `brain-search` (fat-index matches) → `brain-read` (file content within budget). Prevents token waste on irrelevant content.

### Pattern 2: Token-Budgeted Responses
The `tokens` parameter caps response size. Coder brain MCP should accept token budget, return most relevant content within it.

### Pattern 3: Query-Aware Reranking
Context7 passes user's query into every API call for reranking. Brain search should do same — not just keyword match, but query-aware BM25 scoring (LEARN-021 #1 improvement).

### Pattern 4: Enrichment at Index Time
LLM adds explanations during ingestion, not retrieval. Same as our fat-index entries — pre-computed summaries answering "do I need this?" Cost paid once, savings on every query.

### Pattern 5: Backend Filtering > LLM Filtering
65% token reduction from moving filtering off LLM. Brain MCP should do search/rank/filter, return only relevant content. Aligns with LEARN-002's MCP wrapper as #1 priority.

### Pattern 6: Adaptive Embedding by Content Type
Different models for different sizes/complexity. Brain analog: fast embeddings for fat-index entries, high-precision for full LEARN/SPEC files.

### Pattern 7: Rolling Freshness
10-15 day crawl cycle. Brain analog: periodic consolidation/defragmentation (SPEC-000, LEARN-024).

---

## 7. Context7 + Coder Brain: Complementary, Not Competing

| Aspect | Context7 | Coder Brain |
|--------|----------|-------------|
| **Answers** | "How does this library work?" | "How does OUR project use it and why?" |
| **Data** | External library docs (crawled) | Local project knowledge (deposited) |
| **Storage** | Cloud vector DB + Redis | Local markdown + optional BM25/vector |
| **Scale** | 33K+ libraries, millions of snippets | 1 project, tens to hundreds of files |
| **Freshness** | Auto-crawled every 10-15 days | Updated every session by LLM |

**Ideal integration:**
```
Claude Code
├── Context7 MCP → "How does Next.js App Router work?"
└── Coder Brain MCP → "How does OUR project use App Router and why?"
```

### What Context7 doesn't solve (our opportunity)
1. **Project-specific knowledge** — your architecture decisions, edge cases, conventions
2. **Persistent session state** — cross-session memory via SESSION-HANDOFF, LOGs
3. **Knowledge evolution tracking** — contradiction tracking, decision logs, "why did we do X?"
4. **Local-first operation** — zero external dependencies
5. **Custom domain knowledge** — proprietary rules, internal APIs, team standards

---

## 8. Concrete Next Steps for Brain MCP Server

1. Implement two-tool pattern: `brain-search` + `brain-read` (with token budget)
2. Add token budget parameter to `brain-read`
3. Pass query context into search for relevance ranking
4. Pre-enrich at deposit time (already our design — validated by Context7)
5. Consider `brain-deposit` as third tool
6. Use stdio transport for local-first (aligns with LEARN-013)

---

## Sources

- [Context7 GitHub Repository](https://github.com/upstash/context7)
- [Context7 MCP Blog Post](https://upstash.com/blog/context7-mcp)
- [Introducing Context7](https://upstash.com/blog/context7-llmtxt-cursor)
- [Context7 Without Context Bloat](https://upstash.com/blog/new-context7)
- [Inside Context7's Quality Stack](https://upstash.com/blog/context7-quality)
- [c7score Repository](https://github.com/upstash/c7score)
- [DeepWiki - Context7 Architecture](https://deepwiki.com/upstash/context7)
- [Context7 API Guide](https://context7.com/docs/api-guide)

## Known Issues
- Backend is proprietary — can't inspect indexing/ranking internals
- c7score evaluation uses Vertex AI/Gemini — vendor-locked quality scoring
- "96% token savings" claim from Twitter is unverified (single anecdote)
- Pre-1.0 MCP server — API may change
