# LEARN-030: BM25 and Hybrid Search Implementation Patterns
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: BM25, search, hybrid-search, vector-search, ranking, Python, brain-py, implementation, RRF, reranking, SQLite-FTS5 -->
<!-- links: LEARN-021, LEARN-023, SPEC-000 -->

Research synthesis for improving brain.py search. Covers BM25 fundamentals, Python library options, hybrid search architectures, field boosting, query expansion, reranking, and practical recommendations for a 30-200 document markdown corpus.

---

## 1. BM25 Fundamentals

### Algorithm Mechanics

BM25 (Best Matching 25) extends TF-IDF with two critical improvements:
- **Term frequency saturation** -- controlled by `k1`. Prevents a term appearing 100 times from scoring 100x higher than one appearance. Score increases diminish as term frequency grows.
- **Document length normalization** -- controlled by `b`. Penalizes long documents that match simply because they contain more words.

**The BM25 scoring formula:**
```
score(D, Q) = SUM_i [ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl)) ]
```

Where:
- `f(qi, D)` = frequency of term qi in document D
- `|D|` = document length (in tokens)
- `avgdl` = average document length across corpus
- `IDF(qi)` = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1), where N = total docs, n(qi) = docs containing qi

### Parameter Tuning

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `k1` | 1.2-1.5 | 0.0-3.0 | Controls term frequency saturation. Lower = faster saturation (good for short docs). Higher = more sensitive to repeated terms. |
| `b` | 0.75 | 0.0-1.0 | Controls length normalization. 0 = no normalization. 1 = full normalization. |

**For brain.py (short documents, metadata-heavy):**
- `k1 = 0.9-1.2` -- Lower than default because fat index entries are short (5-15 lines). Term repetition is already rare, so saturation should kick in early.
- `b = 0.3-0.5` -- Lower than default because document length variation is small (all entries are similar size). Full normalization would over-penalize slightly longer summaries.

**Tuning guidance:**
- Default k1=1.2, b=0.75 works well for most corpora -- start here and only tune if results are poor.
- For short news-style documents: lower k1 (0.5-1.0) because repeated terms in short docs are highly significant.
- For metadata/tags: k1 near 0 treats any presence of a term as equally important (boolean-like matching).
- Practical tuning method: create 10-20 "golden queries" with expected top-3 results, run grid search over k1/b, pick values that maximize precision@3.

---

## 2. Python Library Comparison

### rank-bm25 (Current choice in brain.py)

- **PyPI:** `rank-bm25` | **Stars:** ~1K | **Status:** Low maintenance but stable
- **Dependencies:** None (pure Python)
- **API:** `BM25Okapi(corpus)` where corpus = list of token lists
- **Variants:** BM25Okapi (standard), BM25L (TF normalization), BM25Plus (lower bound on TF)
- **Persistence:** None built-in (must pickle the object)
- **Performance:** Adequate for <1000 docs. Slow for large corpora (pure Python loops).
- **Pros:** Zero dependencies, simple API, already integrated in brain.py.
- **Cons:** No text preprocessing, no field support, no persistence, no stemming. Low maintenance.
- **Verdict for brain.py:** **Good enough for current scale (37 files).** Already integrated. Upgrade when corpus exceeds ~200 entries or when field boosting becomes critical.

```python
from rank_bm25 import BM25Okapi

corpus = [doc.split() for doc in documents]
bm25 = BM25Okapi(corpus, k1=1.0, b=0.5)  # Tuned for short docs
scores = bm25.get_scores(query.split())
top_n = bm25.get_top_n(query.split(), documents, n=5)
```

### bm25s (Performance upgrade path)

- **PyPI:** `bm25s` | **Stars:** ~2K | **Status:** Active (2024-2025)
- **Dependencies:** numpy, scipy
- **Performance:** Up to 500x faster than rank-bm25 (eager sparse matrix computation).
- **Persistence:** Built-in save/load to directory. HuggingFace Hub integration.
- **Stemming:** Optional built-in stemmer support.
- **Pros:** Fast, persistent index, active maintenance, good documentation.
- **Cons:** Heavier dependencies (numpy/scipy). No native field boosting.
- **Verdict for brain.py:** **Best upgrade from rank-bm25.** When performance or index persistence matters. The numpy/scipy dependency is acceptable since they are widely available.

