# LEARN-032 — Quorum Sensing Framework for LLM Knowledge Management
<!-- type: LEARN -->
<!-- tags: quorum-sensing, knowledge-management, biological-analogy, framework, indexing, contradictions, decay, consolidation, brain-architecture -->
<!-- created: 2026-02-17 -->
<!-- source: Creative exploration session — biological quorum sensing mapped to LLM memory systems, with Grok comparison and iterative Q&A refinement -->
<!-- links: SPEC-000, SPEC-003, LEARN-002, LEARN-003, LEARN-011, LEARN-031 -->

## Discovery

Bacterial quorum sensing — where organisms coordinate behavior through signal molecule accumulation — maps precisely to the problem of LLM knowledge management at scale. Seven rules derived from this biological analogy create a framework for making a Project Brain self-organizing rather than manually curated.

## Context

Explored during a research + design session comparing how biological systems manage distributed knowledge without central coordination. A parallel Grok session explored the same problem space, revealing convergent conclusions on signal emission and contradiction handling, but divergent approaches on decay (Grok favored temporal, we chose topological).

## The Seven Rules

### Rule 1: Every Packet Must Emit Signal
Every brain file must have a fat index entry in INDEX-MASTER.md. A file without an index entry is invisible to the system — it exists but cannot be found. The fat index IS the signal.

### Rule 2: Maximize Binding Sites
Each deposit must create minimum 3 links: forward links to related files, tags for categorical discovery, and backlinks (referenced files should note what references them). Links are how knowledge finds other knowledge. Isolated files decay; connected files compound.

### Rule 3: Declare Open Questions as Chemoattractant Gradients
Every deposit must include a "what this doesn't answer" field. Open questions are aggregated in an OPEN QUESTIONS section in INDEX-MASTER.md. These gradients tell future sessions where to spend tokens — they attract research toward gaps rather than already-covered ground.

### Rule 4: Deposit Contradictions, Don't Resolve Prematurely
When sources disagree, deposit both sides. Tensions have three states:
- **OPEN** — accumulating evidence from both sides
- **BLOCKING** — on critical path, triggers dedicated research
- **RESOLVED** — one side won through asymmetric weight of evidence

Resolution is earned through adversarial evidence accumulation, not premature consolidation. The losing side is retired with full provenance ("we used to think X because A,B but Y proved correct because C,D,E,F,G"). BLOCKING tensions are research triggers — the system tells you where to focus.

### Rule 5: Consolidate at Cluster Quorum, Not Arbitrary Count
Synthesis is not dedup. Don't merge files just because the count hits 20-30. Instead, consolidate when a cluster of files on the same topic reaches a "mental squeeze point" — when the fat index can no longer summarize the cluster without losing critical distinctions. Synthesis produces new understanding; maintenance dedup just removes redundancy.

### Rule 6: Let Decay Work — Topological, Not Temporal
A file's vitality is measured by its connections, not its age. A 6-month-old file with 5 inbound links is alive. A file deposited yesterday with 0 inbound links is decaying. Decay is never automatic — `/brain-status` flags quiet files (0 inbound links), a human reviews and chooses:
- **Reconnect** — add missing links that should exist
- **Confirm quiet** — mark as reviewed, leave in index
- **Retire** — archive, remove from active index

Files only, never whole brains (dormancy ≠ irrelevance).

### Rule 7: Index Is the Medium
INDEX-MASTER.md gains three new sections beyond the fat index:
- **OPEN QUESTIONS** — aggregated from all files' unanswered questions (Rule 3)
- **TENSIONS** — tracked contradictions with state (Rule 4)
- **CLUSTERS** — groups of related files approaching quorum (Rule 5)

The index becomes the coordination layer — it's not just a lookup table, it's the medium through which knowledge self-organizes.

## Grok Comparison

A parallel Grok session exploring the same problem space revealed:
- **Convergent:** Signal emission requirement, contradiction preservation, cluster-based consolidation
- **Divergent:** Grok favored temporal decay (age-based), we chose topological (connection-based). Topological is superior because relevance is about relationships, not recency — a foundational architecture doc doesn't decay just because it's old.

### Novel Ideas from Grok (Not in Our Framework)
Three extensions acknowledged as valuable but not yet incorporated:
1. **Controlled noise injection** — Random cross-domain queries as creative mutation (analogous to horizontal gene transfer). Could surface unexpected connections between brain clusters that pure link-following would miss.
2. **Evolutionary pressure** — Generate multiple synthesis variants during consolidation and let them compete. Rather than one consolidation pass, run 2-3 and pick the best.
3. **Multi-agent "species" differentiation** — Different agent types responding to different signal types, enabling complex ecosystems. Maps to Prover's specialist brains each having different quorum-sensing behaviors.

### Emergent vs Explicit Quorum Detection
A key design philosophy distinction: Grok built infrastructure that *mimics* quorum sensing (explicit detector + synthesizer agents), while our framework describes conditions that *are* quorum sensing (self-describing packets + emergent detection through the index). A session reading a fat index naturally focuses on dense clusters — that IS quorum detection. The best system uses both: Grok's infrastructure for detection and scaling, our packet design principles for ensuring what accretes is capable of emergence.

## Token Overhead Assessment

Estimated ~10K additional tokens in INDEX-MASTER.md for OPEN QUESTIONS, TENSIONS, and CLUSTERS sections at current scale (~41 files). This is ~5% of current context budget — acceptable. Scales sub-linearly as consolidation reduces open items.

## Sub-Index Workflow Impact

When INDEX-MASTER splits into sub-indexes (at "mental squeeze point", not arbitrary file count):
- INDEX-MASTER becomes directory of cluster summaries (~50-100 lines)
- Each sub-index is 200-300 lines
- One extra hop in search workflow, transparent to skills
- Cross-cluster links preserved in master index

## Safety Strategy

- Git branching for structural experiments
- Tagged commits before irreversible operations (e.g., `pre-quorum-implementation`)
- No parallel brains — git history is the undo buffer

## Impact

This framework transforms the brain from a manually-curated knowledge store into a self-organizing system. Affects:
- INDEX-MASTER.md structure (3 new sections)
- `/brain-deposit` skill (minimum links, open questions required)
- `/brain-status` skill (quiet file detection, cluster detection)
- All future deposits (must comply with 7 rules)
- Consolidation workflow (synthesis vs maintenance distinction)

## Action Taken

- Framework fully designed and refined through iterative Q&A
- Implementation plan deposited as SPEC-003
- Tagged commit at `pre-quorum-implementation` for safety
- Implementation deferred to dedicated work session
