# LEARN-010: Claude Code Architecture & Internals
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://code.claude.com/docs/en/how-claude-code-works -->
<!-- tags: claude-code, architecture, agentic-loop, tools, context-window, sessions, checkpoints -->
<!-- links: SPEC-000, LEARN-005, LEARN-006, LEARN-013, LEARN-014, LEARN-017 -->

## The Agentic Loop

Three-phase cycle: **Gather context → Take action → Verify results**. Phases blend together. Claude chains dozens of actions, course-correcting at each step. User can interrupt at any point to steer.

Claude Code = the **agentic harness** around Claude models. It provides tools, context management, and execution environment that turn a language model into a coding agent.

---

## Models

- **Sonnet** — Handles most coding tasks well
- **Opus** — Stronger reasoning for complex architectural decisions
- Switch with `/model` during session or `claude --model <name>` at start

---

## Built-In Tool Categories

| Category | Capabilities |
|----------|-------------|
| **File operations** | Read, edit, create, rename, reorganize |
| **Search** | Find files by pattern (Glob), search content with regex (Grep) |
| **Execution** | Shell commands, servers, tests, git |
| **Web** | Search web, fetch docs, look up errors |
| **Code intelligence** | Type errors/warnings after edits, go-to-definition, find references (requires plugins) |

Plus orchestration tools: spawning subagents, asking user questions, etc. Full list at settings docs.

---

## What Claude Can Access

When you run `claude` in a directory:
- **Your project** — files in directory and subdirectories
- **Your terminal** — any command you could run
- **Your git state** — branch, uncommitted changes, recent history
- **Your CLAUDE.md** — persistent instructions
- **Extensions** — MCP servers, skills, subagents, Chrome extension

Sees whole project = can work across files. Different from inline assistants that see only current file.

---

## Session Model

### Independence
Each new session starts with fresh context window. No conversation history from previous sessions. Persistence via auto memory and CLAUDE.md only.

### Branch Awareness
Sessions tied to current directory. Branch switch = Claude sees new files but conversation history preserved. Parallel sessions via git worktrees (separate dirs).

### Resume & Fork
- `claude --continue` — Resume most recent (same session ID, messages append)
- `claude --resume` — Pick from recent sessions
- `claude --continue --fork-session` — New session ID, preserves history up to that point
- `/rename` to label sessions

**Session-scoped permissions NOT restored on resume** — must re-approve.

**Same session in multiple terminals** — messages interleave in same file. Use `--fork-session` for parallel work from same starting point.

---

## Context Window Management

Context holds: conversation history, file contents, command outputs, CLAUDE.md, loaded skills, system instructions.

### Auto-Compaction
When context fills:
1. Clears older tool outputs first
2. Summarizes conversation if needed
3. Preserves: your requests, key code snippets
4. May lose: detailed instructions from early in conversation

### Control Compaction
- Add "Compact Instructions" section to CLAUDE.md
- `/compact focus on the API changes` for targeted compaction
- `/context` to see what's using space
- `/mcp` to check per-server MCP context costs

### Skills & Subagents for Context Management
- Skills load on demand (only descriptions in context until invoked)
- `disable-model-invocation: true` keeps skill descriptions out entirely
- Subagents get their own fresh context — work doesn't bloat main conversation
- Subagent auto-compaction at ~95% capacity (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` to adjust)

---

## Safety Mechanisms

### Checkpoints
Every file edit snapshots current contents. Esc+Esc to rewind. Local to session, separate from git. Only covers file changes — not remote systems (databases, APIs, deployments).

### Permission Modes (Shift+Tab to cycle)
| Mode | Behavior |
|------|----------|
| Default | Asks before edits and commands |
| Auto-accept edits | Edits without asking, still asks for commands |
| Plan mode | Read-only tools only, creates plan for approval |
| Delegate mode | Coordinates through agent teammates only |

---

## Operational Gotchas

### `.claude/projects/` stale cache after project directory move
When a project is moved to a new directory path, Claude Code's `~/.claude/projects/` directory retains a cache keyed by the old path (path encoded with dashes replacing slashes, e.g., `C--Users-jkmac-Desktop-old-path`). This stale cache persists and should be manually deleted after a project move.

## Key Takeaways for Brain System

1. **Agentic loop validates search→work separation.** Claude's own architecture (gather→act→verify) mirrors our brain's search→reset→work pattern. Context-gathering is a distinct phase.
2. **Session independence = why brains exist.** Each session starts fresh — this is the fundamental problem brain systems solve. Auto memory partially addresses it, brain system does it comprehensively.
3. **Compaction = information loss.** "Detailed instructions from early in conversation may be lost" — this is why SESSION-HANDOFF exists and why critical knowledge must be in files, not conversation.
4. **Checkpoint safety net.** Brain operations that modify files are reversible via checkpoints. Less risk in brain automation.
5. **Fork sessions for brain experiments.** `--fork-session` to try different brain configurations without polluting the main session.
6. **MCP context cost monitoring.** If brain system uses MCP, `/mcp` shows per-server costs. Important for brain MCP wrapper design (LEARN-002 priority #1).