```python
import bm25s

corpus = ["doc one text", "doc two text"]
retriever = bm25s.BM25()
retriever.index(bm25s.tokenize(corpus))

# Save/load persistent index
retriever.save("brain_index/")
retriever = bm25s.BM25.load("brain_index/")

# Query
results, scores = retriever.retrieve(bm25s.tokenize(["search query"]), k=5)
```

### SQLite FTS5 (Full-featured upgrade path)

- **PyPI:** Built into Python's `sqlite3` module
- **Dependencies:** None (SQLite ships with Python)
- **Performance:** Very fast (C implementation, inverted index on disk)
- **Persistence:** Native (it IS a database)
- **Field support:** Native column weights in `bm25()` function
- **Pros:** Zero dependencies, persistent, field boosting, prefix search, phrase queries, incremental updates, battle-tested. k1/b hardcoded at 1.2/0.75.
- **Cons:** k1 and b are NOT configurable (hardcoded in SQLite source). Schema requires upfront column definition. More boilerplate than rank-bm25.
- **Verdict for brain.py:** **Best option when field boosting is critical.** Zero extra dependencies. Natural persistence. The inability to tune k1/b is acceptable given defaults work well for most corpora.

```python
import sqlite3

conn = sqlite3.connect("brain_search.db")
conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS brain_index USING fts5(
        id,
        tags,
        summary,
        file_type,
        known_issues,
        tokenize='porter unicode61'
    )
""")

# Insert entries
conn.execute(
    "INSERT INTO brain_index(id, tags, summary, file_type, known_issues) VALUES (?,?,?,?,?)",
    (entry_id, tags, summary, file_type, known_issues)
)

# Search with field weights: id=4.0, tags=5.0, summary=1.0, file_type=0.5, known_issues=0.5
results = conn.execute("""
    SELECT id, tags, summary,
           bm25(brain_index, 4.0, 5.0, 1.0, 0.5, 0.5) as score
    FROM brain_index
    WHERE brain_index MATCH ?
    ORDER BY score
    LIMIT 10
""", (query,)).fetchall()
# Note: bm25() returns NEGATIVE scores (lower = better match), so ORDER BY score (ascending)
```

### Whoosh / Whoosh-Reloaded

- **PyPI:** `whoosh-reloaded` (fork of abandoned `whoosh`)
- **Status:** Community-maintained fork. Original Whoosh abandoned (~2020).
- **Features:** Full search engine -- schema, analyzers, BM25F (field-weighted BM25), spelling, highlighting.
- **Pros:** Rich feature set, BM25F built-in, pure Python.
- **Cons:** Heavier than needed for 37 files. File-based index adds complexity. Original abandoned, fork maintenance uncertain.
- **Verdict for brain.py:** **Overkill for current scale.** Consider only if brain.py needs highlighting, spelling correction, or complex query parsing. SQLite FTS5 covers the common cases with less complexity.

### tantivy-py

- **PyPI:** `tantivy` | **Status:** Active (Rust bindings)
- **Performance:** 20x faster indexing than Whoosh. 0.8ms query latency.
- **Pros:** Extremely fast, Lucene-quality features, active Rust backend.
- **Cons:** Rust binary dependency (platform-specific wheels). Heavy for a CLI tool. Some features undocumented.
- **Verdict for brain.py:** **Excessive for current scale.** Consider for brain MCP server if query latency becomes critical.

### lunr.py

- **Status:** Port of lunr.js to Python. Low maintenance.
- **Verdict:** Not recommended. Limited features, poor ecosystem.

### Summary Decision Matrix

| Library | Dependencies | Field Boost | Persistence | Tunable k1/b | Best For |
|---------|-------------|-------------|-------------|---------------|----------|
| rank-bm25 | None | Manual (repeat fields) | No | Yes | Prototyping, <100 docs |
| bm25s | numpy, scipy | Manual | Yes (save/load) | Yes | Performance, persistence |
| SQLite FTS5 | None (stdlib) | Native columns | Yes (database) | No (1.2/0.75) | Field boosting, persistence, zero deps |
| Whoosh-Reloaded | None (pure Python) | BM25F native | Yes (file index) | Yes | Complex queries, highlighting |
| tantivy-py | Rust binary | Native | Yes (file index) | Yes | High-performance production |

**Recommendation for brain.py evolution:**
1. **Now (37 files):** Keep rank-bm25. Already working. Focus on improving preprocessing and structural boosts (which brain.py already does well).
2. **Next (50-100 files):** Migrate to SQLite FTS5 for native field weights and persistence. Zero new dependencies.
3. **Later (100+ files or MCP server):** Consider bm25s for speed, or tantivy-py for the MCP server backend.

