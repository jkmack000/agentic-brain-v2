# LEARN-048 — Succinct Hypertext Index Architecture
<!-- type: LEARN -->
<!-- tags: hypertext, succinct-index, FM-index, BWT, suffix-array, graph-index, pattern-matching, compressed-text-index, orthogonal-range-query, transcriptome, bioinformatics -->
<!-- created: 2026-02-20 -->
<!-- source: Thachuk 2013, "Indexing hypertext", Journal of Discrete Algorithms 18, pp.113-122. DOI: 10.1016/j.jda.2012.10.001. Accessed 2026-02-20. -->
<!-- links: S000, L030, L044, L046, L023 -->

## Discovery
First succinct index for hypertext — text organized as a directed graph where nodes contain text fragments and edges denote valid concatenations. Any path through the graph is a valid string. The index supports exact pattern matching against all paths with space proportional to compressed text + topology, and query time sublinear in hypertext size for restricted cases.

## Context
Researching index types beyond inverted indexes and B-trees. Hypertext indexing generalizes linear text indexing to graph-structured text — directly relevant to our brain architecture where files (nodes) link to other files (edges) forming a knowledge graph.

## Evidence

### Data Structure
The index consists of three component sets:

1. **Text indexes** (two FM-indexes):
   - Forward index F: full-text dictionary of serialized node text T = φv₁φv₂...φv|V|$. Supports substring matching within nodes and prefix matching of suffixes of P.
   - Reverse index R: FM-index of reversed node text T^R. Supports finding which nodes contain a prefix of P as a suffix.
   - Space: 2nH_k(T) + o(log σ) bits (k-th order empirical entropy compressed)

2. **Topology indexes** (stored twice for different query types):
   - 2D orthogonal range structure P: edges mapped to points (reverse_id, forward_id). Answers "which edges connect suffix-matching nodes to prefix-matching nodes?" via rectangle queries in O(log|V| / log log|V|) time.
   - Succinct graph Q (Farzan-Munro): adjacency queries in O(1) time, used for multi-edge extension events.
   - Space: (1+o(1))|E| log|E| + (1+ε)log(n²/m) bits

3. **Auxiliary structures**:
   - Fully indexable dictionary D: bit vector marking node boundaries in T, supports rank/select in O(1) for canonical ID lookup.
   - Permutations Π_{R→F} and Π_{F→C}: map between reverse, forward, and canonical node IDs.
   - Space: 2|V| log|V| + |V| log(n/|V|) bits

### Dual ID System
Nodes have three identifiers:
- **Forward ID**: prefix lexicographic rank (determined from forward FM-index)
- **Reverse ID**: suffix lexicographic rank (determined from reverse FM-index)
- **Canonical ID**: application-specific ordering (e.g., genome position)

The forward/reverse distinction is essential: crossing an edge means one node's suffix matches (reverse ordering) and the next node's prefix matches (forward ordering).

### Total Space (Lemma 6)
2nH_k(T) + o(log σ) + n(2+o(1)) + O(|E| log|E|) bits

### Query Model
Pattern P of length m matched against all paths in hypertext G = (V, E) with total node text length n.

### Write Cost
Construction requires building two FM-indexes + 2D range structure + succinct graph. O(n) time for FM-indexes, O(|E| log|E|) for topology structures.

### Scaling Behavior
- Within-node matching: O(m log σ + occ₁ log n) — same as standard FM-index
- Single-edge crossing: O(m log σ + m log|V|/log log|V|) counting
- Multi-edge crossing: O(m log σ + γ² + γ log|V|/log log|V|) where γ = nodes occurring as substrings of P
- **Key limitation**: γ² term. If many nodes share identical text and appear in P, index becomes slower than brute-force. This is the open problem.

### Space Reduction Options (Section 5)
- Drop Π_{F→C} if canonical IDs not needed
- Drop Q (use P for adjacency at O(log|V|/log log|V|) instead of O(1)) — γ² becomes γ² log|V|/log log|V|
- Replace reverse FM-index with sparse suffix tree: 2nH_k → nH_k + O(|V| log n), but time increases to O(m log n)

## Impact
- **Direct analogy to brain architecture**: brain files = nodes, links = edges, searching for a concept = pattern matching across linked files. The three-case decomposition (within-file / crossing one link / crossing multiple links) maps to brain search scenarios.
- **Validates fat-index approach**: the dual forward/reverse indexing is conceptually similar to our forward links + backlinks in INDEX-MASTER. Both enable different query directions on the same structure.
- **2D range query for topology**: mapping edges to points in a 2D grid and querying rectangles is a powerful technique — could potentially optimize brain search when combining "files about topic X" with "files linked from topic Y".

## Action Taken
Deposited as LEARN-048. Cross-referenced with L044 (brain as context multiplier), L030 (BM25 search), L046 (compressed fat index format), L023 (QMD hybrid search).
