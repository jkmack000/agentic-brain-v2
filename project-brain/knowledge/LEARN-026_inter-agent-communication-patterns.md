# LEARN-026: Inter-Agent Communication Patterns for Multi-Brain Systems
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: multi-agent, IPC, communication, context-passing, message-formats, serialization, shared-memory, token-efficiency, A2A, MCP, AutoGen, CrewAI, LangGraph, Claude-Code, OpenAI-Swarm, blackboard, stigmergy -->
<!-- links: SPEC-001, LEARN-009, LEARN-015, LEARN-024, LEARN-002, LEARN-021 -->

## Purpose

Research synthesis of inter-process communication patterns for LLM/AI agents, focused on practical patterns applicable to file-based multi-brain systems using markdown as the knowledge store. Directly informs SPEC-001 (Prover multi-brain architecture) inter-brain communication design.

---

## 1. Context Passing Patterns

Three fundamental strategies for how agents share relevant context:

### 1a. Full Context Dump
- Send the entire conversation history or knowledge base to the receiving agent.
- **Used by:** OpenAI Swarm (intentionally stateless — every handoff must include all context), AutoGen HandoffMessage (passes full `context` list of messages).
- **Pros:** No information loss, simple to implement.
- **Cons:** Blows up context windows, O(n) growth per handoff, impractical beyond ~50K tokens.
- **When to use:** Small task chains with <10K tokens of accumulated context.

### 1b. Summary/Compression
- An LLM or algorithm compresses the relevant context before passing it.
- **Used by:** Anthropic's multi-agent research system (subagents return condensed findings, not full transcripts), Claude Code subagents (~70% token reduction via context filtering), LangGraph compaction (summarize then continue).
- **Compression ratios observed:**
  - Anthropic subagent returns: **10-20x compression** (200K window distilled to 1-2K token summaries per LEARN-024)
  - Claude Code subagent delegation: **~70% reduction** vs handling in main context
  - Acon framework (academic): **26-54% memory reduction** while preserving task success
  - Optimized agent protocols: **73% length reduction** by removing examples, matrices, verbose explanations
- **Cons:** Lossy — the compressor decides what matters, may discard information the receiver needs.
- **When to use:** Default for most multi-agent patterns. The dominant real-world approach.

### 1c. Delta/Incremental
- Only send what changed since the last exchange.
- **Used by:** State Delta Encoding (SDE) research — records differences between hidden states of adjacent tokens for inter-agent transfer. Git-based coordination (tick-md) where changes are diffs/commits.
- **Pros:** Minimal bandwidth, scales with change rate not total size.
- **Cons:** Requires shared baseline state, complex to implement for natural language (works well for structured data).
- **When to use:** Iterative refinement loops where agents exchange updates on the same artifact.

### Brain-Relevant Decision
SPEC-001's CONTEXT-PACK format is a **hybrid of 1b and 1c**: it sends fat index summaries (compressed) plus only the specific task scope (delta from the full brain). This is the right approach. The key insight from Anthropic's research system is that **subagents should receive task-specific context (~500 tokens of instruction) rather than inheriting the full conversation**.

---

## 2. Message Formats Between AI Agents

### 2a. Google Agent2Agent (A2A) Protocol
The most comprehensive standardized protocol. Released April 2025, now under Linux Foundation, 150+ supporting organizations.

**Transport:** HTTPS + JSON-RPC 2.0 (also gRPC as of v0.3)

