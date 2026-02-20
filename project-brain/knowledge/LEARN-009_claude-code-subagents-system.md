# LEARN-009: Claude Code Subagents System
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://code.claude.com/docs/en/sub-agents -->
<!-- tags: claude-code, subagents, delegation, context-isolation, custom-agents, persistent-memory -->
<!-- links: SPEC-000, LEARN-005, LEARN-007 -->

## What Subagents Are

Specialized AI assistants running in their own context window with custom system prompt, specific tool access, and independent permissions. When Claude encounters a matching task, it delegates to the subagent, which works independently and returns results.

**Key constraint:** Subagents cannot spawn other subagents.

---

## Built-In Subagents

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **Explore** | Haiku (fast) | Read-only | File discovery, code search, codebase exploration. Thoroughness levels: quick/medium/very thorough |
| **Plan** | Inherits | Read-only | Research for plan mode |
| **General-purpose** | Inherits | All | Complex multi-step tasks needing both exploration and action |
| **Bash** | Inherits | Terminal | Running commands in separate context |
| **statusline-setup** | Sonnet | Config | `/statusline` configuration |
| **Claude Code Guide** | Haiku | Info | Questions about Claude Code features |

---

## Custom Subagent Locations (Priority Order)

| Location | Scope | Priority |
|----------|-------|----------|
| `--agents` CLI flag (JSON) | Current session only | Highest |
| `.claude/agents/` | Current project | High |
| `~/.claude/agents/` | All your projects | Medium |
| Plugin `agents/` | Where enabled | Lowest |

Same-name agents: higher priority wins.

---

## Frontmatter Fields

```yaml
---
name: code-reviewer          # Required. Lowercase + hyphens
description: Reviews code    # Required. Claude uses to decide delegation
tools: Read, Grep, Glob      # Optional. Inherits all if omitted
disallowedTools: Write, Edit # Optional. Denylist
model: sonnet                # Optional. sonnet/opus/haiku/inherit
permissionMode: default      # Optional. default/acceptEdits/dontAsk/delegate/bypassPermissions/plan
maxTurns: 50                 # Optional. Max agentic turns
skills:                      # Optional. Preloaded skill content
  - api-conventions
mcpServers:                  # Optional. MCP servers available
hooks:                       # Optional. Lifecycle hooks scoped to agent
memory: user                 # Optional. Persistent memory (user/project/local)
---

System prompt goes here in markdown body.
```

---

## Task Tool Restrictions

When running as main thread with `claude --agent`, control which subagents can be spawned:
```yaml
tools: Task(worker, researcher), Read, Bash  # Allowlist
```
`Task` without parens = spawn any. Omit `Task` = no spawning.

---

## Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard permission prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Auto-deny prompts (allowed tools still work) |
| `delegate` | Coordination-only for agent team leads |
| `bypassPermissions` | Skip all checks (caution!) |
| `plan` | Read-only exploration |

Parent `bypassPermissions` takes precedence, cannot be overridden.

---

## Persistent Memory

```yaml
---
name: code-reviewer
memory: user
---
```

| Scope | Location | Use When |
|-------|----------|----------|
| `user` | `~/.claude/agent-memory/<name>/` | Learnings across all projects |
| `project` | `.claude/agent-memory/<name>/` | Project-specific, shareable via VCS |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific, not committed |

When enabled:
- System prompt includes memory read/write instructions
- First 200 lines of `MEMORY.md` injected at startup
- Read, Write, Edit tools auto-enabled for memory management

**Tips:**
- Ask agent to consult memory before work, update after
- Include memory instructions in markdown body
- `user` scope recommended as default

---

## Foreground vs Background

- **Foreground** — Blocks main conversation. Permission prompts pass through.
- **Background** — Concurrent. Permissions pre-approved at launch. MCP tools unavailable. If blocked on permissions, can be resumed in foreground.

Toggle: ask Claude to "run in background" or press **Ctrl+B**. Disable with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.

---

## Resuming Subagents

Each invocation creates fresh context. To continue previous work, ask Claude to resume — preserves full conversation history. Transcripts stored at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.

Transcripts persist independently of main conversation compaction. Auto-cleanup after `cleanupPeriodDays` (default: 30).

---

## CLI-Defined Subagents

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer",
    "prompt": "System prompt here",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  }
}'
```

Session-only, not saved to disk. Useful for testing/automation.

---

## Preloading Skills into Subagents

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

Full skill content injected into subagent context (not just description). Subagents don't inherit parent's skills — must list explicitly.

---

## Disabling Subagents

In settings `permissions.deny`: `["Task(Explore)", "Task(my-agent)"]`
Or CLI: `claude --disallowedTools "Task(Explore)"`

---

## Gotchas

### Custom agents cannot be spawned via Task tool
Custom agents defined in `.claude/agents/*.md` are **user-invoked only** — the Task tool can only spawn built-in agent types (Explore, Plan, general-purpose, Bash, etc.). Attempting `subagent_type: "my-custom-agent"` in a Task call will fail. This constrains orchestration patterns that need custom agent personas.

**Workaround:** Inject the custom agent's full system prompt and instructions into a general-purpose Task prompt. This preserves the agent's knowledge but loses: `permissionMode` constraints, skill preloading, turn limits, and model selection. Test this pattern before depending on it for orchestrator designs.

### Background subagents denied Write permissions in default mode
When launching subagents with `run_in_background: true` under the default permission mode, Write and Bash file-write operations are **denied** (permissions pre-approved at launch only covers read operations). All background subagents complete research successfully but cannot write files. **Workaround:** Resume the subagent in foreground to extract its content, or have the main agent read the subagent's output and write files itself.

## Key Takeaways for Brain System

1. **Brain searcher subagent.** Create a custom `.claude/agents/brain-searcher.md` that has read-only access to brain files and uses Explore model (Haiku) for fast, cheap lookups. Keeps brain search out of main context.
2. **Persistent memory = parallel brain.** Subagent memory (`MEMORY.md` + topic files, 200-line index) independently converges on our fat-index architecture. Could complement rather than replace.
3. **Brain depositor subagent.** Custom agent with Write access to brain dirs, model: haiku for cost efficiency. Auto-deposits discoveries at end of session.
4. **Skills preloading** for brain-aware agents — load relevant SPEC/RULE files as skills into specialized subagents.
5. **Background subagents** for brain maintenance — indexing, consolidation, dedup as async background tasks.
6. **CLI-defined agents for brain automation** — `claude --agents` with brain-specific config for CI/CD brain operations.
