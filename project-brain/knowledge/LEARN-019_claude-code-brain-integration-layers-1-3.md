# LEARN-019 — Claude Code Brain Integration (Layers 1-3)
<!-- type: LEARN -->
<!-- tags: claude-code, integration, CLAUDE-md, rules, skills, hooks, automation, brain-delivery, testing, windows, matcher-format -->
<!-- created: 2026-02-15 -->
<!-- updated: 2026-02-15 -->
<!-- source: implementation session — built from plan based on LEARN-005 through LEARN-008, LOG-003 -->
<!-- links: SPEC-000, LEARN-005, LEARN-006, LEARN-007, LEARN-008, LOG-003 -->

## Discovery
Claude Code's native integration points (CLAUDE.md, .claude/rules/, .claude/skills/, hooks in settings.local.json) can fully automate Project Brain session management. No plugins, MCP servers, or external tooling required — just 8 local files eliminate the manual "read INIT.md" bootstrap.

## Context
Every session previously required manually telling Claude to "read INIT.md." With 22 brain files and fat indexing working well, the bottleneck shifted to session ergonomics — loading, depositing, handoff, and index hygiene were all manual. LOG-003 analyzed four delivery mechanisms; this session implemented the three simplest (rules, skills, CLAUDE.md @path imports). MCP server deferred as higher-effort.

## Evidence
Eight files created across three layers:

**Layer 1 — CLAUDE.md + Rules (always-on)**
- `CLAUDE.md` — Root bootstrap. Uses `@project-brain/INIT.md` import so INIT.md loads automatically every session. Contains quick reference for brain operations and lists available skills.
- `.claude/rules/brain-session-hygiene.md` — Enforces: check SESSION-HANDOFF at start, deposit discoveries during work, write handoff + LOG-002 entry at end. Lists all handoff triggers.
- `.claude/rules/brain-fat-index-discipline.md` — Enforces: index-first search, no speculative file opens, mandatory index updates on every brain file change.
- `.claude/rules/brain-ingestion-dedup.md` — Enforces: scan INDEX-MASTER before depositing, dedup outcomes (new/enrich/skip/contradiction), sequential numbering.

**Layer 2 — Skills (on-demand slash commands)**
- `/brain-search <query>` — Reads INDEX-MASTER.md, searches fat index entries for query terms, returns ranked results (strong/moderate/weak) without opening files.
- `/brain-deposit [TYPE] [desc]` — Guided deposit workflow: parse args, dedup check against index, read template, write file, update INDEX-MASTER.
- `/brain-handoff` — Immediate SESSION-HANDOFF.md write + LOG-002 timeline append. One command captures full session state.
- `/brain-status` — Counts files on disk vs index, finds orphans (unindexed) and ghosts (missing), reports by type, checks handoff recency.

**Layer 3 — Hooks (automated lifecycle events)**
Hooks require the **matcher-based format** as of Claude Code 2.1.42 (see "Hooks format migration" gotcha below). **CRITICAL:** The `matcher` field must be a **string** (regex pattern) or **omitted entirely** — NOT a JSON object. Using an object causes a Settings Error on startup that silently disables ALL hooks.
- `SessionStart` (command, non-blocking) — Echoes brain reminder into context. Matcher: omitted (matches all sessions).
- `PreCompact` (command, non-blocking) — Echoes "write handoff NOW" warning before context compaction. Matcher: omitted.
- `Stop` (command, blocking) — Python checks if SESSION-HANDOFF.md was modified in last 30 min. Exit 2 = block, exit 0 = allow. Includes `stop_hook_active` guard. Matcher: omitted. (Previously prompt-type — failed twice, switched to deterministic command-type.)
- `PostToolUse` (command, non-blocking) — On Edit/Write to brain .md files, reminds to update INDEX-MASTER. Uses `python -c` for JSON parsing. Matcher: `"Edit|Write"` (string regex, only fires on file modifications).

## Impact
- **Session bootstrap:** Automatic. CLAUDE.md loads INIT.md via @path, rules load via .claude/rules/. No manual action needed.
- **Brain operations:** Native slash commands replace manual workflows. `/brain-search`, `/brain-deposit`, `/brain-handoff`, `/brain-status`.
- **Handoff safety:** Stop hook blocks session end if handoff wasn't written. PreCompact hook warns before compaction.
- **Index hygiene:** PostToolUse hook catches brain file edits and reminds to update INDEX-MASTER.
- **Files affected:** Settings.local.json modified (hooks added alongside existing permissions). 8 new files created. Brain file count: 22 → 23 (this LEARN).