**Core message structure:**
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "taskId": "unique-task-id",
    "message": {
      "messageId": "msg-001",
      "role": "user",
      "parts": [
        {"kind": "text", "text": "Analyze BTC daily Donchian breakout..."},
        {"kind": "data", "data": {"timeframe": "1D", "pair": "BTC/USD"}}
      ]
    }
  }
}
```

**Key concepts:**
- **Agent Card** — JSON metadata advertising identity, capabilities, skills, endpoint, auth requirements
- **AgentSkill** — describes what an agent can do (id, name, description, tags, input/output media types)
- **Message** — has `role` ("user" or "agent") and contains typed `Parts` (TextPart, FilePart, DataPart)
- **Task** — fundamental unit of work with lifecycle states (submitted, working, input-required, completed, failed, canceled)
- Supports sync request/response, SSE streaming, and async push notifications

**Brain relevance:** A2A's Agent Card maps directly to a brain's INDEX-MASTER fat index entry — both answer "what can this agent/brain do?" without opening internals. The message Parts system (text + structured data) is more expressive than our current plain-markdown CONTEXT-PACK.

### 2b. AutoGen Message Types
AutoGen defines a typed message hierarchy:

- **GroupChatMessage** — wraps a `UserMessage` body, published to shared topic
- **HandoffMessage** — includes `target` (agent name) + `context` (list of SystemMessage, UserMessage, AssistantMessage, FunctionExecutionResultMessage)
- **RequestToSpeak** — sent by GroupChat manager to selected next speaker
- All messages follow OpenAI chat format (`role` + `content`) as the common interchange format

**Brain relevance:** The HandoffMessage pattern — explicitly naming the target and bundling context — is exactly what SPEC-001's orchestrator-to-specialist routing needs. The context list approach (rather than a single blob) allows selective inclusion.

### 2c. CrewAI Structured Output
CrewAI uses Pydantic models for type-safe inter-agent communication:

```python
class TaskOutput(BaseModel):
    summary: str
    confidence: float
    recommendations: list[str]

task = Task(
    description="Analyze...",
    output_pydantic=TaskOutput,
    agent=analyst_agent
)
```

- **output_json** — validated JSON dict, good for serialization
- **output_pydantic** — full Pydantic model with type checking, required fields, custom validators
- **CrewOutput** — includes final task output, token usage, and individual task outputs

**Brain relevance:** Pydantic-style schemas enforce structure on specialist brain returns. Our RESULT template could be formalized into a typed schema instead of free-form markdown.

### 2d. LangGraph StateGraph
LangGraph uses a shared typed state dict that flows through all nodes:

```python
from langgraph.graph import StateGraph
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]
    available_tools: list[str]
    task_status: str

graph = StateGraph(State)
```

- State defined upfront as TypedDict or Pydantic model
- **Reducers** define how concurrent updates merge (e.g., `add_messages` appends)
- Nodes read from state, write updates, LangGraph merges using reducer logic
- Message passing is the core graph algorithm — nodes send along edges

**Brain relevance:** The reducer pattern is important — when multiple specialists return results concurrently, we need a merge strategy. LangGraph's approach (typed state + merge rules) is more robust than our current "orchestrator reads all results sequentially."

### 2e. OpenAI Swarm / Agents SDK
Deliberately minimal:

- `run()` takes messages, returns messages, saves no state between calls
- Handoffs are functions that return the agent object to hand off to
- Context variables passed as a dict, threaded through all function calls
- **Now superseded** by OpenAI Agents SDK (March 2025) — production-ready with proper state management

**Brain relevance:** Swarm's intentional statelessness validates our file-based persistence approach — if you don't persist state externally, every handoff must be self-contained.

---

## 3. Serialization Strategies

### 3a. Markdown as Interchange Format
- **Used by:** tick-md, our brain system, Letta context repositories
- **Pros:** Every LLM understands it natively, human-readable, git-diffable, zero parsing overhead for the model
- **Cons:** No schema validation, no type safety, verbose for structured data
- **Best practice:** Use markdown for the outer envelope, embed structured data as fenced code blocks (JSON/YAML) within it

### 3b. JSON with Schema Validation
- **Used by:** A2A (JSON-RPC 2.0), CrewAI (Pydantic → JSON), LangGraph state serialization
- **Pros:** Machine-parseable, schema-validatable, compact for structured data
- **Cons:** LLMs occasionally produce invalid JSON, needs error handling/retry
- **Best practice:** Use `output_json` or `output_pydantic` constraints when available; for file-based systems, YAML frontmatter + markdown body is the pragmatic hybrid

### 3c. Protocol Buffers / gRPC
- **Used by:** A2A v0.3+ (optional gRPC binding)
- **Pros:** Extremely compact, strongly typed, fast serialization
- **Cons:** Binary format (not LLM-native), requires code generation, overkill for file-based systems
- **Brain relevance:** Not applicable to our file-based architecture. Mentioned for completeness.

### 3d. Hybrid: YAML Frontmatter + Markdown Body
- **Used by:** Letta (per-file frontmatter), Jekyll/Hugo, many documentation systems
- **Pros:** Structured metadata (parseable by code) + natural language body (readable by LLM), git-diffable
- **Cons:** Slight parsing overhead, frontmatter-body boundary can confuse some tools
- **Brain relevance:** Strong candidate for CONTEXT-PACK and RESULT formats. Example:

```markdown
---
task_id: donchian-btc-daily-001
source_brain: orchestrator
target_brain: donchian
priority: P1
token_budget: 1500
expected_output: RESULT
---
# Task: Analyze Donchian breakout parameters for BTC/USD daily

