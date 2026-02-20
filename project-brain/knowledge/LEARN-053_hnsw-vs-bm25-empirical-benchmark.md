# LEARN-053 — HNSW vs BM25 Empirical Benchmark at Brain-Scale
<!-- type: LEARN -->
<!-- tags: HNSW,BM25,benchmark,vector-search,ann,approximate-nearest-neighbor,cosine-distance,latency,scale-threshold,claude-flow,competitive-analysis -->
<!-- created: 2026-02-20 -->
<!-- source: https://github.com/ruvnet/claude-flow + local benchmark (benchmarks/bm25_vs_hnsw.py) -->
<!-- links: LEARN-030, LEARN-023, LEARN-044, LEARN-040, LEARN-052, CODE-001 -->

## Discovery
At brain-scale (20-200 documents), BM25 is **41.5x faster** than HNSW per query and **11x faster** to build. HNSW's O(log n) advantage only materializes at N > 1,000 documents. Both achieve identical top-1 recall on keyword-retrievable documents, but BM25 produces more topically coherent secondary results due to exact term matching.

## Context
Analyzed the claude-flow multi-agent orchestration framework (ruvnet/claude-flow) which claims "150x-12,500x faster" HNSW search. Investigated their custom TypeScript HNSW implementation (~600 lines in `v3/@claude-flow/memory/src/hnsw-index.ts`), then built a controlled benchmark comparing BM25 vs HNSW on a 20-document corpus matching our brain's scale and structure.

## Evidence

### claude-flow HNSW Implementation
- **Real**: Custom from-scratch TypeScript HNSW with proper heap-based search, pre-normalized cosine fast path
- **Parameters**: M=16, efConstruction=200, dims=1536, cosine distance default
- **Weaknesses**: Pure JS (no SIMD), string IDs in Maps/Sets, no disk persistence for graph (rebuilt from SQLite on load)
- **Performance claims unsubstantiated**: No comparative benchmark code exists in the repo. "150x-12,500x" is a theoretical O(log n)/O(n) projection for N=10K-100K, not an empirical measurement

### Benchmark Results (N=20, 100 iterations, median times)
| Metric | BM25 | HNSW | Ratio |
|--------|------|------|-------|
| Build time | 0.4 ms | 4.6 ms | HNSW 11x slower |
| Avg search | 5.5 us | 226 us | BM25 41.5x faster |
| Memory | ~23 KB | ~12 KB | HNSW 2x smaller |
| Top-1 recall | 4/4 | 4/4 | Tie |

### Why BM25 Wins at Small N
- Linear scan over inverted index fits in L1 cache at N < 200
- HNSW pays ~4 graph hops with expensive cosine distance computation per hop (64-dim: ~256 FP ops; 1536-dim: ~4608 FP ops per distance call)
- BM25 does exact term matching — no semantic drift on structured queries
- HNSW's logarithmic advantage requires N > 1,000 to overcome per-hop overhead

### Scale Crossover Estimate
| N | BM25 (linear) | HNSW (log) | Winner |
|---|---------------|------------|--------|
| 20 | ~6 us | ~226 us | BM25 |
| 200 | ~60 us | ~300 us | BM25 |
| 1,000 | ~300 us | ~400 us | ~Tie |
| 10,000 | ~3 ms | ~500 us | HNSW |
| 100,000 | ~30 ms | ~600 us | HNSW (50x) |

### Hybrid Architecture (claude-flow)
- SQLite B-tree indexes for exact/prefix queries
- HNSW in-memory for embedding similarity queries
- Dual-write to both backends on store
- ReasoningBank adapter over agentdb npm package (thin wrapper, "RETRIEVE-JUDGE-DISTILL" mostly documentation)
- MemoryGraph with PageRank (30%) + vector similarity (70%) blending

## Impact
- **Validates LEARN-030 and LEARN-040 decision**: BM25-first strategy correct for current brain scale (64 files)
- **Sets threshold**: Consider hybrid BM25+vector at 500+ files, pure HNSW only at 1,000+
- **Informs SPEC-005 migration**: No need to add vector search in brain v2 — BM25 with fat-index is optimal for foreseeable scale
- **claude-flow comparison**: Their hybrid architecture is sound engineering, but performance claims are marketing projections, not benchmarked results

## Action Taken
- Benchmark script deposited at `benchmarks/bm25_vs_hnsw.py` for reproducibility
- Brain continues with BM25 search (CODE-001 MCP server) — no changes needed
- Scale threshold documented: revisit vector search when brain exceeds 500 files
