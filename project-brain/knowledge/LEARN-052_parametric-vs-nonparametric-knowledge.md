# LEARN-052 — Parametric vs Non-Parametric Knowledge: Fine-Tuned LLMs vs Brain Index
<!-- type: LEARN -->
<!-- tags: architecture,fine-tuning,parametric-memory,non-parametric-memory,RAG,knowledge-management,scaling,access-pattern,tradeoffs,cost-analysis,context-window,attention -->
<!-- created: 2026-02-20 -->
<!-- source: Analytical synthesis prompted by user question. Draws on L051 (attention as indexing), L044 (brain vs RAG), L040 (access pattern insight), L021 (LangChain/RAG survey), R005 (auditability). -->
<!-- links: LEARN-051, LEARN-044, LEARN-040, LEARN-021, LEARN-002, SPEC-005, RULE-005 -->

## Discovery

Fine-tuned small LLMs and large LLMs with external knowledge indexes (our brain) represent two fundamentally different indexing strategies: **parametric memory** (knowledge in weights) vs **non-parametric memory** (knowledge in retrievable files). The choice depends on the access pattern, not inherent superiority. The brain wins when knowledge velocity is high, auditability matters, and query volume is low. Fine-tuning wins when knowledge is stable, query volume is high, and the domain is narrow.

## Context

User asked whether small LLMs trained on specific domain knowledge would outperform a large model with agentic brain + indexed domain knowledge. This is the central architectural question the brain exists to answer — it's the parametric vs non-parametric boundary that L044 and S005 hadn't fully addressed.

## Evidence

### The Two Approaches as Index Types

| Dimension | Fine-tuned small LLM | Large LLM + Brain |
|---|---|---|
| **Where knowledge lives** | Model weights (parameters) | External files (context window) |
| **Index type** | Implicit — learned attention patterns | Explicit — fat index + BM25 |
| **Query cost** | O(n²) over fixed n (small context) | O(n²) over variable n (loaded files) |
| **Update cost** | Retrain (hours/days, $$) | Write a markdown file (seconds, free) |
| **Knowledge ceiling** | Frozen at training cutoff | Grows continuously |
| **Retrieval precision** | High for trained distribution, brittle outside it | Depends on index quality |
| **Auditability** | Black box — can't trace provenance | Every fact has source URL, date, link trail |
| **Composability** | Locked to one architecture | Works with any LLM |
| **Multi-domain reasoning** | Limited to trained distribution | Full breadth of base model |

### Where Fine-Tuning Wins

1. **Latency** — No retrieval step. Knowledge already "loaded" in weights. Critical for high-throughput production APIs (thousands of req/sec).
2. **Cost per query** — A 7B model costs ~100x less per token than Opus. Millions of queries against stable knowledge → fine-tuning amortizes fast.
3. **Narrow, stable domains** — Medical coding, legal citation lookup, chip datasheets. Predictable question distribution + infrequent knowledge updates.
4. **Edge deployment** — Single GPU or CPU. No external index infrastructure.

### Where Brain + Large LLM Wins

1. **Knowledge velocity** — Deposit a file, searchable immediately. Fine-tuning: collect examples → format → train → evaluate → deploy = days. Seconds vs days.
2. **Reasoning over structure** — Typed links (extends/contradicts/validates), topological position, tensions, open questions. Fine-tuning flattens graph structure into weight distributions. Can't ask "what contradicts what?" or "trace from zettelkasten to MCP."
3. **Auditability (R005)** — Organized + trackable + provable. Every brain fact has source, date, link trail. Fine-tuned model = black box.
4. **Composability** — Brain works with any LLM. Switch Opus→Sonnet→future model, knowledge transfers. Fine-tuned weights locked to one architecture.
5. **Cross-domain synthesis** — L051 exists because a general LLM saw the structural parallel between transformer attention and information retrieval. A model fine-tuned on indexing theory lacks the breadth.
6. **Small data regimes** — Brain works with 1 file (fat index entry enough for load decision). Fine-tuning needs thousands of examples to generalize.

### The n² Reframing (from L051)

Fine-tuning doesn't eliminate O(n²) attention cost — it fixes n at training time. A 7B model with 4K context pays O(4K²) = 16M ops per query regardless of whether the answer needs 100 or 4000 tokens.

The brain pays O(n²) where n = only what was loaded. Focused query needing one file (~1K tokens): O(1K²) = 1M ops. Broad synthesis (~5K tokens): 25M ops. **Brain pays proportional to relevance; fine-tuned models pay fixed cost regardless.**

### The Access Pattern Decision Framework (extending L040)

L040's core insight: "problem is access pattern, not storage." This extends to the parametric/non-parametric boundary:

| Access Pattern | Best Approach | Why |
|---|---|---|
| Read-heavy, write-rare, narrow domain, high volume | Fine-tune | Amortize training cost over millions of queries |
| Write-heavy, evolving knowledge, cross-domain, auditability needed | Brain + large LLM | Knowledge velocity + provenance + reasoning breadth |
| Stable core + evolving edge | Hybrid | Fine-tune the core, brain the edge (this is what modern RAG does) |

### The Hybrid Reality

Most production systems converge on hybrid: fine-tuned base model + retrieval augmentation. LangChain/LangGraph (L021), Letta (L024), and RAG systems generally all combine parametric and non-parametric. The question isn't either/or — it's where to draw the boundary.

For our project specifically — research that evolves daily, needs cross-domain synthesis, requires provenance, single user — the brain + large LLM wins decisively. The brain's value **increases** with knowledge velocity and **decreases** with query volume.

## Impact

### Architectural validation

This analysis provides the strongest theoretical justification yet for the brain's existence:
- Not just "saves tokens" (L040's framing)
- Not just "hard pre-filter" (L051's framing)
- But: **the brain is the optimal architecture when knowledge changes faster than models can be retrained and auditability is required**

### Implications for Brain v2 (S005)

1. **The brain's competitive advantage is knowledge velocity + structure.** S005's link index, typed relationships, and three-space separation are not just organizational conveniences — they're capabilities that parametric memory fundamentally cannot replicate.
2. **The eviction policy matters more than we thought.** If brain files get evicted/archived poorly, the brain loses its advantage over fine-tuning. The cascading pre-filter must preserve retrieval quality as the brain scales.
3. **Hybrid future:** If the brain grows past ~500 files, consider fine-tuning a small model on the stable core (foundational SPECs, settled LEARNs) while keeping the brain for the evolving edge. This is Open Question territory for Brain v3.

### Connection to existing work

- **L044** argued brain ≠ RAG. This extends it: brain ≠ RAG ≠ fine-tuning — three distinct strategies on the parametric/non-parametric spectrum.
- **L040** said "problem is access pattern." This concretizes it: the access pattern determines where on the parametric/non-parametric spectrum to sit.
- **L051** quantified the n² cost. This adds: fine-tuning doesn't escape n² — it just fixes n.

## Action Taken

Deposited as LEARN-052. Flags hybrid approach (fine-tune stable core + brain evolving edge) as future consideration for Brain v3 at ~500+ files.