## Context
[Fat index entries and relevant constraints here]

## Deliverable
Return optimal channel periods with evidence from brain knowledge.
```

---

## 4. Shared Memory / State Patterns

### 4a. Blackboard Architecture
- **Origin:** Hearsay-II (1980), adapted for LLM agents in 2025-2026
- **Pattern:** All agents read/write to a shared "blackboard" (structured state). A controller selects which agent acts next based on blackboard content.
- **LLM implementation:** Shared semantic blackboard where agents contribute based on observed task state. Manager agent maintains evolving global task state.
- **Used by:** PC-Agent (manager + workers), various LLM-based multi-agent research systems
- **Brain mapping:** INDEX-MASTER.md IS a blackboard — it's the shared state that all brains can read/write to. The orchestrator is the controller.

### 4b. Stigmergic Coordination (Indirect via Environment)
- **Pattern:** Agents coordinate by observing effects of other agents' actions on the shared environment. No direct messaging.
- **Example:** Agent A processes files in `input/` and moves to `output/`. Agent B monitors `output/` and begins its task when new files appear.
- **LLM implementation:** File-based signaling. Agent writes a RESULT file; orchestrator polls for new files.
- **Used by:** tick-md (TICK.md file as coordination artifact), git-based workflows
- **Brain mapping:** Our LEARN/SPEC file deposits are stigmergic — specialists write files, orchestrator discovers them via INDEX-MASTER. No direct agent-to-agent channel needed.

### 4c. File-Based Shared State (Our Architecture)
- **Pattern:** Markdown files in a shared directory, tracked by git, indexed by fat index
- **Advantages for LLM agents:**
  - Every LLM reads markdown natively (zero serialization cost)
  - Git provides audit trail, conflict detection, branching
  - File locks prevent concurrent edit conflicts (tick-md pattern)
  - Works offline, portable, no database dependency
- **Disadvantages:**
  - No real-time signaling (polling-based)
  - Merge conflicts on concurrent writes to same file
  - No built-in query language (relies on fat index + grep)

### 4d. Database-Backed Shared Memory
- **Used by:** Mem0 (Qdrant vector store), LangGraph (checkpoint store), Zep (temporal knowledge graph)
- **Pros:** Real-time queries, ACID transactions, vector similarity search
- **Cons:** Extra infrastructure, not LLM-native (need serialization layer), harder to audit/diff
- **Brain relevance:** Not our architecture, but QMD (LEARN-023) could serve as a search complement over brain files.

### 4e. In-Memory Stores
- **Used by:** LangGraph state (in-process TypedDict), AutoGen GroupChat (shared message list)
- **Pros:** Fastest access, typed, no serialization
- **Cons:** Lost on process exit, not file-based, single-machine only
- **Brain relevance:** Not applicable — our agents are separate Claude Code sessions.

---

## 5. Token-Efficient Communication Techniques

Target: **1-2K tokens per inter-agent message** (from LEARN-024 finding #10, Anthropic's observed compression ratio).

### 5a. Context Filtering (Highest Impact)
- Send only task-relevant context, not the full conversation history.
- Claude Code subagents receive ~500 tokens of instruction rather than inheriting 200K of main context.
- **Result:** ~70% token reduction for complex tasks.
- **Implementation:** CONTEXT-PACK includes only the fat index entries relevant to the task, not the full INDEX-MASTER.

### 5b. Protocol Compression
- Remove examples, matrices, checklists, and verbose explanations from agent management instructions.
- **Result:** Average 73% reduction in coordinator role description length.
- **Implementation:** Strip CONTEXT-PACK to essentials: task description, 2-3 relevant fat index entries, constraints, output format spec.

### 5c. Structured Output Constraints
- Force the receiving agent to return in a fixed schema (JSON or typed markdown template).
- Prevents rambling, ensures only requested information is returned.
- **Result:** Consistent 1-2K token returns vs unbounded free-form.
- **Implementation:** RESULT template with explicit token budget in CONTEXT-PACK header.

### 5d. Summary Distillation
- LLM summarizes its own work into a condensed format before returning to the orchestrator.
- Anthropic pattern: subagents "condense the most important tokens for the lead research agent."
- **Result:** 10-20x compression (200K context distilled to 1-2K).
- **Implementation:** Add "Summarize your findings in under 1500 tokens" as a constraint in CONTEXT-PACK.

### 5e. Tiered Memory (Load on Demand)
- Collaborative Memory pattern: private memory (agent-local) + shared memory (selectively shared).
- Don't send all shared state — let the receiving agent request specific files if needed.
- **Implementation:** Fat index entries in CONTEXT-PACK; specialist loads full files only if fat index indicates relevance.

### 5f. Active Context Compression (Academic)
- Acon framework: optimally compresses both environment observations and interaction histories.
- Compression guidelines updated via LLM analysis of failure cases.
- **Result:** 26-54% peak token reduction while preserving task success.
- **Status:** Research-stage, not yet in production frameworks.

### 5g. Delta Encoding (Emerging)
- State Delta Encoding (SDE): transfer information as sequence of changes in agent hidden states.
- **Status:** Academic research, not practical for file-based systems yet.

### Token Budget Envelope

For our system, a practical inter-brain message should fit this budget:

| Component | Token Budget |
|-----------|-------------|
| YAML frontmatter (task_id, routing, constraints) | ~100 tokens |
| Task description | ~200 tokens |
| Relevant fat index entries (2-3 files) | ~300 tokens |
| Constraints + output format spec | ~150 tokens |
| **Total CONTEXT-PACK** | **~750 tokens** |
| | |
| RESULT header (status, task_id) | ~50 tokens |
| Condensed output | ~800-1200 tokens |
| Discoveries (new knowledge) | ~200 tokens |
| Blockers | ~50 tokens |
| **Total RESULT** | **~1100-1500 tokens** |

---

## 6. Real Implementation Analysis

### 6a. Anthropic Multi-Agent Research System
- **Architecture:** LeadResearcher (Opus 4) orchestrates 3-5 Subagents (Sonnet 4) in parallel
- **Context passing:** Subagents get task-specific instructions, NOT the lead's full context
- **Return format:** Condensed findings (1-2K tokens) returned to lead
- **State persistence:** Lead saves plan to Memory before context exceeds 200K (truncation risk)
- **Compression:** Subagents are parallel compressors — each explores independently, returns only the important tokens
- **Performance:** 90.2% improvement over single-agent Opus 4 on internal research eval
- **Cost:** ~15x token overhead vs single-agent chat
- **Key lesson:** Many agents with isolated contexts outperform one agent with a huge context

### 6b. Claude Code Subagents (Task Tool)
- **Architecture:** Main session spawns subagents via Task tool, each gets fresh context window
- **Context passing:** Subagent receives task prompt (~500 tokens) + can read files independently
- **Return format:** Summary returned to main context (verbose output stays in subagent's window)
- **Overhead:** ~20K token startup cost per subagent (context loading)
- **Compression:** ~70% token reduction vs handling in main context
- **Limitation:** Subagents cannot spawn subagents (max 1 level of delegation)
- **Key lesson:** Context isolation is the primary efficiency mechanism, not compression algorithms

### 6c. AutoGen GroupChat
- **Architecture:** GroupChatManager selects next speaker from agent pool, messages published to shared topic
- **Context passing:** GroupChatMessage wraps messages; HandoffMessage includes full context list for transfers
- **Return format:** Agents publish GroupChatMessage with results
- **State:** Conversation-centric — all agents see the shared message history
- **Key lesson:** The HandoffMessage pattern (target name + bundled context) is clean and explicit

### 6d. CrewAI
- **Architecture:** Role-based — each agent has a defined role, goal, and backstory
- **Context passing:** Task outputs chain — output of Task A becomes input of Task B
- **Return format:** Pydantic models or JSON dicts with type validation
- **State:** CrewOutput aggregates all task outputs + token usage
- **Key lesson:** Structured output schemas (Pydantic) prevent agent rambling and ensure type-safe inter-agent data flow

### 6e. LangGraph
- **Architecture:** StateGraph with typed state flowing through nodes, reducer-based merge
- **Context passing:** Shared state object updated by each node; `add_messages` reducer for conversation
- **Return format:** State updates (partial dict), merged by reducer
- **State:** First-class concept — TypedDict or Pydantic model, persisted via checkpointing
- **Key lesson:** Typed state + merge reducers solve the concurrent-results problem cleanly

### 6f. OpenAI Swarm / Agents SDK
- **Architecture:** Intentionally stateless — `run()` takes messages, returns messages, no persistent state
- **Context passing:** Full context in every call (no compression)
- **Handoff:** Functions return agent object to transfer to
- **State:** Context variables threaded through function calls
- **Key lesson:** Statelessness forces self-contained handoffs — validates file-based external persistence

### 6g. tick-md (File-Based Coordination)
- **Architecture:** Single TICK.md file as shared coordination artifact, built on Git
- **Context passing:** Tasks described in markdown, claimed by agents via file lock
- **State:** Git commits as audit trail, dependency tracking between tasks
- **Key lesson:** Markdown + Git is sufficient for asynchronous multi-agent coordination. Every LLM understands markdown natively.

---

## 7. Protocol Landscape: MCP vs A2A

Two emerging standards are relevant but serve different layers:

### Model Context Protocol (MCP)
- **Layer:** Agent-to-tool / Agent-to-data-source
- **Focus:** How an LLM accesses external tools, resources, and data
- **Transport:** HTTP, SSE, stdio
- **Current:** Host-to-Server communication (agent calls tool)
- **2026 roadmap:** Agent-to-Agent extensions (MCP Server acts as agent, recursive delegation)
- **Governance:** Donated to Agentic AI Foundation (Linux Foundation) in Dec 2025 by Anthropic, Block, OpenAI
- **Brain relevance:** Brain MCP server (LEARN-013) would expose brain as a tool. Future A2A extensions could enable brain-to-brain communication via MCP.

### Agent2Agent Protocol (A2A)
- **Layer:** Agent-to-Agent
- **Focus:** How independent agents discover, communicate, and coordinate
- **Transport:** HTTPS + JSON-RPC 2.0, gRPC (v0.3+)
- **Key innovation:** Agent Cards for capability advertisement (like our fat index entries)
- **Governance:** Linux Foundation, 150+ organizations, launched by Google April 2025
- **Brain relevance:** A2A's Agent Card pattern could formalize how specialist brains advertise their capabilities to the orchestrator. The task lifecycle (submitted/working/completed/failed) maps to our RESULT status field.

**Relationship:** MCP and A2A are complementary. MCP connects agents to tools/data. A2A connects agents to agents. A multi-brain system likely uses both — MCP for brain file access, A2A-style patterns for orchestrator-specialist communication.

---

## 8. Patterns Directly Applicable to Our Multi-Brain System

### 8a. Recommended CONTEXT-PACK v2 Format

Based on research findings, an improved version of SPEC-001's CONTEXT-PACK:

```markdown
---
task_id: "donchian-btc-daily-001"
source: orchestrator
target: donchian
priority: P1
token_budget: 1500
output_schema: RESULT-v1
timestamp: "2026-02-17T14:30:00Z"
---
# CONTEXT-PACK: donchian-btc-daily-001

