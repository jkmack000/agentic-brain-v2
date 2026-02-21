# LEARN-054 — Tiered Agent Routing: Bypass LLM for Simple Tasks
<!-- type: LEARN -->
<!-- tags: agent-routing,cost-optimization,Q-learning,WebAssembly,tiered-execution,LLM-bypass,claude-flow,multi-agent,token-efficiency -->
<!-- created: 2026-02-21 -->
<!-- source: https://github.com/ruvnet/claude-flow (v3 architecture analysis) -->
<!-- links: LEARN-038, LEARN-027, LEARN-017, LEARN-040, LEARN-053 -->

## Discovery
Agent systems can dramatically reduce costs by routing tasks through tiers that bypass LLM calls entirely for simple operations. claude-flow implements a three-tier model: (1) WebAssembly transforms for simple edits (no LLM), (2) cheaper/smaller models for medium tasks, (3) full Claude for complex coordinated work. A Q-Learning router learns optimal tier assignment from outcomes over time.

## Context
Discovered while analyzing claude-flow's architecture beyond its memory system. Most agent frameworks route everything through the largest available model. claude-flow's tiered approach treats model selection as an optimization problem rather than a fixed choice.

## Evidence
**Three-tier architecture (claude-flow):**
- **Tier 1 — LLM bypass**: WebAssembly-compiled code transforms handle simple edits (rename, reformat, move). Claimed 352x faster than LLM round-trip. Zero token cost.
- **Tier 2 — Cost-optimized**: Medium complexity tasks routed to smaller/cheaper models. Reduces per-query cost ~10-100x vs full model.
- **Tier 3 — Full model**: Complex reasoning, multi-file changes, architectural decisions use full Claude with agent swarm coordination.

**Q-Learning router:**
- Learns task→tier mapping from outcomes (success/failure, quality scores)
- Mixture-of-Experts with 8 expert classifiers for task categorization
- Claims 250% extension of effective Claude Code usage through intelligent routing

**Comparison to existing patterns:**
- Anthropic's routing pattern (LEARN-038) describes static routing by task type
- claude-flow adds learned routing that adapts from outcomes
- Similar to database query optimizers that learn from execution statistics

## Impact
- **Token economics**: If even 30% of agent tasks can bypass LLM calls, that's a 30% cost reduction with near-zero latency for those tasks
- **Pattern for brain**: Could apply tiered approach to brain search — simple ID lookups skip BM25 entirely, keyword queries use BM25, semantic queries (future) use vector search
- **Validates L040 progressive loading**: Same principle — don't load everything when you only need a fraction

## Action Taken
Deposited as research finding. No implementation needed — our brain already does a version of this (MCP search vs direct file read vs full index load). The Q-Learning adaptation component is novel but premature for our scale.
