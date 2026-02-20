# LEARN-027: Multi-Agent Orchestration Patterns for AI/LLM Systems
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: multi-agent, orchestration, choreography, fan-out, fan-in, task-decomposition, aggregation, error-handling, context-management, LangGraph, CrewAI, AutoGen, OpenAI, prover -->
<!-- links: SPEC-001, LEARN-009, LEARN-015, LEARN-026, LEARN-024 -->

## Purpose

Research synthesis of multi-agent orchestration patterns from production frameworks (LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Microsoft Agent Framework, Google ADK). Directly informs Prover's orchestrator brain design.

---

## 1. Fan-Out / Fan-In Patterns

**Core concept:** Scatter-gather — orchestrator dispatches to N agents in parallel, waits, then merges results.

**Dispatch phase:** Initiator sends to all registered agents or dynamically selects. Each agent operates independently with own model, tools, knowledge.

**Aggregation strategies:**
- **Voting/majority-rule** — for classification tasks
- **Weighted merging** — scored recommendations weighted by confidence/expertise
- **LLM-synthesized summary** — when results need reconciliation into coherent narrative
- **Concatenation with dedup** — when agents cover different facets

**LangGraph implementation:**
- Parallel nodes run as a single "superstep"
- State uses **reducers**: `Annotated[list, operator.add]` concatenates lists from parallel nodes
- **Atomic failure**: if one node fails, entire superstep fails (no partial results saved)
- Benchmark: 137x speedup (61.46s sequential → 0.45s parallel)
- `Send()` API for dynamic fan-out (map-reduce pattern)

**Microsoft guidance:** Agents operate independently, no result handoff between them. Anti-pattern: sharing mutable state between concurrent agents.

**Use when:** Tasks are embarrassingly parallel, time-sensitive, ensemble reasoning needed.
**Avoid when:** Agents build on each other's work, no conflict resolution strategy, resource-constrained.

---

## 2. Choreography vs Orchestration

### Orchestration (Centralized Coordinator)
- Central manager controls flow, decides agents, collects results
- **Pro:** Predictable, debuggable, single control point for error handling
- **Con:** Single point of failure, coordinator context bloat, adding agents requires coordinator updates
- **Implementation:** OpenAI Agents SDK "manager pattern"

### Choreography (Peer-to-Peer / Event-Driven)
- Agents coordinate via events or shared state, no central controller
- **Pro:** Adaptive, no bottleneck, each agent owns its context
- **Con:** Harder to trace/debug, risk of infinite loops, coordination protocols must be precise
- **Implementation:** CrewAI Flows with `@listen` decorators

### Hybrid Consensus (Industry Best Practice 2025-2026)
**"Orchestrate via code for determinism, delegate to LLM for flexibility."**
- Code-level orchestration for workflow skeleton
- LLM-level reasoning within individual agents
- Agents propose tasks asynchronously (choreography) + lightweight coordinator manages handoffs (orchestration)

### Framework Positioning
| Framework | Style |
|-----------|-------|
| LangGraph | Orchestration (code-defined graph) |
| CrewAI Crews | Choreography (agents decide) |
| CrewAI Flows | Hybrid (structured events + agent autonomy) |
| AutoGen | Choreography (conversational group chat) |
| OpenAI Agents SDK | Orchestration (manager) or choreography (handoffs) |
| Microsoft Agent Framework | Orchestration (declarative, all 5 patterns) |

---

## 3. Task Decomposition Strategies

### Strategy 1: Role-Based (CrewAI)
Agents assigned roles (researcher, editor, analyst) with goals, backstory, scoped tools. Tasks assigned to specific roles. Sequential or hierarchical process.

### Strategy 2: Graph-Based (LangGraph)
Workflow as directed graph. Nodes = agents/steps. Edges = data flow (can be conditional). Decomposition at design time. Conditional edges enable dynamic routing.

### Strategy 3: Dynamic Task Ledger (Microsoft Magentic)
For open-ended problems: manager builds dynamic task list, consults specialists, iterates/backtracks. Most flexible but slowest and hardest to cost-predict.

### Strategy 4: Conversation-Based (AutoGen)
Group chat with turn management. Agents discuss and refine until consensus. Less predictable but good for brainstorming.

### Complexity Hierarchy (Microsoft)
Use the simplest level that works:
1. **Direct model call** — classification, summarization
2. **Single agent with tools** — most enterprise use cases (right default)
3. **Multi-agent orchestration** — cross-domain, security boundaries, parallel specialization

---

## 4. Result Aggregation and Conflict Resolution

Five aggregation strategies: voting, weighted merging, LLM synthesis, concatenation+dedup, dedicated conflict resolution agent.

**Conflict handling patterns:**
1. **LLM-based debate** — judge agent evaluates evidence quality
2. **Confidence scoring** — weight by confidence, discard low-confidence
3. **Maker-checker loops** — propose→evaluate→revise (ALWAYS set iteration cap with fallback)
4. **Quorum-based** — accept only if threshold met (e.g., 3/5 agree)
5. **Structured output validation** — schema check before aggregation

**Critical finding:** Multi-agent LLM systems fail at **41-86.7% rates** in production when coordination protocols are unstructured. Every aggregation needs explicit handling for irreconcilable outputs.

---

## 5. Production Framework Details

### OpenAI Agents SDK (successor to Swarm)
- Two primitives: Agents + Handoffs (tool calls that transfer control)
- Context variables: dict passed through `Runner.run()`, injected into instructions
- Guardrails: run in parallel with execution (not before)
- Manager pattern: central LLM delegates via tool calls
- Decentralized handoff: system prompt swaps, chat history persists