## Task
Identify optimal Donchian channel periods for BTC/USD daily timeframe
based on brain knowledge. Do NOT run backtests — synthesize from existing
LEARN files only.

## Relevant Context
<!-- Fat index entries only — load full files only if these summaries are insufficient -->
- **LEARN-042:** Documents BTC daily channel period comparison (20/10 vs 55/20).
  Key finding: shorter channels outperform in trending regimes.
- **LEARN-038:** ATR-based position sizing parameters for BTC daily.

## Constraints
- Return in RESULT format, max 1500 tokens
- Do not modify any brain files
- Flag any contradictions between LEARN files in Discoveries section

## Output Format
Use the RESULT-v1 template. Include confidence level (high/medium/low)
for each recommendation.
```

### 8b. Recommended RESULT v2 Format

```markdown
---
task_id: "donchian-btc-daily-001"
source: donchian
target: orchestrator
status: complete
confidence: high
token_count: 1247
timestamp: "2026-02-17T14:31:15Z"
---
# RESULT: donchian-btc-daily-001

## Findings
[Condensed output, 800-1200 tokens max]

## Recommendations
- [Actionable items with confidence levels]

## Discoveries
<!-- New knowledge found during work — candidate for LEARN deposit -->
- [Any new insight not already in the brain]

## Conflicts
<!-- Contradictions between existing brain files -->
- [LEARN-042 says X, LEARN-038 implies Y — needs resolution]

