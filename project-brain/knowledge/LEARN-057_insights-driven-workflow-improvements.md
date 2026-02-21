# LEARN-057 — Insights-Driven Workflow Improvements from Usage Report Analysis
<!-- type: LEARN -->
<!-- tags: workflow, insights, CLAUDE-md, skills, hooks, friction, session-management, skill-first, MCP-debugging -->
<!-- created: 2026-02-21 -->
<!-- source: Claude Code /insights report analysis, 57 sessions over 10 days, 183 hours -->
<!-- links: L034, R005, R003, L012, L041 -->

## Discovery
Empirical usage analysis (57 sessions, 984 messages, 183 hours) revealed three high-impact improvements: (1) CLAUDE.md was bloated at ~130 lines causing rule-ignoring — slimmed to ~40 lines with protocol details moved to `.claude/rules/brain.md`, (2) ad-hoc execution of deposit/handoff workflows skipped steps — enforced via "skill-first rule" requiring `/brain-*` skill invocation, (3) MCP debugging consumed disproportionate session time — codified diagnostic rules to prevent misdiagnosis loops.

## Context
User ran `/insights` which analyzed all Claude Code sessions. The report identified top friction categories: wrong approach (28 events), MCP infrastructure breaks (12+ sessions), misunderstood intent (multiple sessions). Suggestions were cross-referenced with existing brain knowledge and implemented in a single session.

## Evidence
- **CLAUDE.md bloat**: 130 lines → 40 lines (69% reduction). Anthropic recommends <60 lines for leading teams. Excess content moved to `.claude/rules/brain.md` where it loads identically but doesn't crowd the primary instruction file.
- **Skill-first rule**: Insights showed 12 deposit sessions and 7 handoff sessions where steps were inconsistently followed. Adding the rule ensures the full checklist (dedup, link check, schema validation, commit) runs every time.
- **MCP debugging rules**: 49-minute hang from stdout wrapping, 5+ sessions with tool-loading failures. Rules now codify: check deps before assuming retry loops, never test MCP registration within current session, write handoff if restart needed.
- **Session freshness rule**: Multiple sessions showed Claude assuming continuity from previous sessions. Rule added: every session is FRESH unless explicitly stated otherwise.
- **INDEX-MASTER read-once rule**: Duplicate search results traced to reading INDEX-MASTER multiple times per operation.

## Impact
- `.claude/rules/brain.md` — expanded with 5 new rules (session freshness, MCP debugging section, skill-first rule, INDEX-MASTER read-once, planning confirmation)
- `CLAUDE.md` — reduced from ~130 to ~40 lines
- `.claude/skills/brain-deposit/SKILL.md` — added verification + auto-commit steps
- `.claude/skills/brain-handoff/SKILL.md` — added MCP/env issue tracking + auto-commit steps
- `.claude/settings.local.json` — added dependency pre-flight check to SessionStart hook

## Action Taken
All changes implemented and committed in session. Three commits:
1. `ba15b5e` — Slim CLAUDE.md, move protocol details to rules
2. `bc109be` — Add skill-first rule, insights-driven improvements to rules and skills
3. SessionStart hook dependency check (pending commit)