### LangGraph
- Stateful directed graphs with checkpointing
- Fan-out: multiple edges = parallel superstep, atomic failure
- Reducers for concurrent merge (e.g., `operator.add` on lists)
- Human-in-the-loop via `interrupt()`, subgraphs for nested decomposition

### CrewAI
- Crews (autonomous teams): role/goal/backstory per agent, sequential or hierarchical
- Flows (event-driven): `@start`, `@listen`, `@router`, `and_()` (fan-in), `or_()` (any trigger)
- Built-in memory: short-term, long-term, entity

### AutoGen
- GroupChat + GroupChatManager with speaker selection (round_robin, random, auto)
- Allowed/disallowed speaker transitions constrain handoff graph
- Context grows unboundedly — manual management required
- Best for exploratory/brainstorming, not structured pipelines

### Microsoft Agent Framework
Five built-in patterns: sequential, concurrent, group chat, handoff, magentic. All support human-in-the-loop. Declarative (YAML/JSON) or code (C#/Python).

### Google ADK
Sequential, parallel, delegation, handoff, loop patterns natively. Built-in session management.

---

## 6. Error Handling Patterns

1. **Retry with exponential backoff + jitter** — transient failures
2. **Circuit breakers** — 40%+ failure in 60s → trip to fallback (Salesforce Agentforce pattern)
3. **Failure classification** — transient (retry) vs permanent (escalate) vs degraded quality (retry with different prompt/model)
4. **Graceful degradation** — partial results + quality warning, cached defaults, human escalation
5. **Output validation before propagation** — schema, confidence, relevance, safety checks
6. **Timeout management** — per-agent budgets, proceed without stragglers
7. **Checkpointing** — save state at each node, resume from last checkpoint on failure

**Key statistic:** 41-86.7% failure rates caused by: spec ambiguity, unstructured coordination, context pollution, infinite loops, tool misuse, cascading bad output.

---

## 7. Context Management Strategies

### Strategy 1: Context Isolation (Manus — highest impact)
"Share memory by communicating, don't communicate by sharing memory." Assign sub-agents own context windows. Pass only instructions for simple tasks, full trajectory only when needed.

### Strategy 2: Observation Masking (JetBrains)
Hide verbose tool outputs from earlier turns, preserve action/reasoning history. **Performs on par with LLM summarization**, cheaper and faster. 40-60% context reduction.

### Strategy 3: Compaction Between Agents (Microsoft)
Three levels: full raw context → compacted summary → fresh instructions only. "If your agent can work without accumulated context, take that approach."

### Strategy 4: Blackboard / Shared Memory
External store agents read/write. Pull only needed data. Supports multi-resolution summaries. **INDEX-MASTER is a blackboard.**

### Strategy 5: System Prompt Swapping (OpenAI)
Only active agent's system prompt loaded. Chat history persists across handoffs. Bounds system prompt to one agent at a time.

### Strategy 6: Hierarchical Context
Manager → workers → sub-workers. Each level filters and summarizes before passing down.

### Practical Recommendations
1. Monitor token consumption per agent per run
2. Use smallest model that works per agent
3. Set context budgets with enforcement
4. Persist state externally
5. Prefer observation masking over LLM summarization
6. Design agents to be context-minimal by default

---

## 8. Prover-Specific Takeaways

1. **Use code-level orchestration + LLM reasoning** — orchestrator brain defines the workflow graph in rules, specialist brains use LLM flexibility within their scope.
2. **Fan-out with reducer merge** — orchestrator fans to Donchian + Coder + Frontend in parallel, merges via typed state with append reducers.
3. **Role-based decomposition** — each brain has explicit role/goal/capabilities (maps to fat index entries).
4. **Maker-checker for quality** — Donchian proposes strategy, Coder implements, orchestrator validates output matches spec. Always cap iterations.
5. **Circuit breakers** — if a specialist brain fails 3x, proceed without it + flag to user.
6. **Observation masking > summarization** — when passing context between brains, mask verbose outputs, keep reasoning/decisions.
7. **Context isolation is the #1 architecture principle** — each brain gets clean context, receives only task-specific CONTEXT-PACK.
8. **Complexity hierarchy** — start with single agent + tools. Only escalate to multi-brain when the task genuinely requires cross-domain knowledge.

---

## Sources

- [AI Agent Orchestration Patterns - Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Scaling LangGraph Agents: Parallelization, Subgraphs, and Map-Reduce](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)
- [Orchestrating Multiple Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/multi_agent/)
- [CrewAI vs LangGraph vs AutoGen - DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [Agent Orchestration 2026 Guide - Iterathon](https://iterathon.tech/blog/ai-agent-orchestration-frameworks-2026)
- [Context Engineering in Manus](https://rlancemartin.github.io/2025/10/15/manus/)
- [Smarter Context Management for LLM Agents - JetBrains](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [Why Multi-Agent LLM Systems Fail - Galileo](https://galileo.ai/blog/multi-agent-llm-systems-fail)
- [Practical Guide to Building Agents - OpenAI](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- [Retries, Fallbacks, and Circuit Breakers - Portkey](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/)
- [Salesforce Agentforce Failover Design](https://www.salesforce.com/blog/failover-design/?bc=OTH)
- [CrewAI Flows Documentation](https://docs.crewai.com/en/concepts/flows)
- [From Chaos to Choreography - Cognaptus](https://cognaptus.com/blog/2025-08-09-from-chaos-to-choreography-the-future-of-agent-workflows/)

## Known Issues
- Framework APIs evolve rapidly — analysis is point-in-time Feb 2026
- 41-86.7% failure statistic from Galileo study — methodology not deeply evaluated
- Observation masking finding from JetBrains is one study — needs broader validation
- No hands-on benchmarking — all patterns from documentation and research articles
