# RULE-001 — Hooks Configuration Patterns
<!-- type: RULE -->
<!-- tags: tool-pattern, hooks, configuration, settings-json, windows, matcher, stop-hook -->
<!-- created: 2026-02-16 -->
<!-- status: ACTIVE -->
<!-- links: LEARN-008, LEARN-019 -->

## Rule Statement
Follow these exact patterns when writing Claude Code hooks — most failures are silent and disable all hooks, not just the broken one.

## Patterns

### Format: Matcher must be a string regex, never an object
- **When:** Writing any hook with a `matcher` field
- **Do:** `"matcher": "Edit|Write"` (string regex) or omit entirely
- **Never:** `"matcher": {"tools": ["Edit"]}` or `"matcher": {}`
- **Consequence:** Settings Error silently disables ALL hooks in the session

### Format: Use matcher-based schema (Claude Code 2.1.42+)
- **When:** Writing hooks in settings.json / settings.local.json
- **Do:** `{"matcher": "ToolName", "hooks": [{"type": "command", "command": "..."}]}`
- **Never:** Old flat format `{"type": "command", "command": "...", "blocking": false}`
- **Consequence:** Settings Error, all hooks silently disabled

### Stop hooks: Command-type only, never prompt-type
- **When:** Building a Stop hook that must reliably block session termination
- **Do:** `type: "command"` with exit code 2 to block, exit code 0 to allow
- **Never:** `type: "prompt"` — tested twice with correct format, failed both times
- **Consequence:** Block never fires — session exits even when it shouldn't

### Stop hooks: Always check `stop_hook_active`
- **When:** Any Stop hook that can return exit code 2
- **Do:** Read `stop_hook_active` from stdin JSON. If true, exit 0 immediately.
- **Consequence:** Hook blocks → Claude retries → hook blocks → infinite loop

### Stop hooks: Omit matcher entirely
- **When:** Writing a Stop hook
- **Do:** Do not include a `matcher` field at all
- **Consequence:** Hook errors or never fires

### Prompt-type hooks use `ok`/`reason`
- **When:** Writing a prompt-type hook response (PreToolUse, etc.)
- **Do:** Return `{"ok": true}` or `{"ok": false, "reason": "..."}`
- **Never:** `{"decision": "block"}` — that's for command-type hooks
- **Consequence:** Decision silently ignored

### Command-type hooks use `decision` in stdout
- **When:** Writing command-type hooks for UserPromptSubmit, PostToolUse, Stop, SubagentStop
- **Do:** Output `{"decision": "block", "reason": "..."}` to stdout
- **Never:** `{"ok": false}` — that's for prompt-type hooks
- **Consequence:** Decision silently ignored

### Async hooks cannot return decisions
- **When:** You want a hook to both run in background AND block/allow
- **Do:** Only use `"async": true` for fire-and-forget (logging, formatting, indexing)
- **Consequence:** Async hook output is discarded — blocking has no effect

### Hooks snapshot at startup — restart to test changes
- **When:** You modify hooks in settings.json / settings.local.json
- **Do:** Restart the Claude Code session completely before testing
- **Consequence:** You test the old version, not your fix

### Windows: Normalize paths before string matching in hooks
- **When:** A hook command checks whether a file path is inside a directory
- **Do:** `.replace(chr(92), '/')` in Python — uses `chr(92)` to avoid triple-escape chain
- **Never:** Direct string match like `'project-brain/' in path` on raw Windows paths
- **Consequence:** Paths arrive with `\` on Windows — match never succeeds

### SessionStart stdout is injected into context
- **When:** You want to dynamically inject information at session start
- **Do:** Write a SessionStart command hook that echoes to stdout
- **Note:** Only SessionStart supports `CLAUDE_ENV_FILE` for persistent env vars

## Exceptions
- `@path` imports in CLAUDE.md work with spaces in Windows paths — no escaping needed
- Managed hooks (org-level) may override these patterns — check org policy

## Source / Justification
All patterns extracted from LEARN-019 (integration testing) and LEARN-008 (hooks reference). Every "never" pattern was tested and confirmed broken during the 2026-02-14/15 integration sessions.

## Evolution History
- 2026-02-16: Created — extracted from LEARN-008, LEARN-019 integration test results

## Open Questions
- PreCompact hook not testable on demand — assumed correct (trivial echo)
- SessionEnd hooks for auto-handoff not yet tested