## Test Results (2026-02-15)
Integration tested across two sessions (BUILD session + fresh TEST session after restart).

**Layer 1 — CLAUDE.md + Rules**
- `@project-brain/INIT.md` import: **PASS** — works on Windows even with spaces in the parent path ("LTM SPECS"). INIT.md content appears in context automatically.
- 3 always-on rules: **PASS** — all three load into context automatically every session. No manual action needed.

**Layer 2 — Skills**
- All 4 SKILL.md files initially had `disable-model-invocation: true`, which hid them entirely from Claude's available skills list in the system-reminder. They did not appear at all — not just blocked from model invocation, but invisible. Fixed to `disable-model-invocation: false`. After session restart, all 4 appeared correctly.
- `/brain-search hooks`: **PASS** — returned 5 ranked results from fat index, correct strong/moderate/weak ranking.
- `/brain-status`: **PASS** — reported 23 files, 0 orphans, 0 ghosts, correct per-type counts.
- `/brain-handoff`: **PASS** — wrote SESSION-HANDOFF.md with full state + appended LOG-002 entry.
- `/brain-deposit`: **PASS** — Tested via dedup-check enrichment workflow. Correctly read INDEX-MASTER, identified LEARN-019 as enrichment target (not new file), proceeded with update.

**Layer 3 — Hooks**
- `SessionStart`: **PASS** — Confirmed working. Output appears in system-reminder as `'[Brain] Project Brain detected...'`.
- `PreCompact`: **NOT TESTABLE** — Requires hitting ~95% context. Simple echo command — logic is trivially correct. Accepted as-is.
- **2026-02-17 (production validation):** Stop hook fired successfully in production during quorum sensing session — correctly detected stale SESSION-HANDOFF.md and blocked exit. This validates the command-type approach from Fix 3.
- `Stop`: **PASS (after 3 fixes)** — Command-type hook with deterministic file mtime check. Blocks exit if SESSION-HANDOFF.md not modified in last 30 min. Three bugs fixed to get here:
  1. **Matcher format (Fix 1):** All hooks had `matcher` as JSON objects (`{}`) instead of strings. Caused Settings Error on startup that silently disabled ALL hooks. Fix: omit `matcher` for Stop.
  2. **Response format (Fix 2):** Prompt-type hook instructed LLM to respond with `{"decision": "block"}` but prompt-type hooks require `{"ok": false, "reason": "..."}`. Fixed format but hook still didn't block.
  3. **Prompt-type unreliable (Fix 3):** Abandoned prompt-type entirely. Switched to command-type with Python mtime check + exit code 2. **This worked.** Conclusion: prompt-type hooks are unreliable for Stop events — use command-type with exit codes instead.
  - SessionStart hook confirmed working after Fix 1 (proves hooks are loading).