---

## 3. BM25 for Markdown / Knowledge Bases

### Preprocessing Pipeline

Markdown files need preprocessing before BM25 indexing:

```python
import re

def preprocess_markdown(text: str) -> dict:
    """Extract structured fields from a brain markdown file."""
    fields = {}

    # Extract YAML-style frontmatter comments
    fields["tags"] = extract_meta(text, "tags")
    fields["links"] = extract_meta(text, "links")

    # Extract title (first # heading)
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    fields["title"] = title_match.group(1) if title_match else ""

    # Strip markdown syntax for body
    body = text
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)  # HTML comments
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.MULTILINE)  # Headings
    body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)  # Bold
    body = re.sub(r"\*(.+?)\*", r"\1", body)  # Italic
    body = re.sub(r"`{1,3}[^`]*`{1,3}", "", body, flags=re.DOTALL)  # Code blocks
    body = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", body)  # Links
    body = re.sub(r"^\s*[-*+]\s+", "", body, flags=re.MULTILINE)  # List markers
    fields["body"] = body.strip()

    return fields

def extract_meta(text: str, field: str) -> str:
    match = re.search(rf"<!--\s*{field}:\s*(.+?)\s*-->", text)
    return match.group(1) if match else ""
```

### Document-Level vs Section-Level Indexing

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Document-level** | Simple, one entry per file | Loses section granularity | <100 files, fat index entries |
| **Section-level** (split on ##) | Better precision | More entries, more complex | Long SPEC/CODE files |
| **Fat-index-level** (current) | Cheapest, already parsed | Limited to summary text | Current brain.py approach |

**Recommendation for brain.py:** Stay with fat-index-level indexing. The fat index entries are already curated summaries optimized for search relevance. Section-level indexing of full files adds complexity without proportional benefit at 37 files. Revisit at 100+ files.

### Field Boosting Strategy

For brain files, fields have different signal quality:

| Field | Suggested Weight | Rationale |
|-------|-----------------|-----------|
| Tags | 5.0x | Curated metadata, highest signal density |
| ID | 4.0x | Direct reference lookup (e.g., "LEARN-008") |
| Title | 3.0x | Human-curated summary of content |
| Summary | 1.0x (base) | Bulk content, already curated in fat index |
| Type | 0.5x | Low-cardinality (only 6 values) |
| Known issues | 0.5x | Useful for finding gaps, not primary content |

**Brain.py already implements this** via the `entry_to_corpus_doc()` function which repeats tags 3x and ID 2x. This is a workable approximation of field boosting when using rank-bm25 (which lacks native field support). SQLite FTS5 would make this cleaner with native column weights.

---

## 4. Hybrid Search Architecture

### When Hybrid Beats Pure BM25

For a corpus of 30-200 markdown files:
- **BM25 alone is sufficient** when queries use the same vocabulary as documents (which is likely when the user writes the documents and queries).
- **Vector search adds value** when queries are paraphrased, conceptual, or use different terminology than the stored knowledge (e.g., searching "how to save context" when the document says "SESSION-HANDOFF").
- **Hybrid outperforms both** when queries mix exact terms and conceptual intent.

**For brain.py at current scale:** BM25 alone with good preprocessing and structural boosts (tags, links) is likely sufficient. The user and the LLM both know the brain's vocabulary. Add vector search when the corpus grows or when cross-brain search is needed (different brains may use different terminology).

### Reciprocal Rank Fusion (RRF)

RRF combines results from multiple retrieval methods using only rank positions (not raw scores), making it robust to different score distributions.

**Formula:**
```
RRF_score(d) = SUM_r [ 1 / (k + rank_r(d)) ]
```
Where `k = 60` (empirically optimal constant from the original Cormack et al. paper) and `rank_r(d)` is the rank of document d in retriever r (1-indexed).

**Python implementation:**

```python
def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],  # Each list = doc IDs in rank order
    k: int = 60
) -> list[tuple[str, float]]:
    """Combine multiple ranked lists using RRF.

    Args:
        ranked_lists: List of ranked result lists. Each inner list contains
                      document IDs ordered by relevance (best first).
        k: Ranking constant. k=60 is standard. Higher k dampens the
           influence of top-ranked documents.

    Returns:
        List of (doc_id, rrf_score) tuples sorted by score descending.
    """
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# Usage example: combining BM25 and vector search results
bm25_results = ["LEARN-008", "LEARN-019", "RULE-001", "LEARN-005"]
vector_results = ["LEARN-005", "LEARN-008", "LEARN-006", "SPEC-000"]

