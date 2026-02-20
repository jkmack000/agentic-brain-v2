# LEARN-024: Context Repositories & Context Engineering Patterns
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: context-repositories, context-engineering, letta, memgpt, anthropic, memory-architecture, git-worktrees, progressive-disclosure, compaction, sub-agents -->
<!-- links: LEARN-002, LEARN-004, LEARN-005, LEARN-011, SPEC-000 -->

## Source
- **Primary:** https://www.letta.com/blog/context-repositories (Letta blog, Feb 2026)
- **Linked:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (Anthropic engineering)
- **Linked:** https://arxiv.org/abs/2310.08560 (MemGPT paper)
- **Linked:** https://docs.letta.com/letta-code (Letta Code docs)
- **Linked:** https://github.com/letta-ai/letta-code (GitHub repo)

## What's New (beyond LEARN-002, LEARN-004, LEARN-005, LEARN-011)

### Letta Context Repositories — Implementation Details

LEARN-002 and LEARN-011 document the convergence finding (Letta uses git-backed, file-based, progressive disclosure). This file adds the specific implementation patterns:

1. **Git worktrees for multi-agent isolation.** Multiple agents clone the memory repo into separate git worktrees, work concurrently in isolation, then merge findings through standard git conflict resolution. Enables "divide-and-conquer" learning strategies. This is a concrete coordination mechanism we lack.

2. **Background reflection processes.** Agents periodically persist important information from working memory into the context repo during long sessions — not just at session end. An automatic, continuous deposit pattern rather than our manual/hook-triggered approach.

3. **Memory defragmentation.** Named as a first-class operation: reorganizing, restructuring, and consolidating accumulated memories for long-horizon use. Our "periodic consolidation" (SPEC-000) is the same concept but less formalized.

4. **`system/` always-loaded directory.** Files in `system/` are automatically injected into every system prompt. Agents manage this directory dynamically as they learn what context is always needed. Maps to our CLAUDE.md + rules, but as a managed directory rather than a single file.

5. **YAML frontmatter on individual files.** Each memory file has its own frontmatter description, similar to skill YAML. Our architecture centralizes this into INDEX-MASTER.md instead — a design choice with trade-offs (see comparison below).

6. **Memory initialization via concurrent subagents.** On first use, multiple subagents explore the codebase in parallel and deposit findings concurrently. Our brain requires manual initial ingestion.

### Anthropic Context Engineering Framework — Deep Patterns

LEARN-004 covers the Landgraf article, LEARN-005 covers official best practices. The Anthropic engineering blog adds these specific frameworks:

7. **Attention budget as n² cost.** Transformer attention creates n² pairwise relationships — every token attends to every other. This makes context growth super-linear in computational cost. Not just "context is finite" but "context is quadratically expensive."

8. **Context rot is a gradient, not a cliff.** Models don't fail at a context limit — they degrade progressively. "Models remain highly capable at longer contexts but may show reduced precision for information retrieval and long-range reasoning." This validates our 80% handoff trigger (INIT.md) and the 15-47% middle-context degradation finding (LEARN-002).

9. **Compaction art: recall vs precision.** Compaction has two failure modes — losing important information (low recall) vs keeping too much noise (low precision). Recommendation: "Start by maximizing recall, then iterate toward precision." Tool result clearing is "one of the safest lightest touch forms of compaction." Brain implication: SESSION-HANDOFF should err toward over-capture.

10. **Sub-agent token economics.** Each subagent may explore using "tens of thousands of tokens" but returns "a condensed, distilled summary of its work (often 1,000-2,000 tokens)." This gives a concrete 10-20x compression ratio for sub-agent delegation. Brain implication: brain-searcher subagent (LEARN-009) should target 1-2K return summaries.

11. **Goldilocks zone for system prompts.** Two failure modes: too brittle (complex if-else logic) and too vague (high-level guidance only). Optimal is "minimal information that fully outlines expected behavior while remaining flexible." Brain implication: CLAUDE.md and INIT.md should be evaluated against this — are we too prescriptive?

