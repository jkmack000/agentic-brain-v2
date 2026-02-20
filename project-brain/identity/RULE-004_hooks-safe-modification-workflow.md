# RULE-004 — Hooks Safe Modification Workflow
<!-- type: RULE -->
<!-- tags: tool-pattern, hooks, settings-json, backup, rollback, safety -->
<!-- created: 2026-02-16 -->
<!-- status: ACTIVE -->
<!-- links: RULE-001, LEARN-008, LEARN-019 -->

## Rule Statement
Always create a backup of the working hooks configuration before making changes. Broken hooks fail silently and disable ALL hooks — not just the one you changed.

## Conditions
This rule applies every time you modify hooks in:
- `.claude/settings.local.json`
- `.claude/settings.json`
- Any file containing a `"hooks"` block

## Workflow

### Before modifying hooks
1. **Copy the current working file** to a `.backup` alongside it:
   ```
   cp .claude/settings.local.json .claude/settings.local.json.backup
   ```
2. **Verify the backup exists** before proceeding with edits

### After modifying hooks
3. **Restart the Claude Code session** (hooks snapshot at startup — RULE-001)
4. **Test that hooks still fire** — run a known trigger (e.g., edit a file to trigger PostToolUse, or exit to trigger Stop)
5. **If hooks are broken** (no output, Settings Error, silent failure):
   ```
   cp .claude/settings.local.json.backup .claude/settings.local.json
   ```
   Then restart the session again to restore working hooks.

### After confirming hooks work
6. **Keep the backup** until the next successful modification. Only overwrite `.backup` when you have a new confirmed-working version.

## Why This Matters
- A single malformed field (wrong matcher type, bad JSON) silently disables ALL hooks — not just the broken one
- There is no error message in the session — hooks simply stop firing
- Without a backup, you must reconstruct the working configuration from memory or brain files
- Hooks are tested by observation (did it fire?) not by a validator — failures are discovered late

## Exceptions
- Trivial changes (e.g., editing only a hook's echo message, not its structure) may skip backup if you're confident in the change
- If the current hooks are already broken, there's nothing to back up — fix forward using RULE-001 patterns

## Source / Justification
During 2026-02-15 integration testing (LEARN-019), a matcher format change (`{}` object instead of string) silently disabled all 4 hooks. No error was displayed. The session exited without the Stop hook firing. The working configuration had to be reconstructed from session notes. A backup file would have made recovery instant.

## Evolution History
- 2026-02-16: Created — extracted from LEARN-019 integration failure experience

## Open Questions
- Whether to automate this as a PreToolUse hook that backs up settings.json before Edit/Write touches it (chicken-and-egg: the backup hook itself could break)