fused = reciprocal_rank_fusion([bm25_results, vector_results])
# LEARN-008 and LEARN-005 will score highest (appear in both lists)
```

**Key properties of RRF:**
- No score normalization needed -- works purely on rank positions.
- Documents appearing in multiple lists get boosted naturally.
- k=60 is the standard; lower k gives more weight to top ranks.
- Handles partial results gracefully (a doc missing from one list just gets no score from that list).

### Weighted Score Blending (Alternative to RRF)

When you have calibrated scores (same scale), weighted blending can be more precise:

```python
def weighted_blend(
    bm25_scores: dict[str, float],
    vector_scores: dict[str, float],
    alpha: float = 0.7  # BM25 weight; (1-alpha) = vector weight
) -> list[tuple[str, float]]:
    """Blend BM25 and vector scores with normalization."""
    # Min-max normalize each score set
    def normalize(scores):
        vals = list(scores.values())
        if not vals or max(vals) == min(vals):
            return {k: 0.5 for k in scores}
        lo, hi = min(vals), max(vals)
        return {k: (v - lo) / (hi - lo) for k, v in scores.items()}

    norm_bm25 = normalize(bm25_scores)
    norm_vec = normalize(vector_scores)

    all_docs = set(norm_bm25) | set(norm_vec)
    blended = {}
    for doc in all_docs:
        blended[doc] = (
            alpha * norm_bm25.get(doc, 0.0) +
            (1 - alpha) * norm_vec.get(doc, 0.0)
        )
    return sorted(blended.items(), key=lambda x: x[1], reverse=True)
```

**When to use which:**
- **RRF** -- Default choice. Simpler, more robust, no tuning needed.
- **Weighted blending** -- When you have confidence in score calibration and want to tune the BM25/vector balance.

### Minimal Vector Search Options

If adding vector search to brain.py:

| Option | Install Size | Dependencies | Embedding Model | Quality |
|--------|-------------|-------------|-----------------|---------|
| **fastembed** | ~50MB + model | onnxruntime | BAAI/bge-small (default), quantized ONNX | Good, fast on CPU |
| **sentence-transformers** | ~500MB + model | torch, transformers | all-MiniLM-L6-v2 (23M params) | Best quality |
| **sqlite-vec** | ~2MB | None (C extension) | BYO embeddings | Storage only (no model) |

**Recommended stack for brain.py vector search (if/when needed):**
1. **fastembed** for embedding generation -- lightweight, ONNX-based, no PyTorch.
2. **sqlite-vec** for vector storage and search -- pure C extension, runs anywhere SQLite runs, brute-force search (fine for <1000 docs).
3. Combined with SQLite FTS5 in the same database for a unified BM25+vector search backend.

```python
# Hypothetical hybrid search with SQLite FTS5 + sqlite-vec
import sqlite3
# import sqlite_vec  # pip install sqlite-vec

conn = sqlite3.connect("brain_search.db")
# conn.enable_load_extension(True)
# sqlite_vec.load(conn)

# FTS5 table for BM25
conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS brain_fts USING fts5(
        id, tags, summary, tokenize='porter unicode61'
    )
""")

# Vector table for semantic search
# conn.execute("""
#     CREATE VIRTUAL TABLE IF NOT EXISTS brain_vec USING vec0(
#         id TEXT PRIMARY KEY,
#         embedding float[384]  -- dimension of all-MiniLM-L6-v2
#     )
# """)

