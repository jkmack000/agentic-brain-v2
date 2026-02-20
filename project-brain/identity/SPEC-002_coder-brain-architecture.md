# SPEC-002 — Coder Brain Architecture
<!-- type: SPEC -->
<!-- tags: coder-brain, prover, coding-agent, python, freqtrade, ccxt, context7, code-generation, testing, validation, guardrails -->
<!-- created: 2026-02-17 -->
<!-- status: DRAFT -->
<!-- links: SPEC-001, LEARN-025, LEARN-028 -->

## Context

SPEC-001 defines 5 brains for the Prover multi-brain system. The Coder brain's role is generating Freqtrade IStrategy code from trading theses. This SPEC defines the Coder brain's internal architecture: what knowledge it needs, how it receives work from upstream agents, how it writes/tests/proves code, and what guardrails keep it safe. Informed by LEARN-025 (backtesting architecture), LEARN-028 (Context7 patterns), and external research on Freqtrade IStrategy and LLM code generation.

## Decision

The Coder brain is a **general Python coding agent** (not a template filler) that receives designs from Architect and Planner agents and produces working, tested code. Its power comes from pre-ingested knowledge about the trading infrastructure stack: Freqtrade, CCXT, ta-lib, VectorBT, and pytest.

### Position in the Agent Chain

```
User
 └─▸ Orchestrator
      ├─▸ Architect Agent  → Designs system architecture, component interfaces
      ├─▸ Planner Agent    → Breaks designs into implementation tasks with acceptance criteria
      ├─▸ Coder Agent      → Writes, tests, proves code from plans
      ├─▸ Donchian Brain   → Trading thesis, strategy parameters
      └─▸ Frontend Brain   → Visualization, HMI
```

**Coder receives:** Implementation plans with acceptance criteria, file paths, function signatures, test expectations.
**Coder produces:** Working, tested Python code + test files + validation evidence.
**Coder does NOT:** Make architectural decisions, devise trading logic, or choose between approaches.

### Knowledge Architecture

Three-tier knowledge hierarchy:

1. **Brain files** (first source of truth) — project conventions, validated patterns, known gotchas
2. **Context7 MCP** (current API reference) — auto-updated every 10-15 days across 33K+ libraries
3. **GitHub MCP/CLI** (source-level fallback) — for questions brain files and Context7 don't cover

### Knowledge Sources to Ingest

| Source | What to Extract | Brain File Type | Priority |
|--------|----------------|-----------------|----------|
| **Freqtrade docs** (freqtrade.io) | IStrategy interface, callbacks, hyperopt params, bot lifecycle, config | LEARN + CODE | P0 |
| **Freqtrade GitHub** (github.com/freqtrade/freqtrade) | Source patterns, IStrategy base class, sample strategies, test patterns | CODE | P0 |
| **freqtrade-strategies repo** (github.com/freqtrade/freqtrade-strategies) | Battle-tested strategy examples, common indicator patterns | CODE | P0 |
| **CCXT docs** (docs.ccxt.com) | Exchange abstraction, unified API, market structure, order types, errors | LEARN + CODE | P1 |
| **CCXT GitHub** (github.com/ccxt/ccxt) | Python API patterns, exchange-specific quirks, async patterns | CODE | P1 |
| **ta-lib docs** | Indicator function signatures, parameter defaults, output formats | LEARN | P0 |
| **pandas-ta** (github.com/twopirllc/pandas-ta) | Alternative indicator library, DataFrame-native API | LEARN | P2 |
| **VectorBT docs** (vectorbt.dev) | Vectorized backtesting API, signal generation, portfolio simulation | LEARN + CODE | P1 |
| **Context7 GitHub** (github.com/upstash/context7) | MCP integration patterns, two-tool resolution, token-budgeted retrieval | LEARN | P1 |
| **Optuna docs** (optuna.org) | Hyperparameter optimization, trial API, pruning, Freqtrade integration | LEARN | P2 |
| **pytest docs** | Testing patterns, fixtures, parametrize, mocking | LEARN | P1 |

### Coder Brain File Structure

```
coder-brain/
├── project-brain/
│   ├── INIT.md, INDEX-MASTER.md, SESSION-HANDOFF.md
│   ├── specs/
│   │   └── SPEC-001 — Agent architecture (this document, renumbered for local brain)
│   ├── learnings/
│   │   ├── LEARN-001 — Freqtrade IStrategy reference
│   │   ├── LEARN-002 — CCXT unified API patterns
│   │   ├── LEARN-003 — ta-lib indicator reference
│   │   ├── LEARN-004 — VectorBT API patterns
│   │   ├── LEARN-005 — Freqtrade testing patterns
│   │   ├── LEARN-006 — LLM code generation patterns
│   │   ├── LEARN-007 — Common generation errors + fixes (grows)
│   │   └── LEARN-00x — [grows: new libraries, edge cases, validated patterns]
│   ├── code/
│   │   ├── CODE-001 — IStrategy template v1.0
│   │   ├── CODE-002 — VectorBT runner template
│   │   ├── CODE-003 — CCXT data fetcher patterns
│   │   ├── CODE-004 — Test scaffolding templates
│   │   ├── CODE-005 — Validation pipeline implementation
│   │   └── CODE-00x — [grows: reusable snippets, indicator recipes]
│   ├── rules/
│   │   ├── RULE-001 — Import whitelist
│   │   ├── RULE-002 — Code style conventions
│   │   ├── RULE-003 — Testing requirements
│   │   └── RULE-004 — Security guardrails
│   └── logs/
│       ├── LOG-001 — Generation success/failure log
│       └── LOG-002 — Project timeline
```

## Rationale

