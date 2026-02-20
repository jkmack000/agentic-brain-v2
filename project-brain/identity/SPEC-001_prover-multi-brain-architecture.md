# SPEC-001: Prover Multi-Brain Architecture
<!-- type: SPEC -->
<!-- created: 2026-02-17 -->
<!-- updated: 2026-02-17 -->
<!-- tags: prover, multi-brain, orchestrator, architecture, git-worktrees, sub-agents, coordination, backtesting -->
<!-- links: SPEC-000, LEARN-024, LEARN-025, LEARN-026, LEARN-027, LEARN-028, LEARN-029, LEARN-031, LEARN-009, LEARN-011, LEARN-015, LEARN-037 -->

## Overview

Prover is a multi-brain backtesting system. Multiple specialist brains coordinate through an orchestrator brain to implement, test, and refine trading strategies. This SPEC defines the architecture, coordination patterns, execution pipeline, and inter-brain protocol.

## System Components

### Brains

| Brain | Role | Source | Status |
|---|---|---|---|
| **Agentic Brain** | Meta-brain — documents how brains work | This repo | Exists (40+ files) |
| **Orchestrator** | Fans out tasks, gathers results, deposits knowledge | Fork/refinement of agentic-brain | Not built |
| **Donchian** | Trading domain — indicators, signals, execution, economic thesis | Existing brain | Exists, needs enrichment |
| **Coder** | Implementation — strategy code, framework integration, testing | Context7 MCP for library docs + project brain for patterns | Not built |
| **Frontend** | HMI/UI for backtest visualization | Stack TBD | Not built |

### Each Agent = Own Project + Own Brain

Each specialist agent is its own **project directory** with its own brain, not just a brain-within-a-shared-project. The Coder brain would be a standalone project filled with Python and Context7-specific knowledge; the Donchian brain would be its own project with trading domain knowledge. This is token-efficient — each agent loads only its own brain at session start, not a monolithic shared brain.

**Coordination between agent-projects:** An open design question — shared git repo with worktrees, or fully separate repos with CONTEXT-PACK messages passed via filesystem/MCP. See Open Questions.

### Orchestrator Role

The orchestrator is the **only** brain that talks to the user directly and the **only** brain that writes to `project-brain/` files. It:

1. Receives a task from the user (e.g., "backtest Donchian channel breakout on BTC daily")
2. Decomposes the task into specialist subtasks using code-level workflow (not dynamic LLM routing)
3. Fans out to specialist brains with CONTEXT-PACK messages
4. Gathers RESULT messages and merges via reducer pattern
5. Validates outputs (maker-checker), deposits knowledge as LEARN/LOG files
6. Returns a unified response or coordinates multi-step iterations (capped)

### Specialist Brain Role

Each specialist brain:
- Owns a domain (trading logic, code patterns, UI components)
- Receives a scoped CONTEXT-PACK with only task-relevant fat index entries (not full INDEX-MASTER)
- Returns a structured RESULT (target: 1-1.5K tokens, per LEARN-026)
- Does NOT write to `project-brain/` — returns discoveries in RESULT for orchestrator to deposit
- Does NOT talk to other specialists directly — all coordination through orchestrator

## Coordination Architecture

### Option A: Git Worktree Isolation (from Letta, LEARN-029)

**Recommended layout: bare repo with peer worktrees.**

```
prover.git/                      # Bare repo (no working files)
prover-main/                     # Worktree: main branch (orchestrator)
prover-donchian/                 # Worktree: agent/donchian/<task-id>
prover-coder/                    # Worktree: agent/coder/<task-id>
prover-frontend/                 # Worktree: agent/frontend/<task-id>
```

**Branch naming convention:** `agent/<brain-name>/<task-id>`
- e.g., `agent/donchian/task-042-implement-atr`, `agent/coder/task-043-refactor-signals`