12. **Hybrid pre-load + JIT approach.** Claude Code exemplifies the recommended pattern: CLAUDE.md files are dropped into context initially (pre-load) while glob/grep primitives enable just-in-time file retrieval. Our brain already does this — INDEX-MASTER pre-loaded, individual files retrieved on demand.

13. **Structured note-taking as persistent external memory.** The Pokémon example: an agent maintains precise tallies across thousands of game steps, develops maps of explored regions, remembers achievements, and preserves combat strategy notes — enabling multi-hour task continuation after context resets. This is exactly what our brain system does for software engineering.

14. **Bloated tool sets fail.** "If humans cannot definitively identify which tool applies in given situations, agents cannot perform better." Brain implication: brain skills must have minimal functional overlap.

### MemGPT — OS-Inspired Architecture

15. **Interrupt-based control flow.** MemGPT uses OS interrupt mechanisms to coordinate memory access between tiers. Not just "hierarchical memory" but an active interrupt-driven system that triggers memory movement.

16. **Virtual context illusion.** Like virtual memory in an OS (fast RAM + slow disk appear as one address space), MemGPT makes limited context + external storage appear as one large context. The LLM doesn't need to know about the tier boundaries — the system handles paging transparently.

### Letta Code — Persistent Agent Model

17. **Persistent agents vs persistent memory.** Letta Code maintains a single agent identity across sessions. `/clear` resets the conversation thread but memory persists. This is fundamentally different from Claude Code (ephemeral sessions + external memory) and represents a different architectural choice. Our brain system gives Claude Code persistent memory without requiring persistent agent identity.

## Comparison: Our Brain vs These Patterns

| Pattern | Context Repos (Letta) | Anthropic Framework | Our Brain |
|---|---|---|---|
| Storage | Files in git repo | N/A (framework) | `.md` files in `project-brain/` |
| Index/Disclosure | YAML frontmatter per file | JIT retrieval recommended | Centralized fat index (INDEX-MASTER) |
| Always-loaded | `system/` directory | CLAUDE.md pre-load | CLAUDE.md + rules + INIT.md |
| Versioning | Git-native | N/A | Git repo (manual commits) |
| Multi-agent | Git worktrees | Sub-agent architecture | Planned (Prover), not implemented |
| Compaction | Git merge conflict resolution | Summarize + reinitiate | SESSION-HANDOFF + manual |
| Auto-deposit | Background reflection | Structured note-taking | Hook-triggered (PostToolUse) |
| Defragmentation | Named first-class operation | N/A | "Periodic consolidation" (informal) |
| Agent identity | Persistent (survives /clear) | Ephemeral (session-based) | Ephemeral + external brain |
| Init | Concurrent subagent exploration | N/A | Manual ingestion |

## Gap Analysis — What We Don't Have Yet

1. **Git worktree multi-agent isolation** — Needed for Prover. Each specialist brain could be a worktree.
2. **Background reflection / auto-deposit** — Our PostToolUse hook is reactive (file changes), not proactive (periodic reflection on what's important).
3. **Formalized defragmentation** — We have "periodic consolidation" guidance but no structured process, metrics, or triggers.
4. **Concurrent initialization** — Our `brain ingest` is serial. Parallel subagent ingestion would be faster for large sources.
5. **Per-file frontmatter** — Letta puts metadata on each file; we centralize in INDEX-MASTER. Trade-off: our approach saves tokens (one index load vs many file opens) but requires index maintenance discipline.

## Key Takeaway

The ecosystem is converging on our architecture from multiple directions. Letta, Anthropic, and MemGPT all independently validate: file-based storage, progressive disclosure via summaries, git versioning, sub-agent delegation, and structured note-taking. Our specific innovations (centralized fat index, typed file system, session handoff protocol) remain differentiated. The main gaps are in automation (background reflection, concurrent init) and multi-agent coordination (git worktrees).

## Known Issues
- Letta Code is TypeScript-based (98.1%) — implementation details may not transfer directly to our Python-based brain.py
- MemGPT paper is from Oct 2023 — Letta has evolved significantly since then, some paper details may be outdated
- Anthropic framework is general guidance, not a specific implementation — "how" is left to the builder
