# LEARN-017 — Claude Code Costs, Settings, and Environment Variables
<!-- type: LEARN -->
<!-- tags: claude-code, costs, settings, environment-variables, configuration, token-management, optimization -->
<!-- created: 2026-02-14 -->
<!-- source: code.claude.com/docs/en/costs.md, code.claude.com/docs/en/settings.md -->
<!-- links: SPEC-000, LEARN-004, LEARN-005, LEARN-006, LEARN-010 -->

## Discovery
Concrete cost numbers, complete settings.json schema, 5-level settings hierarchy with precise file paths, and 50+ environment variables for controlling model selection, token budgets, cost, and features. Provides the quantitative foundation for budgeting brain operations and the configuration surface for optimizing brain-powered sessions.

## Context
Existing LEARNs cover costs qualitatively (LEARN-004: "token economics"), settings conceptually (LEARN-006: CLAUDE.md hierarchy), and compaction behavior (LEARN-010). This fills the gap with specific numbers, complete key references, and environment variables.

## Key Details

### Cost Baseline
| Metric | Value |
|--------|-------|
| Average daily cost | **$6/developer/day** |
| 90th percentile | under $12/day |
| Team API usage | ~$100-200/developer/month (Sonnet 4.5) |
| Background token usage | under $0.04/session |
| Agent teams overhead | **~7x** standard sessions |
| Extended thinking budget | 31,999 tokens default (billed as output) |

Brain impact: 10-20% overhead from brain file loading = $0.60-$1.20/day. Brain maintenance via agent teams could cost $3-5+ per run.

**Research session cost benchmarks (measured 2026-02-17):** Each web-research-to-LEARN-file topic costs ~30-40K tokens via subagent (including web searches, reading results, synthesizing). A batch of 3 research topics costs ~100-125K tokens total including housekeeping (INDEX-MASTER, LOG-002, handoff). Chat log review across 8 sessions (~11MB JSONL) consumed ~5 parallel subagents at ~100-130K tokens each.

### Rate Limits by Team Size
| Team Size | TPM/User | RPM/User |
|-----------|----------|----------|
| 1-5 users | 200k-300k | 5-7 |
| 5-20 | 100k-150k | 2.5-3.5 |
| 20-50 | 50k-75k | 1.25-1.75 |
| 50+ | 10k-35k | 0.25-0.87 |

Limits are organization-level (individuals can burst). Brain automation competes with interactive usage for same pool — schedule maintenance during off-hours.

### Settings File Hierarchy (5 Levels)
```
Precedence (highest → lowest):
1. managed-settings.json    → IT-deployed (system paths)
2. CLI flags                → session-only
3. .claude/settings.local.json → personal, gitignored
4. .claude/settings.json    → team-shared, committed
5. ~/.claude/settings.json  → personal, all projects
```

Managed settings locations:
- macOS: `/Library/Application Support/ClaudeCode/`
- Linux/WSL: `/etc/claude-code/`
- Windows: `C:\Program Files\ClaudeCode\`

### Brain-Relevant Settings Keys
| Key | Type | Brain Use |
|-----|------|-----------|
| `model` | string | Default model per-project. Sonnet for brain maintenance. |
| `availableModels` | array | Lock to `["sonnet", "haiku"]` for brain maintenance repos |
| `cleanupPeriodDays` | number | Default 30. Controls session availability for `--resume`. Don't set to 0. |
| `outputStyle` | string | Tune for concise brain-compatible output |
| `respectGitignore` | boolean | Default true. Brain files in gitignored dirs won't appear in `@` picker unless false |
| `env` | object | Inject brain env vars without polluting shell profile |
| `disableAllHooks` | boolean | Emergency kill switch if brain hooks misbehave |
| `fileSuggestion` | object | Custom script for `@` autocomplete — wire to brain index |
| `$schema` | string | `"https://json.schemastore.org/claude-code-settings.json"` for IDE validation |

### Brain-Relevant Environment Variables
**Model control:**
| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_MODEL` | Override model globally |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model for subagents (use haiku for brain lookups) |
| `CLAUDE_CODE_EFFORT_LEVEL` | `low`/`medium`/`high` (Opus 4.6 only) |

**Token and context control:**
| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | 32,000 (max 64K) | Max output per response |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | model-dependent | Override for file reads — affects brain file truncation |
| `MAX_THINKING_TOKENS` | 31,999 | Extended thinking budget. Set lower for routine brain ops. |
| `MAX_MCP_OUTPUT_TOKENS` | 25,000 | Max MCP response. Brain MCP server responses under 10K. |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | ~95 | Trigger compaction %. Lower for brain sessions to compact earlier. |
| `ENABLE_TOOL_SEARCH` | `auto` (10%) | Defer MCP tools at threshold. `auto:5` for brain-heavy setups. |

**Cost control:**
| Variable | Purpose |
|----------|---------|
| `DISABLE_COST_WARNINGS` | Hide cost warnings |
| `DISABLE_PROMPT_CACHING` | **Do NOT set for brain projects** — caching benefits static brain files maximally |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS` | Disable flavor text model calls |

**Features:**
| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `1`=off, `0`=force on |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Enable agent teams |

All can be set via `env` key in settings.json for portability.

### Permissions Syntax (Complete)
```json
{
  "permissions": {
    "allow": ["Bash(npm run lint)", "Read(~/.zshrc)"],
    "deny": ["Bash(curl *)", "Read(./.env)", "Edit(./dist)"],
    "additionalDirectories": ["../project-brain/"],
    "defaultMode": "acceptEdits"
  }
}
```
**`additionalDirectories`** is the key mechanism for brain files stored outside project root.

### Cost Reduction Strategies
1. **CLAUDE.md under ~500 lines** — move specialized knowledge to skills
2. **Prompt caching** benefits static brain files maximally (loaded at session start, repeated)
3. **Skills load on-demand** — brain knowledge as skills saves base context
4. **Subagent model selection** — haiku for brain lookups
5. **Preprocessing hooks** — filter brain files to relevant sections before loading
6. **Code intelligence plugins** reduce unnecessary file reads

## Impact
- Brain operations are quantifiably budgetable ($6/day baseline, 7x for teams, $0.04 for background)
- Settings hierarchy enables layered brain config: org-wide policies → project settings → personal tweaks
- Environment variables provide fine-grained knobs for brain cost optimization
- `additionalDirectories` solves the cross-directory brain access problem
- Prompt caching is a free win for brain files — do not disable

## Action Taken
Deposited as LEARN-017. Cost baseline and settings reference established. Key optimization: `CLAUDE_CODE_EFFORT_LEVEL=low` for cheap brain maintenance, `CLAUDE_CODE_SUBAGENT_MODEL=haiku` for brain search subagents. No code written yet.