# Query: run both, fuse with RRF
# bm25_results = fts5_search(query)
# vector_results = vec_search(embed(query))
# final = reciprocal_rank_fusion([bm25_results, vector_results])
```

---

## 5. Query Expansion and Reranking

### Query Expansion Techniques

| Technique | How It Works | Value for brain.py |
|-----------|-------------|-------------------|
| **Synonym expansion** | Add known synonyms to query | Low -- vocabulary is controlled |
| **Pseudo-relevance feedback (PRF)** | Take top-k terms from top-N results, add to query | Medium -- works well for BM25, easy to implement |
| **HyDE (Hypothetical Document Embeddings)** | LLM generates hypothetical answer, embed that | High -- but requires LLM call (expensive for CLI) |
| **Multi-query** | LLM generates 3-5 query variants | High -- but requires LLM call |

**Pseudo-relevance feedback implementation:**

```python
def expand_query_prf(
    bm25,
    entries: list[dict],
    query_tokens: list[str],
    top_n: int = 3,
    expansion_terms: int = 5
) -> list[str]:
    """Expand query using top terms from top-N results (pseudo-relevance feedback).

    Run BM25 once with the original query, take the top-N results,
    extract their most frequent terms (excluding original query terms),
    and append the best expansion terms to the query for a second pass.
    """
    scores = bm25.get_scores(query_tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]

    # Collect terms from top results
    from collections import Counter
    term_freq = Counter()
    for idx in top_indices:
        doc_tokens = entry_to_corpus_doc(entries[idx])
        term_freq.update(doc_tokens)

    # Remove original query terms and very common terms
    for qt in query_tokens:
        term_freq.pop(qt, None)

    # Take top expansion terms
    expansion = [term for term, _ in term_freq.most_common(expansion_terms)]
    return query_tokens + expansion
```

### Reranking

**Cross-encoder reranking** scores each (query, document) pair jointly, producing much more accurate relevance scores than BM25 alone. However, it is O(n) in the number of candidates (each requires a model forward pass).

**Lightweight options:**

| Model | Size | Latency (10 docs) | Quality |
|-------|------|-------------------|---------|
| FlashRank Nano | ~4MB | ~10ms | Acceptable |
| FlashRank Small (ms-marco-MiniLM-L-12-v2) | ~34MB | ~50ms | Good |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | ~80MB | ~100ms | Best (most popular) |

**When reranking is worth the cost for brain.py:**
- At 37 files, BM25 + structural boosts already produces good results. Reranking adds latency for marginal gain.
- At 100+ files, reranking the top 20 BM25 results could significantly improve precision.
- For the MCP server (where query quality directly affects LLM output), reranking is worth considering.

```python
# FlashRank example (lightest option)
# pip install FlashRank
from flashrank import Ranker, RerankRequest

ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")

# After BM25 retrieves top 20 candidates
passages = [{"id": e["id"], "text": e.get("summary", "")} for _, e in bm25_top_20]
request = RerankRequest(query="search terms", passages=passages)
reranked = ranker.rerank(request)
```

---

## 6. Implementation Patterns for Small Corpora (30-200 docs)

### When BM25 Alone Is Sufficient

BM25 alone is sufficient when:
- Users and documents share vocabulary (brain authors are also brain searchers).
- Queries are keyword-oriented ("hooks configuration", "BM25 search").
- The corpus is small enough that precision@3 naturally covers most relevant docs.
- Fat index entries are well-curated (our case -- entries are written to be searchable).

**This describes the current brain.py use case.** BM25 + structural boosts (tags, ID matching, link propagation) that brain.py already implements is a strong baseline.

### When to Add Vector Search

Add vector search when:
- Cross-brain search is needed (different brains use different terminology).
- Users search conceptually ("how to preserve state between sessions" vs the actual term "SESSION-HANDOFF").
- The corpus grows beyond what a single user can mentally map (~100+ files).
- An MCP server makes search quality directly impact LLM reasoning.

### Incremental Indexing

For brain.py, the index should update incrementally (not rebuild from scratch):

```python
import json
import hashlib

INDEX_CACHE = ".brain-search-cache.json"

def load_cached_index(brain_root):
    cache_path = brain_root / INDEX_CACHE
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    return {"entries_hash": None, "index_data": None}

def needs_reindex(brain_root, current_entries):
    """Check if index needs rebuilding based on content hash."""
    entries_str = json.dumps([e.get("raw", "") for e in current_entries], sort_keys=True)
    current_hash = hashlib.sha256(entries_str.encode()).hexdigest()

    cache = load_cached_index(brain_root)
    return cache.get("entries_hash") != current_hash, current_hash