**Key decisions from LEARN-029:**
- Bare repo layout avoids one "special" main checkout — all worktrees are peers
- Branch exclusivity enforced by Git (can't check out same branch in 2 worktrees)
- Each worktree has own index file — no lock contention for concurrent agents
- `--no-ff` merges preserve agent branch history for audit trail
- Test in each worktree BEFORE merge; only merge branches where tests pass
- Auto-cleanup: `git branch --merged main | grep "agent/" | xargs git branch -d`
- **Critical: orchestrator-only brain writes** — agents work on code in their worktree, return RESULT files; orchestrator deposits knowledge into brain

**What's NOT isolated:** network ports, databases, environment variables (acceptable for Prover)

### Option B: Sub-Agent with Context Packages (Claude Code native)

Use Claude Code's built-in sub-agent system (LEARN-009):

```
Orchestrator (main session)
├── Task tool → Donchian subagent (Explore type, brain files pre-loaded)
├── Task tool → Coder subagent (general-purpose, code access)
└── Task tool → Frontend subagent (general-purpose, UI patterns)
```

- Each subagent gets a fresh context window with only relevant brain files
- Returns condensed summary to orchestrator
- **Pro:** Native to Claude Code, no git overhead, parallel execution
- **Con:** Subagents can't spawn subagents, no persistent state between calls, context from many subagents bloats main conversation

### Option C: Agent Teams (LEARN-015, experimental)

Full independent Claude Code sessions connected by shared task list + mailbox. Deferred until agent teams exits experimental (~7x token cost).

### Option D: Sandbox Agent + Rivet Actors (LEARN-037)

Sandbox Agent (sandboxagent.dev) provides a universal HTTP/SSE API for running coding agents in isolated sandboxes. Each specialist brain runs as a sandboxed agent session, controlled by the orchestrator over HTTP. Rivet actors provide session persistence and routing.

- **Pro:** Session persistence (solves Option B statelessness), per-session MCP tools (brain-search per sandbox), agent-agnostic (swap models per brain), Inspector UI for debugging, RBAC security
- **Con:** Additional infrastructure (runtime dependency), TypeScript SDK only (no Python), HTTP latency vs local sub-agents, v0.2.x maturity
- **Rivet actors as brain execution layer:** Each specialist brain as a Rivet actor. Orchestrator sends CONTEXT-PACKs via HTTP, actor maintains working context between rounds, brain files on disk remain durable knowledge layer. Clean separation: Rivet = working memory, brain files = long-term memory. Natively handles session routing for multi-step specialist workflows.
- **Verdict:** Phase 2+ candidate. Doesn't change brain architecture — changes the execution layer. Over-engineering at current scale.

### Recommended Progression

**Phase 1 (MVP):** Option B (sub-agents). Zero infrastructure to build, native to Claude Code, adequate for single-session backtesting.

**Phase 2 (Persistence):** Option A (worktrees) or Option D (Sandbox Agent). When multi-session tasks require persistent state, auditable results, or per-session tools. Option D preferred if HTTP latency is acceptable and session persistence proves more valuable than git audit trail.

## Inter-Brain Communication Protocol

### CONTEXT-PACK v2 (Orchestrator → Specialist)

YAML frontmatter for machine-parseable metadata + markdown body for LLM consumption (LEARN-026).

```markdown
---
task_id: "donchian-btc-daily-001"
source: orchestrator
target: donchian
priority: P1
token_budget: 1500
output_schema: RESULT-v2
---
# Task: Evaluate Donchian Channel 20/10 on BTC Daily

## Objective
[Scoped description — one clear deliverable]

## Relevant Context
[Fat index entries for files the specialist needs — NOT full files]
[Send only task-relevant entries, not full INDEX-MASTER]

## Constraints
- Output must fit within token_budget (1500 tokens)
- Read-only access to brain files (do not modify)
- Return discoveries separately from main output

## Expected Output
[Specific format: parameter table, code file, analysis report]
```

**Token budget:** ~750 tokens (YAML ~100 + task ~200 + fat indices ~300 + constraints ~150)

### RESULT v2 (Specialist → Orchestrator)

```markdown
---
task_id: "donchian-btc-daily-001"
source: donchian
status: complete | partial | blocked
confidence: high | medium | low
token_count: 1247
---
# RESULT: Donchian Channel 20/10 BTC Daily Evaluation

## Findings
[800-1200 tokens — the primary deliverable]

## Recommendations
[With confidence levels — what should be done next]

## Discoveries
[New knowledge found during work — candidate for orchestrator to deposit as LEARN/LOG]

## Conflicts
[Contradictions with existing brain knowledge — flag for user decision]

## Blockers
[What prevented completion, if status is partial/blocked]
```

**Token budget:** ~1100-1500 tokens (header ~50 + findings ~800-1200 + discoveries ~200)
**Total inter-brain message round trip:** ~2250 tokens max

### Capability Advertisement

Each specialist brain's INDEX-MASTER header declares capabilities for automated routing:

```markdown
<!-- capabilities: trading-strategy-analysis, parameter-optimization, market-regime-detection -->
<!-- input-types: strategy-query, parameter-comparison, backtest-request -->
<!-- output-types: RESULT, LEARN-candidate -->
<!-- token-budget: 1500 -->
```

## Task Routing

Three strategies, in order of implementation:

1. **Hardcoded routing** (Phase 1) — Orchestrator has a static map: trading → Donchian, implementation → Coder, UI → Frontend. Simple, works now.
2. **Fat-index capability ads** (Phase 2) — Each specialist brain's INDEX-MASTER advertises capabilities. Orchestrator scans headers to route. Self-maintaining.
3. **Learned RULE-based routing** (Phase 3) — After enough tasks, deposit routing rules as RULE files based on observed patterns.

**Complexity hierarchy (LEARN-027):** Use simplest mechanism that works — single direct call → single agent → multi-agent fan-out. Don't escalate to multi-brain unless the task genuinely requires it.

## Backtesting Execution Pipeline

### Two-Phase Architecture (LEARN-025)

```
                        ORCHESTRATOR
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
    Phase 1: Screen    Donchian Brain    Coder Brain
    (VectorBT)         (thesis)          (implementation)
           │                │                │
           ▼                ▼                ▼
    Top N by Sharpe    Economic thesis    IStrategy code
           │                │                │
           └────────────────┼────────────────┘
                            ▼
                    Phase 2: Validate
                    (Freqtrade event-driven)
                            │
                            ▼
                    Phase 3: Robust Validation
                    (CPCV with PBO < 0.5 gate)
                            │
                            ▼
                    LEARN deposit (insights)
                    RULE deposit (if strategy passes)
```

**Phase 1 — Screening (minutes):** VectorBT vectorized parameter sweep. 1000x faster than event-driven. Select top N candidates by Sharpe ratio.

**Phase 2 — Validation (hours):** Freqtrade event-driven backtest on top candidates. Full order simulation, realistic slippage/fees. Strategy code uses DataFrame method pattern (LLM-friendly): `populate_indicators()`, `populate_entry_trend()`, `populate_exit_trend()`.

**Phase 3 — Robust Validation:** CPCV (Combinatorial Purged Cross-Validation). Hard gate: PBO (Probability of Backtest Overfitting) must be < 0.5. Deflated Sharpe ratio as secondary metric.

### Strategy Abstraction (LEARN-025)

Freqtrade's DataFrame method pattern (Pattern B) is the recommended abstraction for AI-generated strategies:
- `populate_indicators(dataframe)` — Add technical indicators
- `populate_entry_trend(dataframe)` — Define entry conditions
- `populate_exit_trend(dataframe)` — Define exit conditions
- Declarative parameter definitions — easy for LLM to enumerate and modify
- Separation of concerns — optimize one method without breaking others

### Data Pipeline

Pipeline is a **shared service**, not embedded in each strategy:
- Flow: Raw OHLCV → Clean/normalize → Resample & align → Strategy-ready
- Format: **Parquet** for OHLCV data, **JSON** for metadata
- Store at lowest needed timeframe, resample up (prevents look-ahead bias)
- Multi-timeframe: load base TF, resample higher TFs, align timestamps (higher TF values only after period closes)

### Parameter Optimization (LEARN-025)

Three-phase pipeline:
1. **VectorBT sweep** — grid/random over parameter space (fast, broad)
2. **Optuna Bayesian refinement** — sample-efficient on promising regions, with pruning
3. **CPCV validation** — PBO < 0.5 as hard gate, Deflated Sharpe as quality metric

### Backtest Results — Where They Go

- **Raw results** → Filesystem only (Parquet for trade logs, JSON for metrics). NOT in brain.
- **Insights from results** → LEARN files in Donchian brain (e.g., "Donchian 20/10 outperforms 55/20 on BTC daily in trending markets")
- **Parameter decisions** → SPEC or RULE files in Donchian brain
- **Implementation notes** → CODE files in Coder brain
- **Visualization patterns** → LEARN files in Frontend brain

## Orchestration Patterns (LEARN-027)

### Fan-Out / Fan-In with Reducer Merge

```
Orchestrator:
1. Fan-out CONTEXT-PACKs to Donchian + Coder (+ Frontend) in parallel
2. Wait for all RESULT files (with timeout per specialist)
3. Merge via reducer pattern: append all findings, deduplicate
4. Synthesize merged findings into response or next iteration
```

### Maker-Checker Quality Gate

For strategy implementation:
1. Donchian proposes strategy spec (thesis + parameters)
2. Coder implements per spec (IStrategy code)
3. Orchestrator validates output matches input spec
4. **Always cap iterations** — max 3 rounds, fallback if divergence continues

### Error Handling

- **Circuit breakers:** If specialist fails 3x, proceed without it + flag to user
- **Timeout budgets:** Default 5 min per specialist task; configurable per task type
- **Graceful degradation:** Partial results with quality warning > total failure
- **Output validation:** Schema check on RESULT (has required sections, within token budget, confidence level present)

### Context Management

- **Context isolation is #1 principle** — each brain gets clean context window
- **Observation masking > LLM summarization** (LEARN-027) — 40-60% token reduction, cheaper and faster
- Send only task-relevant fat index entries, never full INDEX-MASTER
- Do NOT let agents inherit full conversation history

## Prover-Specific Guard Rails (LEARN-025)

These MUST be implemented as RULE files in the Orchestrator brain (not modifiable by agents):

1. **Max budget per optimization run** — Enforced via Agent SDK `max_budget_usd` parameter
2. **PBO < 0.5 hard gate** — No strategy reaches "recommended" status without passing CPCV
3. **Economic thesis required before parameter search** — Donchian brain provides thesis, Coder implements it. Never optimize blindly.
4. **Validation methodology fixed** — CPCV pipeline defined in RULE file, never modified by AI agents
5. **Convergence caps** — Stop optimization after N iterations without improvement (prevents infinite search)
6. **Narrative fabrication check** — Orchestrator validates that strategy rationale precedes results (not post-hoc)

## Coder Brain Design (LEARN-028)

Context7 (Upstash MCP server for library docs) informs the Coder brain architecture:

- **Complementary, not competing:** Context7 answers "how does this library work?" while Coder brain answers "how does OUR project use it and why?"
- **Two-tool resolution pattern:** `brain-search` (fat-index lookup) + `brain-read` (token-budgeted content retrieval)
- **Backend filtering > LLM filtering:** Ranking/filtering in brain MCP server (cheap, fast, deterministic), not in LLM (expensive, slow, nondeterministic)
- **Enrichment at deposit time:** Fat index entries pre-computed when file is created (cost paid once, savings on every query)
- **Ideal setup:** Context7 MCP server + Coder brain MCP server both available to the same AI assistant

## Cross-Brain Conflict Resolution

When two specialists return contradictory information:
1. Orchestrator flags the conflict explicitly in the merge step
2. Both claims deposited with `[CONFLICT]` tag in Known Issues
3. User decides (orchestrator presents the conflict, doesn't resolve autonomously)
4. Winning claim updated, losing claim retired with rationale

## Scaling Thresholds (LEARN-031)

| Files per Brain | Action Required |
|---|---|
| 50-100 | Fat index essential (already implemented). First consolidation pass. |
| 100-300 | Sub-indexes created. BM25 search critical. |
| 300-500 | Automated maintenance. "Mental squeeze point" triggers new MOC/sub-index. |
| 500-1000 | Evernote Effect danger zone — aggressive consolidation every 20-30 files. |
| 1000+ | Full automated search (FTS5/hybrid). Progressive summarization required. |

Consolidation every ~20-30 files is the correct cadence (validated by A-MEM NeurIPS 2025, Letta, Claude auto memory).

## Gaps to Close

### Gap 1: Git Worktree Multi-Agent Isolation
- **Need:** Specialists working on shared codebase without conflicts
- **Effort:** Medium — git worktree commands straightforward; bare-repo layout and branch naming defined (LEARN-029)
- **Priority:** P2 — not needed for Option B MVP, needed for Option A evolution
- **Resolution:** Bare repo layout + `agent/<brain>/<task-id>` branches + `--no-ff` merges + orchestrator-only brain writes. See Coordination Architecture section.

### Gap 2: Background Reflection / Auto-Deposit
- **Need:** Specialists auto-depositing discoveries during long tasks
- **Effort:** Medium — requires periodic hook or background subagent
- **Priority:** P3 — manual deposit via orchestrator works initially
- **Blocker:** Claude Code hooks are event-driven, not timer-driven

### Gap 3: Formalized Defragmentation
- **Need:** After iterations, brains accumulate redundant/contradictory results
- **Effort:** Low-Medium — triggers and process defined
- **Priority:** P2 — critical after ~50 files per brain
- **Triggers:** File count > 50; >3 contradictions flagged; fat index > 200 lines; user request

### Gap 4: Concurrent Initialization
- **Need:** Bootstrapping new specialist brain from large source is slow if serial
- **Effort:** Medium — fan out N subagents, each explores different topic, orchestrator deduplicates
- **Priority:** P1 — needed for building Coder and Frontend brains

### ~~Gap 5: Per-File Frontmatter vs Centralized Index~~
- **RESOLVED:** Keep centralized INDEX-MASTER. Proven at 40+ files in agentic-brain. Per-file frontmatter requires opening files to discover them — defeats the purpose. Trade-off (index maintenance discipline) already enforced via rules.

## Open Questions

- Frontend stack preference? (React? Svelte? Plain HTML/JS?)
- Is Prover the whole system or just the backtester?
- Data freshness — how does OHLCV data get refreshed?
- Strategy versioning — git tags? Dedicated VERSION file?
- How do independent agent-projects coordinate? Shared git repo with worktrees, or fully separate repos with CONTEXT-PACK messages via filesystem/MCP?

## Known Issues
- Agent teams (Option C) is experimental and ~7x token cost — not viable yet
- Subagents can't spawn subagents — limits recursive orchestration depth to 1
- Context from many completed subagents can bloat orchestrator's context window
- No timer-driven hooks in Claude Code — background reflection requires workaround
- Claude Code native worktree support is an open feature request (#24850)
- Freqtrade is crypto-focused — equity/futures may need different framework evaluation
- FTS5 k1/b parameters are hardcoded at 1.2/0.75 (not tunable) — acceptable given defaults work well