### Why knowledge-first, not guess-and-check
Without ingested knowledge, an LLM guesses at APIs and produces code that looks right but fails on execution (hallucinated methods, wrong parameter names, deprecated patterns). Pre-ingested LEARN and CODE files give the Coder agent validated patterns to draw from. Research confirms: few-shot examples from working code improve Pass@1 by up to 13.79% (SCoT, ACM TOSEM 2024).

### Why template-fill for strategies
Template-based generation eliminates entire categories of errors: missing imports, structural errors, lifecycle bugs. The LLM fills only variable sections (indicator logic, signal conditions, parameters) within a known-good IStrategy skeleton. Production systems like NexusTrade (24K users) take this further — LLM produces JSON config, engine executes.

### Why full generation for non-strategy code
Data pipelines, CCXT integrations, and utility modules don't have a fixed template shape. The Coder generates complete files guided by brain CODE files (validated patterns), Architect/Planner specs, and Context7 API reference.

### Why three-tier knowledge (brain → Context7 → GitHub)
Brain files capture project-specific knowledge (conventions, validated patterns, known gotchas). Context7 provides current API reference auto-updated every 10-15 days. GitHub is the fallback for source-level questions. This mirrors LEARN-028's finding: Context7 answers "how does this library work?" while brain answers "how does OUR project use it?"

## Interface / Contract

### Input: CONTEXT-PACK from Orchestrator

```markdown
---
task_id: "coder-042"
source: orchestrator
target: coder
task_type: implement | test | fix | refactor
plan_ref: "architect-plan-007"
---
# Task: [description]

## Plan (from Architect/Planner)
[What to build, file paths, function signatures, interfaces to satisfy]

## Acceptance Criteria
[Checkboxes — what must pass for this task to be complete]

## Relevant Brain Files
[Fat index entries the Coder should reference]

## Constraints
[Import restrictions, style rules, performance requirements]
```

### Output: RESULT to Orchestrator

```markdown
---
task_id: "coder-042"
source: coder
status: complete | partial | blocked
confidence: high | medium | low
validation: passed | failed
stages_passed: [ast, imports, tests, dry_run]
---
# RESULT: [description]

## Files Written
[List of files with one-line descriptions]

## Validation Evidence
[Stage-by-stage pass/fail with details]

## Implementation Notes
[Decisions made during implementation]

## Discoveries
[New knowledge for Orchestrator to deposit]
```

### How the Coder Writes Code

1. **Search brain** for relevant patterns (indicator recipes, similar strategies, gotchas)
2. **Query Context7** for current API signatures if brain doesn't cover it
3. **Use few-shot examples** from CODE files (2-3 validated implementations)
4. **Reason about control flow** before generating (SCoT pattern)
5. **Template-fill** for IStrategy files; **full generation** for non-strategy code

### How the Coder Tests Code

Every task produces **code and tests**:
- **Unit tests** — individual functions and methods
- **Integration tests** — strategy loads in Freqtrade, CCXT calls work with mocks
- **Property tests** — DataFrame operations preserve shape, signals are binary

Pre-built fixtures: `sample_dataframe` (200 OHLCV candles), `mock_exchange` (CCXT mock), `minimal_config` (Freqtrade dry-run config).

### How the Coder Proves Code (Validation Pipeline)

```
Stage 1: AST Parse    → Syntax valid? Structure correct?
Stage 2: Import Check → Only allowed modules? No dangerous ops?
Stage 3: Test/Dry-Run → pytest passes? Freqtrade dry-run completes?
```

On failure: extract specific error → feed back to LLM → regenerate failing component.
**Max 3 rounds** per task (diminishing returns beyond this, per LLMLOOP ICSME 2025).

## Constraints

### Import Whitelist (strategy files — strict)

```python
ALLOWED_IMPORTS = {
    # Core Python
    "datetime", "typing", "dataclasses", "enum", "math", "functools",
    "collections", "itertools", "decimal", "logging",
    # Data
    "numpy", "pandas",
    # Indicators
    "talib", "talib.abstract", "technical", "technical.indicators",
    # Freqtrade
    "freqtrade.strategy", "freqtrade.vendor.qtpylib.indicators",
    "freqtrade.persistence",
    # Exchange
    "ccxt",
    # Testing
    "pytest", "unittest.mock",
}
```

Non-strategy files (data pipelines, scripts): relaxed whitelist — allow pathlib, json, csv for file I/O.

### Security Guardrails

- **Whitelist, never blacklist** for imports
- No network calls (socket, urllib, requests, http blocked)
- No filesystem writes in strategy files (os, shutil blocked)
- No code execution (exec, eval, compile, __import__ blocked)
- No serialization (pickle, shelve, marshal blocked)
- No system access (subprocess, ctypes, multiprocessing blocked)
- 30-second timeout on dry-run execution
- 512MB memory limit (container-level if available)

### Knowledge Ingestion Phases

- **Phase 1 (seed):** Freqtrade docs/GitHub, freqtrade-strategies, CCXT docs, ta-lib
- **Phase 2 (expand):** VectorBT, Optuna, pytest, Context7 MCP integration
- **Phase 3 (accumulate):** Error patterns, validated snippets, consolidation every ~20-30 files

## Open Questions

1. Architect/Planner agent design — how do they communicate plans to Coder? (needs own SPEC)
2. CCXT async vs sync — which pattern for data fetchers?
3. Short/futures support — day-one or deferred?
4. Multi-timeframe template — include `informative_pairs()` scaffold?
5. VectorBT template details — deferred to CODE-002
6. How to ingest GitHub repos — clone + extract, or use GitHub MCP?
7. CCXT scope — focus on top 5 exchanges (Binance, Bybit, OKX, Kraken, Coinbase)?

## Changelog
- 2026-02-17: Created from first draft (coder.agent.project.md) + research synthesis
