# LEARN-039: Anthropic Agent SDK — Practical Design Patterns
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- source: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk -->
<!-- tags: anthropic, agent-sdk, agents, feedback-loop, context-gathering, verification, tool-design, code-generation, evaluation, practical-patterns -->
<!-- links: LEARN-038, LEARN-014, LEARN-010, LEARN-005, LEARN-009 -->

## Why This File Exists
Anthropic's practical guide for building agents with the Claude Agent SDK. Complements LEARN-038 (which agent pattern to use) with HOW to implement agents effectively. Complements LEARN-014 (SDK API reference) with design philosophy and ranked strategies. Core framing: "giving Claude a computer."

## The Agent Feedback Loop

Four-stage cycle (refines LEARN-010's three-phase agentic loop):

1. **Gather Context** — retrieve and filter relevant information
2. **Take Action** — execute tasks using tools
3. **Verify Work** — evaluate own output for correctness
4. **Iterate** — refine based on feedback

The loop runs autonomously after initial human direction. Environmental feedback (tool results, code execution, test output) is the primary signal — not the LLM's own confidence (aligns with LEARN-038).

## Context Gathering Hierarchy (Ranked)

Anthropic recommends this priority order:

| Rank | Method | Mechanism | Tradeoff |
|------|--------|-----------|----------|
| 1 | **Agentic search** | bash commands (grep, tail, find) to selectively load files | Transparent, controllable, start here |
| 2 | **Semantic search** | Vector-based retrieval | Faster but less transparent |
| 3 | **Subagents** | Parallel processing in isolated context windows | Returns summaries, not full contexts |
| 4 | **Compaction** | Auto-summarization of previous messages | Prevents context exhaustion in long sessions |

**Key principle:** File system structure IS context engineering. How you organize files determines what the agent can find via agentic search.

**Brain relevance:** Validates our brain directory structure (typed directories, fat index, predictable naming) as a form of context engineering. Also validates agentic search (grep/glob) as primary, with BM25/vector as secondary — matches our brain.py roadmap (LEARN-030).

## Verification Taxonomy (Ranked)

| Rank | Method | Example | Quality |
|------|--------|---------|---------|
| 1 | **Rules-based** | Linting, type checking, test suites | Most robust, deterministic |
| 2 | **Visual** | Screenshots, rendered output via Playwright MCP | Good for UI, automated |
| 3 | **LLM-as-judge** | Secondary model evaluates output | Fuzzy criteria, latency overhead, least robust |

**Insight:** TypeScript preferred over JavaScript specifically because the type system provides additional feedback layers the agent can use for self-verification.

**Brain relevance:** Maps to our Coder brain validation pipeline (SPEC-002): AST parse + import whitelist (rules-based) → pytest (rules-based) → Freqtrade dry-run (rules-based). We're correctly prioritizing rules-based verification.

## Tool Design Principles

1. **Tool prominence = prioritization** — tools that appear more prominently in the context window get used more by the agent. Position matters.
2. **Tools should reflect primary actions** — design custom tools around the core things you want the agent to do
3. **MCP for standardized integrations** — handles auth automatically (Slack, GitHub, Google Drive, Asana) without custom OAuth

**Brain relevance:** Our brain skills (brain-search, brain-deposit, brain-handoff) ARE the primary tools for brain agents. Their prominence in the skill description budget (2% of context, per LEARN-007) directly affects how much the agent uses them.

## Code Generation as Action Type

Code generation is ideal when outputs need to be:
- **Precise** — exact format control
- **Composable** — combine with other code
- **Reusable** — run repeatedly with same results

Examples: generating Excel/PowerPoint/Word files, data transformations, API integrations.

**Principle:** Code-based outputs > natural language outputs for reliability and composability. Aligns with Coder brain's template-fill approach (CODE-001 in coder-brain).

## Agent Evaluation Checklist

Before deploying, verify:
1. Does the agent have **sufficient information access** for the task?
2. Does it have **appropriate tools** for when things fail?
3. Can it find **creative alternatives** for error scenarios?
4. Do you have **representative test sets** for programmatic evaluation?

## Relationship to Other Brain Files

| File | Covers | This file adds |
|------|--------|----------------|
| LEARN-038 | WHAT pattern to use (5 workflows + agents) | HOW to implement (feedback loop, ranked strategies) |
| LEARN-014 | SDK API reference (methods, options, params) | Design philosophy and practical patterns |
| LEARN-010 | Agentic loop architecture | Ranked context gathering and verification hierarchies |
| LEARN-005 | Verification as #1 lever | Verification taxonomy with 3 ranked methods |

## Known Issues
- WebFetch returned summarized content — full code examples from the article not captured
- Article is practical guidance, not API spec — may evolve as SDK matures
- "Giving Claude a computer" framing is philosophical, not prescriptive