- `PostToolUse`: **PASS (after fix)** — Originally failed due to Windows path separator bug (`project-brain\` vs `project-brain/`). Fixed with `.replace(chr(92),'/')`. String matcher `"Edit|Write"` verified: hook logic correctly detects brain file edits and generates INDEX-MASTER reminder. Hook output may be consumed silently by Claude Code (not always visibly displayed), but the logic is confirmed correct via manual stdin test.

## Gotchas and Patterns

### `disable-model-invocation` behavior
- `true` = skill is completely hidden from Claude's system-reminder skills list. Claude cannot see or invoke it. Only the user can invoke via `/` autocomplete.
- `false` (or omitted) = skill appears in system-reminder. Both Claude and user can invoke.
- This is correct per the skills spec (LEARN-007) but the total invisibility from system-reminder was not obvious during initial implementation.

### Windows path handling in hooks
- Hook commands that inspect `file_path` from tool input must handle both `/` and `\` separators.
- **Pattern:** Use `chr(92)` in Python one-liners to represent backslash without escaping. Example: `.replace(chr(92),'/')` normalizes all paths to forward slashes before any string matching.
- This avoids the JSON (`\\`) → bash (`\\`) → Python (`\\`) triple-escape chain where 8 backslashes in JSON produce 1 in Python.

### `@path` imports with spaces
- `@project-brain/INIT.md` resolves correctly on Windows even when the workspace path contains spaces (e.g., `C:\Users\...\LTM SPECS\project-brain\INIT.md`). No quoting or escaping needed in the CLAUDE.md `@path` reference.

### Hooks snapshot at startup
- All hooks are captured when Claude Code starts. Changes to settings.local.json require a session restart to take effect. This means hook fixes can't be verified in the same session they're applied.

### Hooks format migration (Claude Code 2.1.42+)
- Old format (flat): `{"type": "command", "command": "...", "blocking": false}` directly in the event array.
- New format (matcher-based): `{"matcher": "ToolName", "hooks": [{"type": "command", "command": "..."}]}` — each entry wraps hooks inside a matcher + hooks structure.
- The old format causes a **Settings Error** on startup with a message: `hooks: Expected array, but received undefined`.
- **CRITICAL: `matcher` must be a string (regex pattern) or omitted entirely.** Using a JSON object (e.g., `{}` or `{"tools": ["Edit", "Write"]}`) causes `matcher: Expected string, but received object` error that silently disables ALL hooks.
- For PostToolUse: `"matcher": "Edit|Write"` (string regex matching tool names).
- For SessionStart, PreCompact, Stop: omit `matcher` entirely (no filtering needed; Stop does not support matchers).
- Omitting `matcher` = match everything. Example: `{"hooks": [{"type": "command", "command": "echo hello"}]}`.
- The matcher-based format is cleaner for PostToolUse — tool filtering moves from Python logic to the matcher string, so the hook only fires on relevant tools.

### Prompt-type hook response format
- Prompt-type hooks (Stop, PreToolUse, etc.) must respond with `{"ok": true}` or `{"ok": false, "reason": "..."}`.
- Using `{"decision": "block"}` or `{"decision": "allow"}` does NOT work — those are for command-type hooks' JSON stdout.
- The `ok`/`reason` format is documented in LEARN-008 but easy to miss when writing hook prompts.
- **Stop hooks specifically** should also check `stop_hook_active` in the input to prevent infinite loops — if the hook blocks, Claude continues, then tries to stop again, triggering the hook again.

### Skills in paths with spaces (Windows)
- Skills in `.claude/skills/` under a project path containing spaces (e.g., `C:\Users\...\fuck windows\Desktop\LTM SPECS\.claude\skills\`) are **detected** by Claude Code (appear in system-reminder, work via Skill tool) but **fail to resolve via CLI `/` command** ("Unknown skill" error).
- **Workaround:** Copy skills to user-level `~/.claude/skills/` which typically has no spaces. This also makes them available across all projects.
- The user-level path takes precedence and resolves correctly. Both copies may appear in system-reminder (duplicates are harmless).
- Likely a bug in Claude Code's CLI command parser — the Skill tool uses a different resolution path that handles spaces correctly.

## Action Taken
All 8 files created and settings.local.json modified. Integration is live. Two post-build fixes applied:
1. `disable-model-invocation: true` → `false` in all 4 SKILL.md files (skills now visible).
2. PostToolUse hook: added `.replace(chr(92),'/')` path normalization for Windows compatibility.
Stop hook uses prompt type (blocking) — tested and FAILED (see test results). Root cause was object matchers, not prompt type itself.
3. Hooks migrated from flat format to matcher-based format (required by Claude Code 2.1.42+).
4. PostToolUse hook now uses `"Edit|Write"` string matcher instead of checking tool name in Python.
5. Skills copied to user-level `~/.claude/skills/` to work around spaces-in-path CLI resolution bug.
6. **2026-02-15 (recovery session, fix 1):** All `matcher` fields fixed from JSON objects to strings/omitted. `matcher: {}` → omitted; `matcher: {"tools": ["Edit", "Write"]}` → `"Edit|Write"`. SessionStart confirmed working. Stop hook still failed.
7. **2026-02-15 (recovery session, fix 2):** Stop hook prompt response format changed from `{"decision": "block/allow"}` to `{"ok": true/false, "reason": "..."}` per prompt-type hook spec (LEARN-008). Added `stop_hook_active` infinite loop guard. Still failed.
8. **2026-02-15 (recovery session, fix 3):** Abandoned prompt-type Stop hook entirely — unreliable (failed twice with correct format). Switched to command-type: Python checks `os.path.getmtime('project-brain/SESSION-HANDOFF.md')` < 1800s (30 min). Exit 2 blocks, exit 0 allows. `stop_hook_active` passed via stdin JSON. **PASS — successfully blocked exit.**
9. **2026-02-15 (cleanup session):** Removed 4 duplicate project-level skills from `.claude/skills/` (user-level copies in `~/.claude/skills/` are canonical). Verified PostToolUse hook logic via manual stdin test. Tested `/brain-deposit` skill (dedup check → enrich workflow). Deleted `test-session-handoff.md` artifact. All known issues now resolved except PreCompact (not testable on demand).
