# RULE-002 — Context and Session Management
<!-- type: RULE -->
<!-- tags: tool-pattern, context-window, compaction, sessions, subagents, clear, plan-mode -->
<!-- created: 2026-02-16 -->
<!-- status: ACTIVE -->
<!-- links: LEARN-005, LEARN-010, LEARN-018 -->

## Rule Statement
Protect the context window as the #1 resource — every tool call costs tokens you can't recover. These patterns prevent silent context degradation.

## Patterns

### Compaction loses early instructions — externalize critical state
- **When:** Session will run long enough to trigger auto-compaction (~95% context)
- **Do:** Put critical instructions in CLAUDE.md or .claude/rules/, not in conversation. Write SESSION-HANDOFF.md at ~80% context usage.
- **Consequence:** Detailed instructions from early in conversation silently vanish after compaction. Claude continues with incomplete knowledge.

### Use subagents for investigation, not the main context
- **When:** Need to read many files, explore a codebase area, or do deep research
- **Do:** Delegate to a subagent (Explore for read-only, general-purpose for broader). Main context receives only the summary.
- **Consequence:** Main context fills with intermediate file reads and tool outputs that are irrelevant after investigation completes.

### Skills save context vs. always-on CLAUDE.md
- **When:** Knowledge is only relevant for some tasks, not all
- **Do:** Put it in a skill file. Only the skill description lives in context until invoked (~2% budget for all skill descriptions).
- **Consequence:** Everything in CLAUDE.md is always loaded. Irrelevant knowledge consumes tokens every session.

### `/clear` after 2 failed corrections — never attempt a third
- **When:** You've corrected Claude on the same issue twice and it keeps repeating
- **Do:** `/clear` or `/rewind` and start fresh with a better prompt incorporating what you learned
- **Consequence:** Polluted context with multiple failed approaches. Claude treats failures as examples or gets confused by contradictory instructions.

### "ultrathink" / "think hard" are not special keywords
- **When:** You want Claude to reason more deeply
- **Do:** Set `CLAUDE_CODE_EFFORT_LEVEL=high` env var, or `MAX_THINKING_TOKENS` for a budget
- **Never:** Write "ultrathink" or "think hard" in prompts — treated as regular text
- **Consequence:** Silent failure — standard reasoning when you expected deep reasoning

### Plan Mode for read-only analysis
- **When:** You need exploration/search/analysis with zero risk of file modification
- **Do:** `claude --permission-mode plan -p "query"` (headless) or Shift+Tab toggle
- **Consequence:** Normal mode allows edits — exploration sessions can accidentally modify files

### Don't resume sessions in two terminals simultaneously
- **When:** You want to continue a session from a different terminal
- **Do:** Use `--fork-session` to create an independent copy
- **Consequence:** Both terminals append to the same session file. Messages interleave unpredictably.

### Session permissions are not restored on `--continue`
- **When:** Resuming a previous session
- **Do:** Expect to re-approve all permission prompts. Don't assume previous grants persist.
- **Consequence:** Automation breaks with unexpected permission prompts

### `--output-format json` includes cost metadata in headless mode
- **When:** Running Claude headlessly for automation and tracking costs
- **Do:** Pass `--output-format json` to get `cost` and `duration` fields in response

### Deposit first, implement second
- **When:** A prior session generated knowledge (framework, design, analysis) that exists only in conversation/handoff
- **Do:** Deposit undeposited knowledge into brain files BEFORE starting implementation work. This ensures knowledge survives even if the implementation session dies.
- **Consequence:** Knowledge lives only in ephemeral context. If the session crashes mid-implementation, both the knowledge AND the implementation are lost.

## Exceptions
- Subagent context isolation doesn't apply to the Task tool's returned summary — that does enter main context
- Subagents cannot spawn other subagents (no recursive delegation)
- Background subagents cannot use MCP tools

## Source / Justification
Extracted from LEARN-005 (best practices), LEARN-010 (architecture internals), LEARN-018 (workflows). Patterns validated through multiple sessions.

## Evolution History
- 2026-02-16: Created — extracted from LEARN-005, LEARN-010, LEARN-018

## Open Questions
- Optimal compaction threshold for brain sessions (80% handoff vs 95% auto-compact)
- Whether `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` should be lowered for brain-heavy sessions
