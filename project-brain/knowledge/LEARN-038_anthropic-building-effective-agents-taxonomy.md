# LEARN-038: Anthropic's Building Effective Agents — Official Taxonomy & Design Principles
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- source: https://www.anthropic.com/engineering/building-effective-agents -->
<!-- tags: anthropic, agents, workflows, orchestration, taxonomy, tool-design, ACI, poka-yoke, simplicity, augmented-LLM, evaluator-optimizer -->
<!-- links: LEARN-027, LEARN-026, SPEC-001, LEARN-037 -->

## Why This File Exists
Anthropic's official engineering blog on agent design. Authoritative source for taxonomy, design principles, and tool engineering guidance. Overlaps with LEARN-027 (orchestration patterns from 6 frameworks) but provides the canonical Anthropic framing and unique insights on ACI and tool engineering.

## Core Taxonomy: Workflows vs Agents

Anthropic splits all "agentic systems" into two categories:

| | Workflows | Agents |
|---|-----------|--------|
| **Definition** | LLMs + tools orchestrated through **predefined code paths** | LLMs **dynamically direct** their own processes and tool usage |
| **Control** | Developer defines the flow | LLM maintains control over how it accomplishes tasks |
| **When to use** | Well-defined tasks needing predictability | Open-ended problems where steps can't be predicted |
| **Trust requirement** | Low (code controls flow) | High (LLM makes decisions) |

**Key principle:** "Finding the simplest solution possible, and only increasing complexity when needed." Most tasks don't need full agents — workflows suffice.

## The Five Canonical Workflow Patterns

### 1. Prompt Chaining
- Sequential LLM calls where each processes the previous output
- **Novel element: "gate" checkpoints** — programmatic quality checks between steps that can halt or redirect the chain
- Example: outline → gate (check structure) → draft → gate (check accuracy) → final
- Use when: task naturally decomposes into fixed sequential subtasks

### 2. Routing
- Classify input → direct to specialized downstream handler
- Enables separation of concerns and per-route optimization
- Example: customer query → classify (general/refund/technical) → specialized handler
- Example: simple queries → cheap model, complex → capable model
- Use when: distinct categories exist with meaningfully different handling

### 3. Parallelization
Two sub-patterns:
- **Sectioning**: Independent subtasks run simultaneously (e.g., guardrail check + main response in parallel)
- **Voting**: Same task run N times for diverse outputs (e.g., multiple code vulnerability reviewers)
- Use when: subtasks are independent OR consensus/diversity improves quality

### 4. Orchestrator-Workers
- Central LLM **dynamically** decomposes task → delegates to worker LLMs → synthesizes results
- Key distinction from parallelization: "subtasks aren't pre-defined, but determined by the orchestrator based on the specific input"
- Example: multi-file code changes, multi-source research
- Use when: task decomposition can't be predicted in advance

### 5. Evaluator-Optimizer
- Generator LLM produces output → Evaluator LLM provides feedback → iterate
- Requires: clear evaluation criteria, measurable improvement potential
- Example: literary translation with iterative refinement, multi-round search
- **Not well-covered in existing brain files** — distinct from maker-checker (LEARN-027) because it's iterative refinement, not binary pass/fail

## The Augmented LLM (Building Block)

The foundational unit is not a bare LLM but an **augmented LLM**: LLM + retrieval + tools + memory. All workflows and agents compose from this building block. MCP provides standardized tool integration.

**Brain relevance:** Our brain system IS the memory augmentation layer. Context7 IS the retrieval layer. The Coder brain's tool pipeline IS the tools layer. We're already building augmented LLMs.

## ACI: Agent-Computer Interface (Novel Concept)

Anthropic applies **HCI (Human-Computer Interface) design principles** to the tool interfaces agents use:

1. **Tool documentation is UX design** — treat tool definitions with the same rigor as user-facing UI
2. **Include in tool definitions:** example usage, edge cases, input format requirements, clear boundaries
3. **Poka-yoke (mistake-proofing):** design tools so misuse is structurally impossible
4. **Format selection principles:**
   - Give the model enough tokens to think before committing to output structure
   - Keep formats close to what the model has seen in natural text on the internet
   - Eliminate formatting overhead (line counting, string escaping)

### Tool Engineering > Prompt Engineering
**Critical finding:** For SWE-bench, Anthropic spent **more optimization time on tools than on prompts**. This inverts the common assumption that prompt engineering is the primary lever.

**Brain relevance:** Directly validates our CONTEXT-PACK/RESULT format design (SPEC-001) — the inter-brain message format IS an ACI. Also validates investing in brain skill design (brain-search, brain-deposit) over tweaking CLAUDE.md prompts.

## Simplicity-First Principle

1. **Start with LLM APIs directly** — don't adopt frameworks first
2. Frameworks (Agent SDK, Strands, Rivet, Vellum) "create extra layers of abstraction that can obscure the underlying prompts and responses, making them harder to debug"
3. Only add complexity when simpler approaches demonstrably fail
4. "Success in the LLM space isn't about building the most sophisticated system. It's about building the *right* system for your needs."

**Brain relevance:** Validates our SPEC-001 recommendation of Option B (sub-agents) before Option A (git worktrees) or Option D (Sandbox Agent). Start simple, evolve when needed.

## Autonomous Agents

Agents become viable as LLMs improve at: understanding complex inputs, reasoning/planning, reliable tool use, error recovery.

Key design requirements:
- Agents gain "ground truth" from **environmental feedback** (tool results, code execution) — not from the LLM's own confidence
- Must operate in a **loop**: act → observe environment → decide next step
- Require **sandboxed testing** before deployment
- **Toolset documentation is critical** — "design toolsets and their documentation clearly and thoughtfully"

Natural agent domains:
- **Customer support** — conversation flows + tools + measurable resolution criteria
- **Coding agents** — solutions verifiable via automated tests, well-defined problem space, objective quality measures

## What's New vs LEARN-027

| Topic | LEARN-027 (6 frameworks) | This file (Anthropic official) |
|-------|-------------------------|-------------------------------|
| Orchestrator-worker | Covered extensively | Covered (canonical framing) |
| Fan-out/fan-in | Detailed with reducers | Called "parallelization" with sectioning/voting |
| Evaluator-optimizer | Maker-checker (binary) | **Iterative refinement** (new) |
| Prompt chaining + gates | Not covered | **New pattern** |
| Routing | Implicit in task decomposition | **Explicit named pattern** |
| ACI / tool engineering | Not covered | **New concept** |
| Simplicity principle | Complexity hierarchy mentioned | **Central thesis** |

## Prover/Brain Implications

1. **Evaluator-optimizer** maps to our VectorBT screening → Freqtrade validation → CPCV pipeline — each stage evaluates and refines
2. **Routing** pattern applicable to Orchestrator brain: classify strategy type → route to appropriate Coder brain template
3. **ACI principle** means our CONTEXT-PACK/RESULT formats deserve as much design attention as the strategies themselves
4. **Gate checkpoints** in prompt chaining map to our 3-stage validation pipeline (AST parse → import whitelist → pytest)
5. **Tool engineering > prompt engineering** — invest more in brain skill quality than CLAUDE.md size

## Known Issues
- Article is high-level guidance, not implementation-specific — no code examples, no benchmarks
- Framework recommendations may shift as Claude Agent SDK evolves
- "Simplicity first" may conflict with Prover's inherent multi-brain complexity (but the principle is to not add complexity *beyond* what's needed)
