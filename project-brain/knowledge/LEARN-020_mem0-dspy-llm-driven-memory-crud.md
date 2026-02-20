# LEARN-020 — mem0-dspy: LLM-Driven Memory CRUD via DSPy ReAct Agents
<!-- type: LEARN -->
<!-- tags: mem0, dspy, react-agent, memory-crud, qdrant, vector-search, competitive-analysis, architecture-patterns -->
<!-- created: 2026-02-15 -->
<!-- source: https://github.com/avbiswas/mem0-dspy — full source analysis -->
<!-- links: LEARN-002, LEARN-001, SPEC-000 -->

## Discovery
A from-scratch Mem0 reimplementation (~300 lines Python) reveals that Mem0's core innovation is **two LLM agents in sequence**: one for response generation (with optional memory search), one for memory CRUD (ADD/UPDATE/DELETE/NOOP decided by the LLM itself). The LLM-driven CRUD pattern is the key differentiator vs. our rule-based `/brain-deposit` dedup check — it automates the same judgment we do manually.

## Context
Analyzed avbiswas/mem0-dspy repo as competitive intelligence for Project Brain. The repo strips away Mem0's cloud API to expose the underlying architecture using DSPy (structured LLM programming framework) and Qdrant (vector DB).

## Evidence

### Architecture
```
User Input → Agent 1: ResponseGenerator (DSPy ReAct)
                 |— Tool: fetch_similar_memories() → Qdrant search
                 |— Outputs: response text + save_memory boolean
                 v (if save_memory == true)
             Agent 2: UpdateMemory (DSPy ReAct)
                 |— Tools: add_memory(), update(), delete(), noop()
                 |— Sees: last 6 messages + existing similar memories
                 |— Outputs: summary of actions taken
                 v
             Qdrant (64-dim DOT product vectors)
```

### Key Implementation Patterns

**1. Two-agent separation of concerns**
- Agent 1 (ResponseGenerator): answers user, optionally searches memories, outputs boolean `save_memory` flag. Max 2 tool iterations.
- Agent 2 (UpdateMemory): receives recent messages + retrieved similar memories, decides which CRUD operation(s) to perform. Max 3 tool iterations.
- This mirrors Mem0's two-phase approach (respond, then update) but makes it explicit and inspectable.

**2. DSPy Signatures as agent contracts**
- Each agent defined via `dspy.Signature` class with typed input/output fields
- Docstring serves as system prompt — no raw prompt engineering
- Structured outputs: `response: str`, `save_memory: bool`, `summary: str`
- `dspy.ReAct(Signature, tools=[...], max_iters=N)` wraps it as a tool-calling agent

**3. LLM-driven CRUD decisions**
- The UpdateMemory agent sees both new conversation AND existing similar memories
- It decides: ADD (genuinely new), UPDATE (enrich existing — delete old + reinsert with new embedding), DELETE (stale/contradicted), NOOP (already known)
- This is exactly our `/brain-deposit` dedup check (new/enrich/skip/contradiction) but automated via LLM

**4. Category faceting for guided search**
- Memories tagged with LLM-assigned categories (e.g., "travel", "food preferences")
- Qdrant's `facet` API enumerates all existing categories per user
- Categories passed to Agent 1 so it can filter searches — avoids blind full-DB searches

**5. Aggressive embedding compression**
- OpenAI `text-embedding-3-small` at **64 dimensions** (default is 1536 — this is 24x smaller)
- DOT product distance, score threshold 0.1, limit 2 results
- Trades semantic precision for speed and storage cost

**6. Update = delete + reinsert**
- No in-place mutation — embedding changes when text changes
- `update()` tool: looks up `point_id` by index, deletes old point, generates new embedding, inserts fresh record

### Bugs Found in the Repo
1. **`delete()` tool** passes `memory_ids` (integer indexes) directly to `delete_records()` instead of mapping to Qdrant `point_id` strings — will crash
2. **Date format** — `%H:%m` should be `%H:%M` (gets month instead of minutes)
3. **Duplicated facet call** in `get_all_categories()` — calls `client.facet()` twice identically
4. **`"/n -"` join** in baseline chatbot — should be `"\n -"`

### Technology Stack
- DSPy 3.0+ (agent orchestration via Signatures + ReAct)
- Qdrant (local Docker, async client)
- OpenAI `text-embedding-3-small` (64 dims)
- `gpt-5-mini` with `reasoning_effort="minimal"`, `temperature=1`
- Pydantic v2 data models
- Full async/await throughout

## Impact

### Comparison with Project Brain

| Aspect | mem0-dspy | Project Brain |
|--------|-----------|---------------|
| Storage | Qdrant vectors (64-dim) | Markdown files + fat index |
| Search | Semantic similarity (embedding) | Keyword scan on fat index summaries |
| CRUD decisions | LLM-driven (ReAct agent) | Rule-based (/brain-deposit dedup check) |
| Dedup | LLM compares new vs existing | Manual index scan + human judgment |
| Categories | Auto-assigned by LLM | Typed file system (SPEC/LEARN/RULE/etc) |
| Compression | 64-dim embedding (lossy) | Semantic compression in summaries (lossless) |
| Cost per operation | OpenAI API call | Zero (file reads) |
| Transparency | Full (source visible) | Full (markdown readable) |
| Cross-session persistence | Qdrant DB | File system |
| Human readability | Low (vectors + payloads) | High (markdown) |

### Brain-Relevant Takeaways
1. **LLM-driven CRUD is the automation path for `/brain-deposit`** — an agent that sees the conversation + existing fat index entries could automate the dedup check
2. **Category faceting** maps to our file type system but is more granular — worth considering sub-categories or tags as searchable facets
3. **The `save_memory` boolean pattern** is interesting — our PostToolUse hook could trigger a lightweight "should this be deposited?" check instead of always reminding
4. **64-dim embeddings** are viable for small memory stores — if we add vector search to brain.py, we don't need large embeddings
5. **DSPy Signatures** are a cleaner alternative to raw prompts for structured agent tasks — relevant if we build brain automation via Agent SDK

## Action Taken
Deposited as LEARN-020. No implementation changes — findings inform future brain automation design. Key candidate for implementation: LLM-driven dedup check as an enhancement to `/brain-deposit` skill.
