# LEARN-051 — Transformer Self-Attention as Soft Indexing
<!-- type: LEARN -->
<!-- tags: transformer,attention,self-attention,query-key-value,indexing,soft-lookup,multi-head,positional-encoding,KV-cache,n-squared,scaling,context-window,architecture -->
<!-- created: 2026-02-20 -->
<!-- source: "Attention is All You Need" (Vaswani et al., NeurIPS 2017) https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf -->
<!-- links: LEARN-044, LEARN-040, LEARN-048, LEARN-030, LEARN-001, LEARN-024, SPEC-005 -->

## Discovery

Transformer self-attention is a differentiable index lookup. The Query-Key-Value mechanism maps directly to information retrieval: **Keys = index entries, Queries = search queries, Values = stored content.** The softmax over Q·K^T/√d_k computes a weighted retrieval over all stored values — a "soft index" where every entry contributes proportionally to its relevance. This is the foundational mechanism that makes LLM context windows work, and its limitations are exactly why external indexes (like our fat index) exist.

## Context

User provided the foundational Transformer paper for analysis through our indexing lens. The brain already references attention costs (L024: "attention budget n² cost", L044: "lost in the middle") but had no deposit covering the actual mechanism or its structural parallels to indexing.

## Evidence

### The QKV Mechanism as Index Lookup

The core attention equation:

```
Attention(Q, K, V) = softmax(Q·K^T / √d_k) · V
```

Mapping to information retrieval:
| Attention component | Index analogy | Our brain equivalent |
|---|---|---|
| **Query (Q)** | Search query | `/brain-search <query>` |
| **Key (K)** | Index entries / signatures | Fat index entries (ID\|tags\|summary) |
| **Value (V)** | Stored content | Full brain file content |
| **softmax(Q·K^T/√d_k)** | Relevance scoring | BM25 scores |
| **Weighted sum of V** | Retrieved result | Loaded file(s) in context |

Critical difference: attention retrieves a **weighted blend** of all values (soft), while our fat index retrieves **discrete files** (hard). Soft lookup enables gradient-based learning; hard lookup enables token efficiency.

### Multi-Head Attention as Parallel Index Spaces

The paper uses h=8 parallel attention heads, each with d_k=d_v=64 dimensions (from d_model=512):

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W^O
where head_i = Attention(Q·W_i^Q, K·W_i^K, V·W_i^V)
```

Each head learns a different "index" over the same data:
- Head 1 might index by syntactic role
- Head 2 might index by semantic similarity
- Head 3 might index by positional proximity

**Brain parallel:** This is analogous to our multi-field search (tags 5x, ID 4x, title 3x boost in L030) — different "heads" weighting different aspects of the same documents. Also parallels sub-indexes (INDEX-claude-code) focusing on different clusters.

### Positional Encoding as Address Scheme

Since attention is permutation-invariant (bag-of-tokens), position must be explicitly encoded:

```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

Properties:
- **Unique address per position** — each position gets a distinct vector
- **Relative distances recoverable** — PE(pos+k) is a linear function of PE(pos) for any fixed k
- **No learned parameters** — deterministic, generalizes to unseen lengths

**Brain parallel:** Our file IDs (LEARN-051) and the sequential numbering serve as positional encoding — they encode creation order and enable relative temporal reasoning ("L051 came after L050"). The compressed-v1 format's pipe-delimited fields encode structural position within an entry.

### The n² Problem and Why External Indexes Exist

Self-attention costs O(n²·d) in compute and O(n²) in memory, where n = sequence length. This means:
- 4K context: 16M attention computations
- 128K context: 16.4B attention computations (1000x more)
- 200K context: 40B attention computations

**This is the fundamental reason our brain exists.** Loading all 64 brain files (~100K+ tokens per L040) would burn massive attention budget on irrelevant content. The fat index serves as a **hard pre-filter** that reduces n before attention's n² kicks in:

```
Without brain: attention over 100K tokens → 10^10 operations
With brain:    BM25 selects 3 files (~5K tokens) → 2.5×10^7 operations
Savings:       ~400x fewer attention operations
```

### KV-Cache as Runtime Index

During autoregressive generation, previously computed Key and Value vectors are cached (the "KV-cache"). This is literally a **runtime index** that grows with each generated token:
- **Structure:** Append-only array of (K, V) pairs per layer per head
- **Query model:** New token's Q vector queries all cached K vectors
- **Write cost:** O(d) per token (compute and store one K, V pair)
- **Space overhead:** O(n·d·L·h) where L=layers, h=heads — grows linearly with context
- **Scaling:** Memory-bound; at 128K context with 80 layers, KV-cache alone can exceed 10GB

**Brain parallel:** KV-cache is to transformers what INDEX-MASTER is to our brain — a growing index that enables efficient lookup without reprocessing all stored content. Both face scaling pressure (KV-cache memory; INDEX-MASTER token budget).

### "Lost in the Middle" — Attention Distribution Decay

Referenced in L044 but worth grounding here: attention scores follow a U-shaped distribution over position — tokens attend strongly to the beginning and end of context, with a trough in the middle. This is not a bug in any specific model but an emergent property of how positional encodings interact with learned attention patterns.

**Brain implication:** Position within the context window matters. Fat index entries loaded first (system prompt) and last (recent conversation) get disproportionate attention. Files loaded in the middle of a large context dump are effectively "lost." This validates progressive disclosure (L044) and the MCP server's selective loading (C001).

## Impact

### Direct implications for brain design

1. **Fat index = hard attention pre-filter.** Our BM25 search replaces the n² soft lookup with an O(n·log n) hard filter. The theoretical savings are enormous — this is the strongest justification for the brain's existence beyond "it saves tokens."

2. **Multi-field search ≈ multi-head attention.** Our tag/ID/title field boosting (L030) is a crude discrete analog of multi-head attention. Brain v2 (S005) could formalize this: typed link indexes = specialized attention heads over the knowledge graph.

3. **Position matters for loaded content.** System prompt and recent messages get strongest attention. Brain files should be loaded in importance order, not creation order. The MCP server (C001) should return highest-relevance files first.

4. **KV-cache analogy validates append-only INDEX-MASTER.** Both are growing indexes with O(1) append, O(n) lookup. Both face scaling pressure. The compressed-v1 format (L046) is essentially KV-cache quantization — reducing per-entry cost to extend capacity.

5. **The n² wall is our opportunity.** As context windows grow, the attention cost grows quadratically but the value of additional context grows sub-linearly (diminishing returns + lost-in-the-middle). External indexes that provide **the right 5K tokens** will always beat naively loading 200K tokens.

### Connections to existing brain work

- **L048/L049 (hypertext indexing):** The three-case decomposition (within-node, one-edge, multi-edge) maps to attention patterns: within a single document, across one link, across a chain. The γ² bottleneck in L049 is structurally identical to attention's n² — both are exhaustive pairwise comparisons.
- **S005 (Brain v2):** Three-layer index (fat + link + cluster) parallels the Transformer's three information flows (token content + position + cross-attention between encoder/decoder).
- **L046 (compressed format):** Token reduction in fat index entries = "quantization" of the brain's KV-cache. 70% reduction extends the index's effective capacity the same way KV-cache compression extends context.

## Action Taken

Deposited as LEARN-051. This provides theoretical grounding for why the fat-index architecture works: it replaces O(n²) soft attention with O(n·log n) hard pre-filtering, dramatically reducing the attention budget spent on irrelevant content.