## Blockers
[What prevented full completion, if any. Empty if status=complete]
```

### 8c. Orchestrator State Management

Adopt LangGraph's reducer pattern for merging concurrent specialist results:

```
Orchestrator state = {
    task_plan: str,          # Saved to memory before fan-out
    pending_results: dict,   # task_id -> "pending" | RESULT
    merged_findings: list,   # Reducer: append new findings
    conflicts: list,         # Reducer: append any cross-brain conflicts
    token_budget_used: int   # Track total spend
}
```

When all pending_results are resolved, orchestrator synthesizes and responds to user.

### 8d. Capability Advertisement (from A2A Agent Cards)

Each specialist brain could expose a capability summary in its INDEX-MASTER header:

```markdown
<!-- brain: donchian -->
<!-- capabilities: trading-strategy-analysis, parameter-optimization, indicator-knowledge -->
<!-- input-types: strategy-query, parameter-comparison, indicator-explanation -->
<!-- output-types: RESULT, LEARN-candidate -->
<!-- token-budget: 1500 -->
```

This enables fat-index capability routing (SPEC-001 routing strategy #2) — the orchestrator reads capability headers to decide which brain handles which subtask.

---

## 9. Key Takeaways

1. **Context isolation beats context sharing.** Anthropic's 90.2% improvement comes from giving each agent a clean, focused context window — not from sharing everything. Our subagent-per-brain approach is correct.

2. **1-2K token returns are achievable and standard.** Anthropic's research system, Claude Code subagents, and CrewAI structured outputs all converge on ~1-2K tokens as the sweet spot for inter-agent results.

3. **Markdown + Git is a legitimate coordination layer.** tick-md, Letta context repositories, and our brain system all demonstrate that file-based coordination works for asynchronous multi-agent systems where agents don't need real-time messaging.

4. **YAML frontmatter + markdown body is the optimal serialization for our use case.** Structured metadata (parseable by code/orchestrator logic) plus natural language body (readable by LLM). Used by Letta, validated by our existing brain architecture.

5. **Blackboard pattern maps to INDEX-MASTER.** Our centralized fat index is already a blackboard — shared readable state that the orchestrator uses to decide routing. This is a known, validated coordination pattern from classical multi-agent systems.

6. **Agent Card pattern from A2A should be adopted.** Adding capability metadata to brain INDEX-MASTER headers enables self-describing brains and automated routing.

7. **Typed output schemas prevent bloat.** CrewAI's Pydantic pattern and LangGraph's TypedDict pattern both show that constraining output format is essential for token-efficient communication. Our RESULT template should specify token budget and structure explicitly.

8. **15x token overhead is the cost of multi-agent.** Anthropic openly states this. The value must justify the expense. Use multi-agent only when context isolation improves quality (complex tasks across domains), not for simple sequential work.

---

## Sources

- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Code subagent documentation](https://code.claude.com/docs/en/sub-agents)
- [Claude Code SDK subagents](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Google A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [A2A Agent Skills & Agent Card](https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/)
- [AutoGen GroupChat documentation](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/group-chat.html)
- [AutoGen message types reference](https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.messages.html)
- [CrewAI Tasks and structured output](https://docs.crewai.com/en/concepts/tasks)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph state management](https://notechit.com/state-agentstate-typedict-and-message-state-in-langgraph)
- [OpenAI Swarm framework](https://github.com/openai/swarm)
- [OpenAI Agents SDK guide](https://fast.io/resources/openai-agents-sdk/)
- [tick-md: Multi-agent coordination with markdown](https://purplehorizons.io/blog/tick-md-multi-agent-coordination-markdown)
- [Coordination mechanisms in multi-agent systems](https://apxml.com/courses/agentic-llm-memory-architectures/chapter-5-multi-agent-systems/coordination-mechanisms-mas)
- [Memory in multi-agent systems: technical implementations](https://artium.ai/insights/memory-in-multi-agent-systems-technical-implementations)
- [LLM-based Multi-Agent Blackboard System](https://arxiv.org/html/2507.01701v1)
- [Acon: Optimizing Context Compression for LLM Agents](https://arxiv.org/html/2510.00615v1)
- [State Delta Encoding for multi-agent communication](https://arxiv.org/html/2506.19209)
- [Multi-Agent Multi-LLM Systems Guide 2026](https://dasroot.net/posts/2026/02/multi-agent-multi-llm-systems-future-ai-architecture-guide-2026/)
- [LangGraph vs AutoGen vs CrewAI comparison](https://latenode.com/blog/platform-comparisons-alternatives/automation-platform-comparisons/langgraph-vs-autogen-vs-crewai-complete-ai-agent-framework-comparison-architecture-analysis-2025)
- [Google A2A protocol and AI agent frameworks](https://medium.com/@FelA350/unleashing-the-aijson-rpc-2-0-team-your-guide-to-agent-communication-in-2025-ec35245160d3)
- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [Claude Code agent coordination and context amnesia](https://medium.com/@ilyas.ibrahim/how-i-made-claude-code-agents-coordinate-100-and-solved-context-amnesia-5938890ea825)
- [Collaborative Memory for multi-agent environments](https://arxiv.org/html/2505.18279v1)
- [Comparing file systems and databases for AI agent memory](https://blogs.oracle.com/developers/comparing-file-systems-and-databases-for-effective-ai-agent-memory-management)

## Known Issues
- A2A protocol is still evolving (v0.3 as of July 2025) — specific JSON schemas may change
- MCP agent-to-agent extensions are on 2026 roadmap, not yet implemented
- Acon and SDE are academic research — not yet in production frameworks
- 15x token overhead for multi-agent is Anthropic's number for research tasks — may differ for our use case
- tick-md is a young project — file locking implementation details not deeply analyzed
