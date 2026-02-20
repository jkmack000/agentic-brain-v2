# LEARN-005: Claude Code Official Best Practices (Anthropic)
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://www.anthropic.com/engineering/claude-code-best-practices (now redirects to https://code.claude.com/docs/en/best-practices) -->
<!-- tags: claude-code, best-practices, context-management, CLAUDE-md, prompting, workflows, subagents, headless, hooks, skills, verification, session-management -->
<!-- links: SPEC-000, LEARN-004, LEARN-013, LEARN-014, LEARN-017, LEARN-018 -->

## Core Constraint

**Context window is the #1 resource to manage.** Performance degrades as context fills. Everything in the conversation — messages, files read, command output — consumes tokens. A single debugging session can burn tens of thousands of tokens. Track usage continuously with a custom status line.

**Relevance to Brain System:** Directly validates our fat-index architecture (avoid loading files you don't need), SESSION-HANDOFF at 80% context, and the entire search→skip→load workflow.

---

## 1. Give Claude a Way to Verify Its Work

**Single highest-leverage practice.** Claude performs dramatically better when it can self-verify — run tests, compare screenshots, validate outputs.

| Strategy | Bad | Good |
|----------|-----|------|
| Provide verification criteria | "implement email validation" | "write validateEmail. test: user@example.com=true, invalid=false, user@.com=false. run tests after" |
| Verify UI visually | "make dashboard look better" | "[paste screenshot] implement this design, screenshot result, compare, list differences, fix them" |
| Address root causes | "the build is failing" | "build fails with [error]. fix it, verify build succeeds, address root cause not symptom" |

Verification can be: test suite, linter, Bash command, screenshot comparison, or the Chrome extension for UI testing.

---

## 2. Explore → Plan → Implement → Commit Workflow

Four-phase workflow using **Plan Mode** (Shift+Tab to toggle; Ctrl+G opens plan in editor):

1. **Explore** (Plan Mode) — Claude reads files, answers questions, no changes
2. **Plan** (Plan Mode) — Create detailed implementation plan; Ctrl+G opens plan in editor for direct editing
3. **Implement** (Normal Mode) — Code against plan, verify with tests
4. **Commit** (Normal Mode) — Descriptive commit + PR

**When to skip planning:** Scope is clear, fix is small (typo, log line, rename). If you could describe the diff in one sentence, skip the plan.

**Relevance to Brain System:** Maps to our search→reset→work session pattern. Plan Mode = search phase. RESET files = the plan artifact. Validates the idea that exploration and execution should be separated.

---

## 3. Provide Specific Context in Prompts

| Strategy | Bad | Good |
|----------|-----|------|
| Scope the task | "add tests for foo.py" | "test foo.py covering edge case where user is logged out, avoid mocks" |
| Point to sources | "why weird API?" | "look through git history of ExecutionFactory, summarize how API evolved" |
| Reference patterns | "add calendar widget" | "look at HotDogWidget.php for patterns, follow same pattern for calendar widget with month select + pagination" |
| Describe symptoms | "fix login bug" | "login fails after session timeout, check src/auth/ token refresh, write failing test, then fix" |

**Rich content input methods:**
- `@filename` — reference files directly (Claude reads before responding)
- Paste/drag images directly into prompt
- Give URLs for docs (use `/permissions` to allowlist domains)
- `cat error.log | claude` — pipe data in
- Tell Claude to self-fetch context via Bash, MCP, or file reads

**When vague is OK:** Exploration. "What would you improve in this file?" surfaces things you wouldn't think to ask.

---

## 4. CLAUDE.md Best Practices

Run `/init` to generate starter CLAUDE.md from project structure, then refine.

**Include:**
- Bash commands Claude can't guess
- Code style rules that differ from defaults
- Testing instructions and preferred test runners
- Repo etiquette (branch naming, PR conventions)
- Architectural decisions specific to the project
- Dev environment quirks (required env vars)
- Common gotchas or non-obvious behaviors

**Exclude:**
- Anything Claude can figure out by reading code
- Standard language conventions Claude already knows
- Detailed API docs (link instead)
- Information that changes frequently
- Long explanations or tutorials
- File-by-file codebase descriptions
- Self-evident practices ("write clean code")

**Key insight:** If Claude keeps ignoring a rule, the file is probably too bloated and the rule gets lost. If Claude asks questions answered in CLAUDE.md, the phrasing is ambiguous. Treat CLAUDE.md like code — review it when things go wrong, prune regularly.

**Emphasis tuning:** Add "IMPORTANT" or "YOU MUST" to improve adherence on critical rules.

**`@path` imports in CLAUDE.md:**
```markdown
See @README.md for project overview and @package.json for available npm commands.
# Additional Instructions
- Git workflow: @docs/git-instructions.md
- Personal overrides: @~/.claude/my-project-instructions.md
```

**File locations:**
- `~/.claude/CLAUDE.md` — all sessions globally
- `./CLAUDE.md` — project root, check into git for team sharing
- `./CLAUDE.local.md` — personal overrides, .gitignore it
- Parent directories — monorepo support (root + subdir both loaded)
- Child directories — loaded on demand when Claude works in those dirs

**Relevance to Brain System:** CLAUDE.md is the primary delivery mechanism for brain knowledge into Claude Code sessions. Consider generating CLAUDE.md content from brain files. The `@path` import syntax could point to brain files directly. The include/exclude rules are a quality checklist for our SPEC/RULE files.

---

## 5. Environment Configuration

### Permissions
- `/permissions` to allowlist safe commands (npm run lint, git commit)
- `/sandbox` for OS-level isolation
- `--dangerously-skip-permissions` — bypass all checks (only in sandboxed/offline containers)

### CLI Tools
Tell Claude to use `gh`, `aws`, `gcloud`, `sentry-cli` etc. for external services. Claude learns new CLIs via `--help`.

### MCP Servers
`claude mcp add` to connect Notion, Figma, databases, etc. Enables: implement from issue trackers, query DBs, analyze monitoring, integrate designs.

### Hooks
Deterministic automation — unlike CLAUDE.md (advisory), hooks guarantee execution.
- Run scripts at specific Claude workflow points
- Claude can write hooks for you: "Write a hook that runs eslint after every file edit"
- `/hooks` for interactive config or edit `.claude/settings.json`
- Use for: auto-formatting after edits, lint before commits, block writes to protected dirs

### Skills (SKILL.md)
On-demand knowledge and workflows in `.claude/skills/`:
```markdown
---
name: api-conventions
description: REST API design conventions
---
# API Conventions
- Use kebab-case for URL paths
- Use camelCase for JSON properties
```
- Claude applies automatically when relevant, or invoke with `/skill-name`
- `disable-model-invocation: true` for side-effect workflows (manual trigger only)
- Use instead of CLAUDE.md for domain knowledge that's only sometimes relevant

### Custom Subagents
`.claude/agents/*.md` — specialized assistants with own context and tool restrictions:
```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---
```

### Plugins
`/plugin` to browse marketplace. Bundle skills, hooks, subagents, MCP into installable units.

**Relevance to Brain System:** Skills are a natural delivery mechanism for brain knowledge — each SPEC/RULE/LEARN could potentially be exposed as a skill. Custom subagents could be generated from brain files for specialized review. Hooks could automate brain deposits (e.g., auto-deposit after each commit).

---

## 6. Communication Patterns

### Codebase Questions
Ask Claude questions like you'd ask a senior engineer:
- "How does logging work?"
- "How do I make a new API endpoint?"
- "What edge cases does CustomerOnboardingFlowImpl handle?"
- "Why does this call foo() instead of bar() on line 333?"

### Interview Pattern (Knowledge Elicitation)
For larger features, have Claude interview you:
```
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.
Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs.
Don't ask obvious questions, dig into the hard parts I might not have considered.
Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.
```
Then start a **fresh session** to execute the spec — clean context focused on implementation.

**Relevance to Brain System:** The interview pattern is directly applicable to `brain ingest` — when ingesting from a human expert rather than a document. Could formalize as a brain ingestion mode.

---

## 7. Session Management

### Course-Correct Early
- **Esc** — stop mid-action, context preserved, redirect
- **Esc+Esc or /rewind** — restore conversation and/or code to any checkpoint
- **"Undo that"** — revert changes
- **`/clear`** — reset context between unrelated tasks

**Critical rule:** If you've corrected Claude more than twice on the same issue, context is cluttered with failed approaches. `/clear` and start fresh with a better prompt incorporating what you learned.

### Context Management
- `/clear` frequently between tasks
- Auto-compaction triggers summarization preserving code, file states, key decisions
- `/compact <instructions>` for targeted compaction (e.g., `/compact Focus on the API changes`)
- Esc+Esc → select checkpoint → "Summarize from here" for partial compaction
- CLAUDE.md can control compaction: "When compacting, always preserve the full list of modified files and any test commands"

### Subagents for Investigation
Delegate research to subagents — they explore in separate context, report back summaries:
```
Use subagents to investigate how auth handles token refresh,
and whether we have existing OAuth utilities to reuse.
```
Also use for post-implementation review: `use a subagent to review this code for edge cases`

### Checkpoints
Every Claude action creates a checkpoint. Esc+Esc or /rewind to restore conversation only, code only, or both. Persists across sessions. Only tracks Claude's changes, not external processes.

### Resume
- `claude --continue` — resume most recent
- `claude --resume` — pick from recent sessions
- `/rename` to label sessions ("oauth-migration", "debugging-memory-leak")

---

## 8. Automation and Scale

### Agent SDK (formerly "Headless Mode")
`claude -p "prompt"` — no interactive session. For CI, scripts, pre-commit hooks. Now also available as a full programmatic library (see LEARN-014).
```bash
claude -p "Explain what this project does"
claude -p "List all API endpoints" --output-format json
claude -p "Analyze this log file" --output-format stream-json
```

### Multiple Sessions
- Desktop app: visual, isolated worktrees per session
- Web: Anthropic cloud VMs
- Agent teams: automated coordination with shared tasks and messaging

**Writer/Reviewer pattern:**
- Session A: "Implement rate limiter for API endpoints"
- Session B: "Review rate limiter in @src/middleware/rateLimiter.ts for edge cases, race conditions, pattern consistency"
- Session A: "Here's review feedback: [B output]. Address these issues."

### Fan-Out
Batch processing across many files:
```bash
for file in $(cat files.txt); do
  claude -p "Migrate $file from React to Vue. Return OK or FAIL." \
    --allowedTools "Edit,Bash(git commit *)"
done
```
`--allowedTools` restricts Claude's capabilities for unattended runs.

---

## 9. Common Failure Patterns (Anti-Patterns)

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Kitchen sink session** | One task, then unrelated task, context full of irrelevant info | `/clear` between unrelated tasks |
| **Over-correction loop** | Correct → wrong → correct → wrong, context polluted with failures | After 2 failed corrections, `/clear` + write better initial prompt |
| **Bloated CLAUDE.md** | Too long, Claude ignores important rules buried in noise | Ruthlessly prune. Delete rules Claude follows without being told. Convert to hooks. |
| **Trust-then-verify gap** | Plausible code that misses edge cases | Always provide verification (tests, scripts, screenshots). Can't verify = don't ship. |
| **Infinite exploration** | Unscoped "investigate" fills context reading hundreds of files | Scope narrowly or use subagents for exploration |

**Relevance to Brain System:** These anti-patterns are directly applicable to brain usage. "Kitchen sink" = loading too many brain files. "Bloated CLAUDE.md" = bloated SPEC/RULE files. "Infinite exploration" = speculative file opens that fat indexing prevents. Consider depositing these as a RULE file for brain session hygiene.

---

## Key Takeaways for Brain System

1. **CLAUDE.md as delivery mechanism:** Brain files could generate or populate CLAUDE.md via `@path` imports. Skills (.claude/skills/) are the on-demand equivalent — brain knowledge loaded only when relevant.
2. **Verification-first principle:** When depositing knowledge, include verification criteria — how would Claude prove this knowledge is correct?
3. **Interview pattern for ingestion:** Formalize human-expert ingestion using AskUserQuestion-style interview flow.
4. **Hooks for brain automation:** Auto-deposit after commits, auto-update INDEX-MASTER, auto-lint brain files.
5. **Custom subagents from brain files:** Generate specialized reviewers/analysts from SPEC/RULE content.
6. **Anti-patterns as RULE file:** The failure patterns section is directly depositworthy as brain session hygiene rules.
7. **Fan-out for brain operations:** Batch brain operations (consolidation, dedup, re-indexing) could use headless fan-out pattern.
