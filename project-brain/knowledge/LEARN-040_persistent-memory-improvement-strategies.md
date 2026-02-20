# LEARN-040 — Persistent Memory Improvement Strategies for LLM Systems
<!-- type: LEARN -->
<!-- tags: memory, context-window, MCP, embeddings, architecture, scaling, multi-agent, prompt-caching -->
<!-- created: 2026-02-17 -->
<!-- source: session analysis — synthesized from brain knowledge + architectural reasoning -->
<!-- links: SPEC-000, LEARN-002, LEARN-013, LEARN-024, LEARN-028, LEARN-030, LEARN-031, SPEC-001 -->

## Discovery
Systematic evaluation of 9 strategies for improving persistent LLM memory beyond the current Project Brain file-based system. Triggered by loading all 37 LEARN files into a single context window — which blew through the 200K token limit and caused compaction, proving the need for better access patterns.

## Context
Current brain system stores knowledge as markdown files with fat indexes. The fat index (INDEX-MASTER.md) is the optimization layer — it lets LLMs skip files they don't need. But the system still requires loading files into context, which is finite. The question: what's better?

## Strategies Evaluated

### Tier 1: Improve Access Without More Context (highest ROI)

#### 1. MCP Memory Server (RECOMMENDED — highest leverage)
- Wrap brain.py as an MCP server with stdio transport
- LLM sends search queries via tool calls → server returns relevant *paragraphs*, not whole files
- Fat index stays in context (~5-8K tokens), individual files never loaded unless explicitly requested
- Already have BM25 search in brain.py, LEARN-013 covers full MCP architecture
- Context7 (LEARN-028) validates two-tool pattern: `resolve` + `get` with token budget parameter
- **Impact:** Brain accessible at near-zero context cost. Changes brain from "load files" to "query knowledge"
- **Effort:** Medium — MCP SDK + wrap existing search + add resource/prompt support

#### 2. Embeddings + Vector Search (medium effort)
- Add sentence embeddings alongside BM25 for semantic recall
- "What do I know about validation pipelines?" finds content even if exact words aren't in fat index
- ChromaDB or sqlite-vec for local storage (LEARN-030 recommends sqlite-vec)
- LEARN-030 3-phase roadmap: tokenizer (done) → SQLite FTS5 → hybrid search
- **Impact:** Better recall for conceptual queries. Complements BM25 for cross-domain search
- **Effort:** Medium — embedding model + vector store + RRF fusion

#### 3. Progressive Context Loading (process change, zero code)
- Load only INDEX-MASTER (~8K tokens), let LLM request files on demand
- This IS the current design — fat index discipline. But gets bypassed when loading all files at once
- **Impact:** Already works when discipline is followed. No code needed
- **Effort:** Zero — behavioral, already designed

#### 4. RESET Files as Pre-Computed Context Packs
- For known tasks, pre-compute RESET file bundling exactly the 5-6 files needed
- Already specced in SPEC-000, already implemented in brain.py `recall` command
- Underused in practice
- **Impact:** Reduces context waste for recurring task types
- **Effort:** Zero — already built, just needs more use

### Tier 2: Increase Effective Context

#### 5. Multi-Agent Context Splitting (already designed)
- Prover architecture: each agent gets own 200K window with only its domain knowledge
- Orchestrator coordinates via CONTEXT-PACK/RESULT protocol (~750/~1500 tokens each)
- 3 specialists × 200K = 600K effective context
- SPEC-001, LEARN-026, LEARN-027 cover this extensively
- **Impact:** Linear context scaling with agent count
- **Effort:** High — requires full Prover build

#### 6. Prompt Caching (Anthropic API feature)
- Cached prefixes (brain index + rules) don't count against per-request costs after first call
- Brain's static files are ideal cache candidates — they change slowly
- Doesn't increase window but reduces cost of keeping brain context loaded
- **Impact:** 90% cost reduction for brain context. Better economics, not more capacity
- **Effort:** Low — API configuration, no brain changes

#### 7. Hierarchical Summarization
- Three levels: INDEX-MASTER (one-line) → Sub-indexes (paragraph) → Full files
- Currently have two levels. Adding "executive summary" per cluster (~500 tokens) would improve recall
- LEARN-031 discusses progressive summarization (Forte's 5-layer model)
- **Impact:** Better recall without opening individual files
- **Effort:** Low-medium — write cluster summaries, update sub-index format

### Tier 3: Architectural Alternatives

#### 8. External Memory Store (mem0/Letta pattern)
- Move brain content to external DB (Postgres + pgvector, or Letta managed memory)
- LLM queries via tool calls, never holds full corpus in context
- LEARN-020 (mem0-dspy) and LEARN-024 (Letta) cover this architecture
- **Downside:** Lose human-readable, git-friendly markdown. Lose transparency and debuggability
- **Impact:** Unlimited memory capacity. Total architectural change
- **Effort:** Very high — full rewrite, lose core advantages

#### 9. Wait for Bigger Windows
- Context has grown from 100K → 200K. Likely to grow further
- Architecture that works at 200K works even better at 500K
- **Impact:** Free improvement. But doesn't solve the access pattern problem
- **Effort:** Zero — wait

## Recommendation Stack
1. **MCP Memory Server** (Option 1) — transforms brain from "load files" to "query knowledge". Highest ROI
2. **Prompt Caching** (Option 6) — reduces cost of current approach immediately
3. **Hierarchical Summarization** (Option 7) — improves fat index recall for free
4. **Vector Search** (Option 2) — adds semantic dimension when BM25 isn't enough

Options 3 and 4 are already built. Options 5 and 8 are larger architectural projects. Option 9 is free but passive.

## Key Insight
The fundamental problem isn't memory *storage* — the brain already stores knowledge well. The problem is the **access pattern**: loading whole files into context is wasteful. The MCP server changes the access pattern from "read file" to "query and receive relevant excerpts" — the same shift that made databases better than flat files.

## Action Taken
Deposited as LEARN-040. MCP Memory Server design to follow as implementation task.
