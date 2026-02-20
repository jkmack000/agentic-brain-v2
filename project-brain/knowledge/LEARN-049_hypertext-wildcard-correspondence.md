# LEARN-049 — Hypertext-Wildcard Correspondence and Three-Case Pattern Matching
<!-- type: LEARN -->
<!-- tags: hypertext, pattern-matching, wildcard, algorithm, FM-index, dynamic-programming, prefix-free-code, graph-topology, transcriptome, complexity -->
<!-- created: 2026-02-20 -->
<!-- source: Thachuk 2013, "Indexing hypertext", Journal of Discrete Algorithms 18, pp.113-122. DOI: 10.1016/j.jda.2012.10.001. Accessed 2026-02-20. -->
<!-- links: L048, S000, L044, L030, L032 -->

## Discovery
Pattern matching in hypertext is a strict generalization of pattern matching in text with wildcards. Edges in the hypertext correspond to wildcard groups in text — both represent "gaps" where unknown content may appear. This correspondence means improvements to either problem transfer directly to the other. The paper exploits this by adapting wildcard-matching techniques (Lam et al. 2007, Thachuk 2011) to hypertext, yielding the first indexed hypertext search.

## Context
The correspondence is the key theoretical insight of the paper. It's not just an analogy — the multi-edge matching algorithm is literally a generalization of the wildcard DP algorithm, with the added complexity that wildcards have fixed positions in text while edges can connect to any neighbor in a graph.

## Evidence

### The Three-Case Decomposition

**Case (i) — Within a node** (no edge crossed):
Pattern P is a substring of a single node. Solved by standard FM-index backward search on the forward full-text dictionary F. Time: O(m log σ + occ₁ log n). Identical to the wildcard case of matching within a non-wildcard segment.

**Case (ii) — Crossing one edge**:
For each split point i (1 < i ≤ m): P[1..i-1] must be a suffix of some node v_j and P[i..m] must be a prefix of some node v_k, with edge (j,k) ∈ E.
- Preprocessing: backward search in R gives reverse ID range [a,b] for suffix-matching nodes; backward search in F gives forward ID range [c,d] for prefix-matching nodes.
- Query: 2D orthogonal range report on P in rectangle [a,b] × [c,d] finds all valid edge crossings.
- Time: O(m log σ + m log|V|/log log|V| + occ₂ log|V|/log log|V|).
- In wildcard text, this is matching across a single wildcard group — but there the "edge" is predetermined (fixed position), here any edge in E qualifies.

**Case (iii) — Crossing multiple edges** (the hard case):
P[2..m-1] must contain at least one complete node as a substring. Algorithm:
1. Find all γ candidate nodes contained in P[2..m-1] using full-text dictionary matching statistics.
2. For each candidate v_j matching P[i..i+k-1], verify:
   - **Suffix condition**: exists a path from v_j matching P[i+k..m]. Two sub-cases:
     - *Initiation event*: P[i+k..m] is a prefix of a neighbor of v_j (2D range query)
     - *Extension event*: a previously stored sub-path in working array W[i+k] starts at a neighbor of v_j (O(1) adjacency query on Q)
   - **Prefix condition**: exists a node containing P[1..i-1] as suffix with edge to v_j (2D range query on [a,b] × [j,j])
3. Working array W tracks putative sub-paths with back-pointers for path reconstruction.
- Time: O(m log σ + γ² + γ log|V|/log log|V|)
- This generalizes the wildcard DP: in wildcard text, extension events only check the single predecessor position; in hypertext, they must check all neighbors.

### Restricted Cases with Improved Bounds

| Restriction | γ Bound | Counting Time | Key Technique |
|---|---|---|---|
| None | up to O(m|V|) | O(m log σ + γ² + γ log|V|/log log|V|) | DP + adjacency queries |
| Constant degree Δ(G)=O(1) | unchanged | O(m log σ + m log|V|/log log|V| + γ log γ) | Balanced tree for W lookups |
| Quasi-prefix-free nodes | γ = O(m) | O(m log σ + m log|V|/log log|V|) | Pigeonhole: ≤O(1) candidates per suffix |
| Path constraints | unchanged | +O(k log|V|) per path verification | FM-index over serialized valid paths |

### The Open Question
Can unrestricted hypertext be indexed with query time dependent only on m and log(n)? The γ² bottleneck remains unsolved. This is equivalent to asking: can wildcard text be indexed without dependence on the number of wildcard groups matched?

### Matching Statistics as a Tool
For each suffix of P, compute (longest match length q, suffix array range [a,b]) against the full-text dictionary. This is done incrementally in O(m log σ) total — not per-suffix — because extending from P[i..m] to P[i-1..m] reuses the previous SA range. These statistics simultaneously identify: which nodes are substrings of P, which contain P as substring, and the split points for edge crossings.

## Impact

### Relevance to Brain Fat-Index Design
1. **Three-case decomposition maps to brain search**: (i) concept found within a single file, (ii) concept spans two linked files, (iii) concept spans a chain of linked files. Our current BM25 search only handles case (i). Cases (ii) and (iii) would require link-aware search — following edges during retrieval.

2. **Prefix-free property matters**: The strongest results require nodes to be quasi-prefix-free (no node is a prefix of more than O(1) others). In brain terms: if file summaries in the fat index are distinct enough that no summary is a prefix of another, search is most efficient. This validates our practice of writing distinct, specific summaries.

3. **γ² problem parallels brain hub problem**: If many files contain similar content (analogous to many nodes sharing text), search degrades. Our L033 hub analysis (S000 with 33 backlinks) shows concentration — the antidote in both systems is ensuring nodes/files have distinct content.

4. **Path constraints are transcript validation**: The ability to restrict valid paths using an additional FM-index over serialized paths is analogous to validating that a chain of linked files forms a coherent knowledge path — not just arbitrary graph traversal.

5. **2D range queries for link-aware search**: The technique of mapping edges to 2D points and querying rectangles could inspire a brain search enhancement: "find files about X that link to files about Y" as a single indexed operation rather than two searches + intersection.

## Action Taken
Deposited as LEARN-049. Cross-referenced with L048 (index architecture), L044 (brain as context multiplier), L032 (quorum sensing — topology-based retrieval), L030 (BM25 search improvements).