```

### Index Persistence Options

| Method | Size | Load Time | Dependencies | Best For |
|--------|------|-----------|-------------|----------|
| **Pickle** | ~10KB | ~1ms | None | rank-bm25 objects |
| **JSON** | ~5KB | ~1ms | None | Fat index cache |
| **SQLite** | ~50KB | ~2ms | None (stdlib) | FTS5 + metadata |
| **bm25s save/load** | ~20KB | ~5ms | numpy, scipy | bm25s index |

**Recommendation:** SQLite is the natural persistence layer for brain.py. It can store both the FTS5 index and metadata in a single file, supports incremental updates, and requires zero extra dependencies.

---

## 7. Recommended Implementation Roadmap for brain.py

### Phase 1: Improve Current BM25 (Low effort, immediate)

Changes to the existing rank-bm25 implementation:

1. **Add stemming to tokenizer** -- Use a simple Porter stemmer (or just suffix stripping) to match "searching" with "search".
2. **Add stopword removal** -- Remove common English words from both corpus and queries.
3. **Tune k1 and b** -- Set k1=1.0, b=0.4 for the fat-index corpus (short, similar-length documents).
4. **Improve tokenizer** -- Handle hyphenated terms (BM25 -> bm25, session-handoff -> session handoff).

```python
# Improved tokenizer for brain.py
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "and", "but", "or",
    "not", "no", "nor", "so", "yet", "both", "each", "this", "that",
    "these", "those", "it", "its", "they", "them", "their", "we", "our",
    "you", "your", "he", "she", "his", "her", "which", "what", "when",
    "where", "who", "whom", "how", "all", "any", "some", "none", "if",
    "then", "than", "too", "very", "just", "also", "about", "up", "out",
}

def tokenize(text: str) -> list[str]:
    """Tokenize with stopword removal and hyphen expansion."""
    tokens = re.findall(r"[a-z0-9][-a-z0-9]*", text.lower())
    # Split hyphenated terms: "session-handoff" -> ["session", "handoff", "session-handoff"]
    expanded = []
    for t in tokens:
        expanded.append(t)
        if "-" in t:
            expanded.extend(t.split("-"))
    # Remove stopwords
    return [t for t in expanded if t not in STOPWORDS and len(t) > 1]
```

### Phase 2: Migrate to SQLite FTS5 (Medium effort, high value)

Replace rank-bm25 with SQLite FTS5 for native field boosting and persistence:

1. Create `brain_search.db` alongside INDEX-MASTER.md.
2. Parse fat index entries into structured fields (id, tags, summary, type, known_issues).
3. Use FTS5 `bm25()` with column weights for field boosting.
4. Keep the structural boosts (exact tag match, ID match, link propagation) as a post-FTS5 scoring layer.
5. Rebuild index only when INDEX-MASTER.md changes (check file mtime or content hash).

**Key implementation detail:** FTS5 `bm25()` returns negative scores where lower (more negative) is better. Either negate for display or use `ORDER BY score ASC`.

### Phase 3: Add Hybrid Search (High effort, future)

Only pursue when the corpus exceeds ~100 files or an MCP server is built:

1. Add fastembed for lightweight embedding generation.
2. Store vectors in sqlite-vec alongside FTS5 in the same database.
3. Combine BM25 and vector results with RRF (k=60).
4. Consider FlashRank reranking for the MCP server path.

---

## 8. QMD Patterns Worth Adopting

From LEARN-023 (QMD analysis), several patterns are directly applicable:

1. **Smart signal detection** -- If BM25 score of top result is highly confident (large gap between #1 and #2), skip query expansion. This saves computation.
2. **Position-aware score blending** -- Do not let a reranker completely override a high-confidence BM25 result. Blend scores with position awareness.
3. **Content-addressable storage** -- SHA-256 hash of content (brain.py already has `.content-hashes.json`). Use for cache invalidation.

---

## 9. Key Takeaways

1. **rank-bm25 is adequate now.** The current brain.py implementation with structural boosts and link propagation is a solid baseline for 37 files.
2. **SQLite FTS5 is the best next step.** Zero new dependencies, native field boosting, persistence, and incremental updates. This is the clear Phase 2 target.
3. **Vector search is premature for current scale.** The brain author and brain searcher share vocabulary. Add vectors when cross-brain search or MCP server is built.
4. **RRF over weighted blending.** When hybrid search is added, use RRF (simpler, more robust, no score calibration needed).
5. **Reranking is premature.** At 37 files, BM25 + structural boosts is sufficient. Consider FlashRank at 100+ files or for MCP server.
6. **Improve preprocessing first.** Stopwords, stemming, and hyphenated term handling will improve search quality more than switching libraries.
7. **Pseudo-relevance feedback is the cheapest query expansion.** No LLM call needed, easy to implement, works well with BM25.
8. **k1=1.0, b=0.4 are reasonable starting points** for the fat-index corpus (short, uniform-length documents).
