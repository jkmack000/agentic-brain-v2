# LEARN-021 — LangChain/LangGraph: Architecture, Memory, Retrieval, and Agent Patterns
<!-- type: LEARN -->
<!-- tags: langchain, langgraph, deep-agents, memory, persistence, retrieval, RAG, middleware, competitive-analysis, architecture-patterns -->
<!-- created: 2026-02-15 -->
<!-- source: https://docs.langchain.com/ — full documentation analysis via 3 parallel research agents -->
<!-- links: LEARN-002, LEARN-020, SPEC-000 -->

## Discovery
LangChain has reorganized (Feb 2026) into three layered products: **DeepAgents** (autonomous agents with auto-compression and virtual filesystem), **LangChain Agents** (`create_agent` with middleware), and **LangGraph** (stateful graph workflows). Their memory architecture adopts the CoALA psychology-derived taxonomy (semantic/episodic/procedural) which maps directly to our file types (LEARN+SPEC / LOG / RULE). Multiple patterns independently validate our brain architecture, while several novel patterns (BM25 hybrid search, content hashing dedup, transient vs persistent context, procedural self-modifying memory) represent actionable improvements.

## Context
Researched full LangChain documentation as competitive intelligence for Project Brain. Three parallel agents analyzed: (1) site structure and overview, (2) memory/persistence/retrieval/indexing, (3) agents/tools/RAG/LangGraph. Source was the reorganized docs.langchain.com site plus raw MDX source files from the langchain-ai/docs GitHub repo.

## Evidence

### Product Structure (Reorganized Feb 2026)

```
LangChain Ecosystem
├── DeepAgents (NEW) — autonomous agents, auto-compression, virtual filesystem, subagent-spawning
├── LangChain Agents (create_agent) — standard tool-calling agents with middleware system
├── LangGraph — stateful graph workflows, persistence, human-in-the-loop
└── LangSmith (proprietary) — observability, evaluation, deployment, agent builder
```

Each layer builds on the one below. DeepAgents uses LangChain Agents, which uses LangGraph.

### Memory Architecture (CoALA Paper Taxonomy)

LangGraph adopted a psychology-derived memory model with two scopes and three types:

**Two scopes:**
- **Short-term** (thread-scoped) — conversation state persisted via checkpointers, keyed by `thread_id`
- **Long-term** (cross-session) — Store with namespace tuples + key-value pairs, semantic search optional

**Three types:**

| Memory Type | What it Stores | LangGraph Implementation | Brain Equivalent |
|-------------|---------------|-------------------------|-----------------|
| **Semantic** | Facts | Store (profile or collection approach) | LEARN, SPEC files |
| **Episodic** | Past experiences | Few-shot example prompting from stored episodes | LOG files |
| **Procedural** | Instructions/rules | Self-modifying prompts via reflection | RULE files, .claude/rules/ |

**Semantic memory — two approaches:**
1. **Profile** — single continuously-updated JSON doc per entity. Model receives old profile + new info, generates updated version (or JSON patch via Trustcall package). Risk: information loss as profile grows.
2. **Collection** — growing set of narrowly-scoped documents. Higher recall (easier for LLM to generate new objects than reconcile with existing). Complexity shifts to search and dedup. Our brain uses this approach exclusively.

**Memory writing strategies:**
- **Hot path** (synchronous) — memories immediately available, adds latency, agent multitasks. Example: ChatGPT's `save_memories` tool.
- **Background** (async) — no latency impact, separate process, challenge is scheduling triggers. Common: time-based, cron, manual.

### Persistence: Checkpointers + Store

| Concept | LangGraph | Brain System |
|---------|-----------|-------------|
| Thread state | Auto-checkpoint every super-step | SESSION-HANDOFF.md (manual/triggered) |
| Time travel | Replay from any checkpoint, fork | Git commits (proposed in LEARN-002, not implemented) |
| Cross-thread memory | Store with namespace tuples + semantic search | INDEX-MASTER.md + typed files (keyword search only) |
| Durability modes | exit/async/sync | Single mode (manual handoff) |
| State history query | `get_state_history()` returns all checkpoints | LOG-002 timeline (append-only, not queryable) |

