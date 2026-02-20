# LEARN-001 — Semantic Compression as Context Window Extension
<!-- type: LEARN -->
<!-- tags: context-window, compression, semantic-search, ingestion, supermemory, architecture -->
<!-- created: 2026-02-14 -->
<!-- source: https://supermemory.ai/blog/extending-context-windows-in-llms/ -->
<!-- links: SPEC-000 -->

## Discovery
There are two complementary techniques for extending effective LLM context: semantic compression (for static documents) and infinite chat (for dynamic conversations). Semantic compression achieves ~6:1 reduction while retaining 90%+ accuracy on retrieval tasks. This matches our SPEC-000 ingestion compression ratio target independently.

## Context
Researching existing approaches to LLM memory during Phase 0 of Project Brain development. Evaluating whether our fat-indexing approach is redundant with existing tools.

## Evidence

### Semantic Compression Pipeline (for static documents)
Six-stage process reducing documents to ~1/6 original size:
1. **Segmentation** — split into sentence blocks constrained to ~512 tokens (BART tokenizer)
2. **Embedding** — blocks converted to 384-dim MiniLM vectors; cosine similarity builds adjacency matrix
3. **Spectral clustering** — graph eigenstructure detects topic boundaries (preferred over k-means because it finds natural graph splits, not spherical assumptions)
4. **Parallel summarization** — BART-large-cnn generates abstractive summaries (64-256 tokens per cluster, target ~450 tokens per cluster)
5. **Reassembly** — summaries stitched back in original order
6. **LLM prompting** — compressed text injected as system context

Key numbers: 90%+ accuracy on pass-key retrieval past 60K tokens. Batch sizes: encoder=64, summarizer=4.

### Infinite Chat (for dynamic conversations)
Four-stage retrieval pipeline for growing conversation transcripts:
1. Chunk transcript at sentence boundaries
2. Embed chunks and store in searchable index
3. Score by relevance (embedding similarity) + recency (timestamp decay)
4. Retain top-scoring chunks fitting token budget; rebuild prompt

Operates as transparent proxy for OpenAI-compatible APIs. Adds milliseconds of latency; claims 50%+ token reduction in long chats.

## Impact
- **brain.py `ingest` command:** The semantic compression pipeline (segmentation → embedding → clustering → summarization) is a candidate architecture for automating the ingestion workflow. Currently `ingest` creates stub files for manual extraction. This pipeline could auto-extract knowledge.
- **Not a replacement for fat indexing:** Compression stuffs more into the window; fat indexing avoids loading content at all. They solve different layers. Compression is useful INSIDE our architecture, not instead of it.
- **Monetization relevance:** SPEC-000 identifies AI-powered auto-summarization as the paid tier. This pipeline is a concrete implementation path for that feature.
- **Infinite Chat is less relevant:** Our SESSION-HANDOFF system solves the cross-session problem differently (structured snapshots vs. vector retrieval of conversation chunks). Their approach is better for chat-heavy workflows; ours is better for knowledge-heavy workflows.

## Action Taken
Documented for future reference. No code changes. Flagged as candidate architecture for `brain ingest` automation in a future phase.
