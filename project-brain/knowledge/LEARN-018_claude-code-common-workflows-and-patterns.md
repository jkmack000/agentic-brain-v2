# LEARN-018 — Claude Code Common Workflows and Operational Patterns
<!-- type: LEARN -->
<!-- tags: claude-code, workflows, plan-mode, extended-thinking, recipes, automation, patterns -->
<!-- created: 2026-02-14 -->
<!-- source: code.claude.com/docs/en/common-workflows.md -->
<!-- links: SPEC-000, LEARN-005, LEARN-010, LEARN-014, LEARN-017 -->

## Discovery
The common-workflows page provides concrete operational recipes and several details not captured elsewhere: Plan Mode operational mechanics (headless plan mode, Ctrl+G editor export), extended thinking/adaptive reasoning configuration, four reusable workflow recipe shapes, session picker keyboard shortcuts, git worktree patterns for parallel sessions, and the `@` reference system's automatic CLAUDE.md loading behavior.

## Context
LEARN-005 covers conceptual workflows (4-phase pattern, verification, session management). This adds the concrete recipes, operational shortcuts, and configuration details. Deduplicated against all LEARN-004 through LEARN-010.

## Key Details

### Plan Mode — Operational Details
- **Shift+Tab** cycles permission modes: Normal → Auto-Accept → Plan Mode (→ Delegate with teams)
- **`--permission-mode plan`** flag starts fresh session in Plan Mode
- **Headless Plan Mode**: `claude --permission-mode plan -p "query"` — read-only analysis, zero file modification risk
- **Ctrl+G** opens the plan in default text editor for direct editing before Claude proceeds
- Default Plan Mode config: `{"permissions": {"defaultMode": "plan"}}` in settings.json

Brain-relevant: Headless Plan Mode is ideal for brain search — read-only, no file modification risk.

### Extended Thinking / Adaptive Reasoning
- Extended thinking is **enabled by default**
- **Opus 4.6 uses adaptive reasoning** — dynamically allocates thinking based on effort level (low/medium/high), not a fixed budget
- Other models use fixed budget up to 31,999 tokens
- `MAX_THINKING_TOKENS` env var limits budget. Set to 0 to disable entirely.
- `CLAUDE_CODE_EFFORT_LEVEL` env var controls Opus 4.6 effort
- **Alt+T** (Win/Linux) or **Option+T** (Mac) toggles thinking on/off mid-session
- **"think", "think hard", "ultrathink" are NOT special keywords** — treated as regular text, do not allocate thinking tokens
- Thinking tokens are billed as output tokens

Brain-relevant: `CLAUDE_CODE_EFFORT_LEVEL=low` for cheap brain maintenance. `high` for complex consolidation/dedup. "Ultrathink" in brain prompts would have no effect.

### Four Reusable Workflow Recipe Shapes
These concrete patterns could become RESET file templates:

**1. Explore** (overview → architecture → data models → specific component):
```
> give me an overview of this codebase
> explain the main architecture patterns
> what are the key data models?
> how is authentication handled?
```
Tip: Ask for a glossary of project-specific terms — high-value brain deposit for onboarding.

**2. Debug** (share error → get options → apply fix → verify):
```
> I'm seeing an error when I run npm test
> suggest a few ways to fix the @ts-ignore in user.ts
> update user.ts to add the null check
```
Key: provide command to reproduce + stack trace + whether intermittent or consistent.

**3. Refactor** (find targets → recommend → apply with constraints → verify):
```
> find deprecated API usage in our codebase
> suggest how to refactor utils.js
> refactor utils.js while maintaining same behavior
> run tests for the refactored code
```

**4. Test** (find uncovered → scaffold → edge cases → verify):
```
> find functions not covered by tests
> add tests for the notification service
> add edge case tests
> run the new tests and fix any failures
```

### PR Creation and Session Linking
- **`/commit-push-pr`** built-in skill — commits, pushes, opens PR in one step
- **Slack auto-posting**: if Slack MCP configured and channels in CLAUDE.md, auto-posts PR URL
- **`--from-pr <number>`**: resume session linked to a PR. Sessions auto-link when `gh pr create` is used.

### Session Picker Shortcuts
| Key | Action |
|-----|--------|
| P | Preview session content |
| R | Rename session |
| / | Search/filter |
| A | Toggle current dir ↔ all projects |
| B | Filter by current git branch |

`A` key means sessions accessible across projects — relevant for cross-project brain operations.

### Git Worktrees for Parallel Sessions
```bash
git worktree add ../project-feature-a -b feature-a
cd ../project-feature-a && claude
```
Each worktree needs its own environment setup. If brain files are in a git repo, worktrees enable parallel brain operations (consolidation in one, deposits in another).

### `@` Reference Behavior
- `@file.js` — includes full file content
- `@directory` — provides directory listing (not contents)
- `@server:resource` — fetches from MCP resources
- **Critical: `@` references also load CLAUDE.md from that file's directory and parent directories**

Brain-relevant: if brain directories contain their own CLAUDE.md with navigation hints, any `@brain-file` reference auto-loads brain navigation context. Zero-config discoverability.

### Headless Automation Patterns
- `--output-format json` includes cost + duration metadata — enables brain operation cost tracking
- `--output-format stream-json` for real-time per-turn JSON
- Package.json `scripts` pattern for brain lint: `"brain:lint": "claude -p 'validate brain files...'"

### Self-Documentation
Claude has built-in access to its own docs. Brain system instructions don't need to explain Claude Code features — reference them and Claude self-retrieves.

## Impact
- **Headless Plan Mode** (`--permission-mode plan -p`) is the ideal brain search mechanism — zero file modification risk
- **Four recipe shapes** → four RESET file templates for brain-guided workflows
- **Effort level** is a concrete cost optimization knob for brain operations
- **`@` reference CLAUDE.md loading** enables zero-config brain discoverability via directory-level CLAUDE.md files
- **Glossary generation** identified as high-value brain deposit for project onboarding
- **"ultrathink" is not special** — corrects common misconception, don't rely on it in brain prompts

## Action Taken
Deposited as LEARN-018. Four RESET template variants identified but not yet created. Headless Plan Mode identified as brain search implementation path. No code written yet.