**Store API:**
```python
store = InMemoryStore(index={"embed": embed_fn, "dims": 1536})
store.put(("user123", "memories"), "a-memory", {"rules": ["User likes short language"]})
item = store.get(("user123", "memories"), "a-memory")
items = store.search(("user123",), query="language prefs", filter={"key": "val"})
```

Store backends: InMemoryStore (dev), PostgresStore, RedisStore (production). Supports AES encryption via `EncryptedSerializer`.

### Middleware System (6 Hook Types)

LangChain's primary extensibility mechanism for **context engineering**:

| Hook | When | Persistence | Brain Parallel |
|------|------|-------------|---------------|
| `@before_model` | Before each LLM call | Persistent (modifies saved state) | SessionStart hook |
| `@after_model` | After each LLM call | Persistent | PostToolUse hook |
| `@wrap_model_call` | Wraps LLM call | **Transient** (model sees it, state doesn't save it) | No equivalent — novel |
| `@wrap_tool_call` | Wraps tool execution | Persistent | PreToolUse/PostToolUse hooks |
| `@dynamic_prompt` | Before LLM call | **Transient** | CLAUDE.md @path imports |
| `SummarizationMiddleware` | Between calls, token threshold | Persistent | PreCompact hook + handoff at 80% |

**Key novel concept: Transient vs Persistent context.** `@wrap_model_call` modifies what the LLM sees for a single call without changing saved state. Our hooks either echo messages (loosely transient) or modify files (persistent). This distinction is architecturally useful — inject brain context for one call without bloating the conversation history.

**SummarizationMiddleware:** Built-in auto-summarization with configurable token threshold and message retention:
```python
SummarizationMiddleware(model="gpt-4.1-mini", trigger=("tokens", 4000), keep=("messages", 20))
```

### Agent Tool-Calling Patterns

**ToolRuntime injection** — tools receive runtime access to state, store, context, and stream_writer without exposing these to the LLM's tool schema:
```python
@tool
def brain_search(query: str, runtime: ToolRuntime) -> str:
    """Search the brain fat index."""
    return runtime.store.search(("brain",), query=query, limit=5)
```

**Command return** — tools simultaneously update state AND navigate the graph:
```python
@tool
def brain_deposit(content: str, runtime: ToolRuntime) -> Command:
    runtime.store.put(("brain", "learnings"), next_id, {"content": content})
    return Command(update={"deposited": True}, goto="update_index")
```

**Dynamic tool selection** — middleware filters available tools based on conversation state, auth, permissions, or task type. Brain tools could surface only during ingestion sessions, hide during pure coding sessions.

### Retrieval Patterns (Priority-Ranked for Brain)

| # | Pattern | What It Does | Brain Impact | Effort |
|---|---------|-------------|-------------|--------|
| 1 | **BM25 over fat index** | Term-frequency keyword scoring | Immediate search quality upgrade over naive keyword match | Low |
| 2 | **Content hashing for dedup** | SHA-256 per file, auto-detect new/changed/deleted | Replaces manual INDEX-MASTER dedup scan | Low |
| 3 | **Multi-query retrieval** | LLM generates 3-5 query reformulations, merge results | Better recall on ambiguous searches | Low |
| 4 | **Self-query filtering** | LLM parses "What LEARNs about hooks?" → `{type:LEARN} + "hooks"` | Leverages existing type/tag metadata | Medium |
| 5 | **Hybrid BM25 + vector** | Ensemble with reciprocal rank fusion | Best of keyword + semantic | Medium |
| 6 | **ParentDocumentRetriever** | Embed small chunks, retrieve full parent doc | Already our architecture (fat index = small chunk) | N/A |
| 7 | **ContextualCompressionRetriever** | Post-retrieval LLM extraction of relevant portions | Useful when brain files are large | Medium |

**ParentDocumentRetriever is our fat index.** LangChain independently arrived at the same pattern — embed/summarize small chunks for matching, retrieve full parent documents when needed. Implemented with vectors instead of summaries.

**Indexing API with content hashing:**
- `RecordManager` tracks what's been indexed, content hashes, last update times
- On re-indexing, computes diffs: only processes changed documents
- Three cleanup modes: None (add only), incremental (remove stale from same source), full (remove all not in current batch)
- Directly solves our dedup problem systematically — `brain reindex` command using content hashes

### LangGraph State Machine Workflows

Agents modeled as directed graphs (inspired by Google's Pregel):
- **Nodes** = functions that transform state
- **Edges** = transitions (fixed or conditional)
- **State** = typed dict with reducers controlling how updates merge
- **Super-steps** = discrete iterations with message passing between nodes

Brain operations as a graph:
```
user_query → route → search_brain → synthesize → respond
                   → read_file ──────┘
                   → deposit_knowledge → update_index
```

**Durable execution** with three modes:
- `"exit"` — persist only on graph exit (fastest, least durable)
- `"async"` — persist asynchronously while next step runs
- `"sync"` — persist synchronously before next step (slowest, most durable)

**`@task` decorator** for idempotent replay — wraps non-deterministic operations (API calls, writes) so results are stored in persistence layer and not re-executed on replay. Relevant for brain deposit operations.

### DeepAgents (NEW — Post May 2025)

Limited info available (new section, couldn't fetch full docs). Known features:
- **Automatic compression** of long conversations (beyond SummarizationMiddleware)
- **Virtual filesystem** — agents get an isolated file workspace
- **Subagent spawning** for managing/isolating context
- Built on top of LangChain Agents, which is built on LangGraph

This is the most directly competitive layer to our brain system — autonomous agents with built-in context management. Needs deeper research when docs stabilize.

## Impact

### Architectural Validations (Independent Convergence)

Four patterns in LangChain/LangGraph independently converge on brain system architecture:
1. **ParentDocumentRetriever** = our fat index (summary for matching, full doc for retrieval)
2. **ConversationSummaryMemory** = our fat index entries (LLM-generated compressed representations)
3. **Store namespace tuples** = our directory structure (`("brain", "learnings")` ≈ `project-brain/learnings/`)
4. **Context engineering principle** ("right context > model capability") = validates INDEX-MASTER.md approach

### Brain-Relevant Takeaways

1. **BM25 search is the #1 low-effort improvement** — `rank_bm25` Python package over fat index entries, no vector DB needed
2. **Content hashing automates dedup** — SHA-256 per brain file replaces manual INDEX-MASTER scanning
3. **Multi-query retrieval** is implementable now — `/brain-search` skill could generate alternative phrasings before searching
4. **Profile + Collection dual strategy** — we use collection only; a "profile" document per project would provide holistic context
5. **Transient context injection** is a missing pattern — inject brain knowledge for one LLM call without saving to conversation state
6. **Procedural memory** (self-modifying RULE files based on session feedback) is a novel improvement path
7. **Background memory writing** — async deposit queue, separated from primary task, reduces session friction
8. **Memory type taxonomy** (semantic/episodic/procedural) maps cleanly to our file types — could improve search by querying memory type intent
9. **Durable execution modes** — relevant for choosing when to write SESSION-HANDOFF (our "exit" vs "sync" decision)
10. **DeepAgents virtual filesystem + auto-compression** — most directly competitive to brain system, needs monitoring

### Comparison Table: LangGraph Store vs Project Brain

| Aspect | LangGraph Store | Project Brain |
|--------|----------------|---------------|
| Storage | JSON in DB (Postgres/Redis) | Markdown files on disk |
| Organization | Namespace tuples + keys | Directories + typed file prefixes |
| Search | Semantic (embeddings) + content filters | Keyword scan on fat index summaries |
| Dedup | Content hashing via RecordManager | Manual index scan + human judgment |
| Persistence | Automatic (checkpointers) | Manual (SESSION-HANDOFF, /brain-handoff) |
| Human readability | Low (JSON in DB) | High (markdown, git-friendly) |
| Cost per operation | DB queries + optional embedding API | Zero (file reads) |
| Cross-session | Store (cross-thread namespaces) | File system (all sessions read same files) |
| Encryption | AES via EncryptedSerializer | None (plaintext markdown) |

## Action Taken
Deposited as LEARN-021. No implementation changes. Key actionable items:
- **Immediate:** Add BM25 scoring to `brain.py search` (low effort, high impact)
- **Short-term:** Content hashing for automatic dedup in `/brain-deposit`
- **Medium-term:** Multi-query retrieval in `/brain-search` skill
- **Future:** Hybrid BM25+vector search, procedural memory, background deposit queue
- **Monitor:** DeepAgents development — most directly competitive to brain system
