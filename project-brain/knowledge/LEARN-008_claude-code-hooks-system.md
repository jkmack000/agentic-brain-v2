# LEARN-008: Claude Code Hooks System (Reference + Guide)
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://code.claude.com/docs/en/hooks + https://code.claude.com/docs/en/hooks-guide -->
<!-- tags: claude-code, hooks, automation, lifecycle, deterministic, configuration -->
<!-- links: SPEC-000, LEARN-005, LEARN-007, LEARN-015, LEARN-016 -->

## What Hooks Are

User-defined shell commands (or LLM prompts, or agents) that execute automatically at specific lifecycle points. Unlike CLAUDE.md instructions (advisory), hooks are **deterministic** — they guarantee execution.

**Three hook types:**
- `command` — Shell script. Receives JSON stdin, returns via exit code + stdout.
- `prompt` — Single-turn LLM evaluation. Returns `{ok: true/false, reason}`.
- `agent` — Multi-turn subagent with tool access. Same response format, up to 50 turns.

---

## Hook Lifecycle (14 Events)

| Event | When | Can Block? |
|-------|------|------------|
| `SessionStart` | Session begins/resumes | No |
| `UserPromptSubmit` | Prompt submitted, before processing | Yes |
| `PreToolUse` | Before tool call executes | Yes |
| `PermissionRequest` | Permission dialog appears | Yes |
| `PostToolUse` | After tool call succeeds | No (already ran) |
| `PostToolUseFailure` | After tool call fails | No |
| `Notification` | Claude sends notification | No |
| `SubagentStart` | Subagent spawned | No |
| `SubagentStop` | Subagent finishes | Yes |
| `Stop` | Claude finishes responding | Yes |
| `TeammateIdle` | Agent team member about to idle | Yes |
| `TaskCompleted` | Task being marked complete | Yes |
| `PreCompact` | Before context compaction | No |
| `SessionEnd` | Session terminates | No |

---

## Configuration Structure

Three nesting levels:
1. **Hook event** (e.g., `PreToolUse`)
2. **Matcher group** (regex filter, e.g., `"Bash"`, `"Edit|Write"`)
3. **Hook handler(s)** (command/prompt/agent to run)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

### Hook Locations
| Location | Scope | Shareable |
|----------|-------|-----------|
| `~/.claude/settings.json` | All projects | No |
| `.claude/settings.json` | Single project | Yes (commit) |
| `.claude/settings.local.json` | Single project | No (gitignored) |
| Managed policy | Org-wide | Admin-controlled |
| Plugin `hooks/hooks.json` | When enabled | Bundled |
| Skill/agent frontmatter | While active | In component |

---

## Exit Code Protocol

- **Exit 0** — Success. Stdout parsed for JSON output. For SessionStart/UserPromptSubmit, stdout added as context.
- **Exit 2** — Blocking error. Stderr fed to Claude. PreToolUse blocks tool, UserPromptSubmit rejects prompt, Stop prevents stopping.
- **Other** — Non-blocking error. Stderr logged in verbose mode (Ctrl+O).

---

## Decision Control Patterns

| Events | Pattern | Key Fields |
|--------|---------|------------|
| UserPromptSubmit, PostToolUse, Stop, SubagentStop | Top-level `decision` | `decision: "block"`, `reason` |
| PreToolUse | `hookSpecificOutput` | `permissionDecision` (allow/deny/ask), `permissionDecisionReason`, `updatedInput` |
| PermissionRequest | `hookSpecificOutput` | `decision.behavior` (allow/deny), `updatedInput`, `updatedPermissions` |
| TeammateIdle, TaskCompleted | Exit code only | Exit 2 blocks, stderr is feedback |

### PreToolUse Can Modify Input
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": { "command": "npm run lint" },
    "additionalContext": "Environment: production"
  }
}
```

---

## Common Input Fields (All Events)
- `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`

Tool events add: `tool_name`, `tool_input`, `tool_use_id`

---

## Key Practical Patterns

### Desktop Notifications
```json
{ "hooks": { "Notification": [{ "matcher": "", "hooks": [{ "type": "command", "command": "osascript -e 'display notification...'" }] }] } }
```

### Auto-Format After Edits
```json
{ "hooks": { "PostToolUse": [{ "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" }] }] } }
```

### Block Protected Files
PreToolUse + Exit 2 for `.env`, `package-lock.json`, `.git/`

### Re-inject Context After Compaction
SessionStart with `compact` matcher — echo critical reminders back into context.

### Async Hooks
`"async": true` — runs in background, doesn't block. Output delivered on next conversation turn. Cannot return decisions. Only for `type: "command"`.

### Prompt-Based Quality Gates
```json
{ "hooks": { "Stop": [{ "hooks": [{ "type": "prompt", "prompt": "Check if all tasks are complete. Respond {ok: true} or {ok: false, reason: '...'}" }] }] } }
```

### Agent-Based Verification
```json
{ "hooks": { "Stop": [{ "hooks": [{ "type": "agent", "prompt": "Verify all tests pass. Run test suite and check results.", "timeout": 120 }] }] } }
```

---

## SessionStart Special Features

### Persist Environment Variables
Write `export` statements to `$CLAUDE_ENV_FILE`:
```bash
echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
```
Available in all subsequent Bash commands during session. Only SessionStart hooks have `CLAUDE_ENV_FILE`.

### Context Injection
SessionStart and UserPromptSubmit: stdout text added to Claude's context. Use for dynamic context loading.

---

## MCP Tool Matching
MCP tools follow pattern `mcp__<server>__<tool>`:
- `mcp__memory__.*` — all tools from memory server
- `mcp__.*__write.*` — any write tool from any server

---

## Security Notes
- Hooks run with full user permissions
- Quote shell variables (`"$VAR"`)
- Block path traversal (check for `..`)
- Use `$CLAUDE_PROJECT_DIR` for project-relative paths
- Skip sensitive files (.env, .git/, keys)
- Hooks snapshot at startup — mid-session changes require review

---

## Key Takeaways for Brain System

1. **SessionStart hooks for brain loading.** Auto-inject brain context on session start: `!`uv run brain.py recall "current-task"`` or echo INDEX-MASTER summary.
2. **PreCompact hooks for brain preservation.** Before compaction, dump critical brain context to preserve it through summarization.
3. **PostToolUse hooks for auto-deposit.** After git commits, auto-run brain deposit to capture what was done.
4. **Stop hooks as quality gates.** Prompt/agent hooks could verify session handoff was written before Claude stops.
5. **SessionEnd hooks for cleanup.** Auto-write SESSION-HANDOFF on session termination.
6. **UserPromptSubmit for brain-aware routing.** Intercept prompts, inject relevant brain context based on keywords.
7. **Async hooks for background indexing.** After file edits, async re-index brain files without blocking Claude.
