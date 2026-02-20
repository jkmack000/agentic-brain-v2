# RULE-003 — Skills and CLAUDE.md Patterns
<!-- type: RULE -->
<!-- tags: tool-pattern, skills, SKILL-md, CLAUDE-md, configuration, visibility, context-budget -->
<!-- created: 2026-02-16 -->
<!-- status: ACTIVE -->
<!-- links: LEARN-005, LEARN-007, LEARN-018, LEARN-019 -->

## Rule Statement
Skills and CLAUDE.md are the primary delivery mechanisms for brain knowledge into Claude sessions. These patterns prevent silent configuration failures.

## Patterns

### `disable-model-invocation: true` makes skills fully invisible to Claude
- **When:** Setting frontmatter in SKILL.md
- **Do:** Use `disable-model-invocation: false` (or omit) if Claude needs to see and invoke the skill. Use `true` only for user-only CLI shortcuts.
- **Consequence:** With `true`, the skill vanishes from Claude's system-reminder. The Skill tool fails. Claude cannot discover or invoke it at all — it behaves as if the skill doesn't exist.

### Skills in paths with spaces fail CLI resolution on Windows
- **When:** Project path contains spaces (e.g., `C:\Users\...\my project\...`)
- **Do:** Copy skills to user-level `~/.claude/skills/` which typically has no spaces
- **Note:** The Skill tool (model invocation) works fine from spaced paths — only `/skillname` CLI autocomplete fails
- **Consequence:** `/skillname` returns "Unknown skill" even though it appears in system-reminder

### Bloated CLAUDE.md causes critical rules to be ignored
- **When:** CLAUDE.md grows long and Claude starts missing important rules
- **Do:**
  1. Delete rules Claude already follows without being told
  2. Move rarely-needed knowledge to skills (loaded on demand)
  3. Convert enforced rules to hooks (deterministic, not LLM-interpreted)
  4. Add "IMPORTANT" or "YOU MUST" to truly critical rules
- **Consequence:** Claude treats long CLAUDE.md as noise. Critical rules are missed silently. More words = less compliance.

### `@` references auto-load CLAUDE.md from target directory
- **When:** Using `@brain-file.md` or `@directory/` in a prompt
- **Do:** Know that this also loads any CLAUDE.md in that file's directory and parents. Exploit this: place navigation CLAUDE.md files in brain subdirectories for automatic context injection.
- **Consequence:** Unintended CLAUDE.md files may be loaded (or you miss the opportunity to use this for zero-config context delivery)

### 2% context budget for all skill descriptions combined
- **When:** Adding new skills to a project
- **Do:** Keep total skill description text under 2% of context window (~2,800 tokens for 140K). Only skill descriptions are always-loaded — full skill content loads on invocation.
- **Consequence:** If descriptions exceed the budget, Claude falls back to 16K chars and may drop some skills entirely

### Supporting files pattern for large skills
- **When:** A skill's instructions exceed ~500 lines
- **Do:** Keep SKILL.md as the entry point under 500 lines. Put details in sibling files and reference them with `@supporting-file.md` or Read tool instructions.
- **Consequence:** Oversized SKILL.md consumes excessive context on every invocation

## Exceptions
- `@path` imports in CLAUDE.md work with spaces in Windows paths — no escaping needed
- Auto memory (MEMORY.md) is Claude-controlled and shouldn't be used for structured domain knowledge
- Managed policy (org-level) overrides all project-level CLAUDE.md

## Source / Justification
Extracted from LEARN-005 (best practices), LEARN-007 (skills reference), LEARN-018 (workflows), LEARN-019 (integration testing). Visibility and path issues confirmed through testing.

## Evolution History
- 2026-02-16: Created — extracted from LEARN-005, LEARN-007, LEARN-018, LEARN-019

## Open Questions
- Optimal CLAUDE.md size threshold (currently "under 500 lines" from Anthropic docs — may need tighter for brain projects)
- Whether skill `context: fork` is needed for brain operations that read many files
