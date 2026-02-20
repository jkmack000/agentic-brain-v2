# LOG-003 — Brain-to-Claude Code Delivery Mechanism Analysis
<!-- type: LOG -->
<!-- tags: integration, delivery, skills, rules, imports, claude-code, architecture -->
<!-- created: 2026-02-14 -->
<!-- links: SPEC-000, LEARN-005, LEARN-006, LEARN-007, LEARN-008 -->

## Decision
Not yet made. This LOG captures the emerging architecture for how brain knowledge gets delivered into Claude Code sessions. Four mechanisms identified, each with different trade-offs.

## Alternatives Considered

1. **`.claude/skills/` (on-demand loading via slash commands)**
   - Pros: User-controlled, only loads when needed, supports `disable-model-invocation` for user-only workflows, follows Agent Skills open standard, supports dynamic context via `!`command`` preprocessing
   - Cons: 2% context budget limits total skill count (LEARN-007), requires explicit invocation, each skill needs its own SKILL.md file
   - Best for: Task-specific brain knowledge (e.g., `/brain-search`, `/deposit`, `/recall`), workflow playbooks

2. **`.claude/rules/*.md` (always loaded, path-scoped)**
   - Pros: Automatically loaded every session, supports path-specific conditional rules via YAML `paths` field with globs, maps directly to our RULE file type, modular
   - Cons: Always consumes context tokens even when irrelevant, no on-demand control, grows linearly with rule count
   - Best for: Session hygiene rules (always deposit, always handoff), coding standards, invariant constraints

3. **`@path` imports in CLAUDE.md**
   - Pros: Selective loading, supports relative paths, user approves on first use, can reference any brain file directly, max depth 5
   - Cons: Static — changes to brain files require CLAUDE.md updates, approval dialog on new paths, limited to files CLAUDE.md author anticipated needing
   - Best for: Stable reference material (architecture specs, API contracts), project-specific brain files that rarely change

4. **Auto memory (Claude writes for itself)**
   - Pros: Zero user effort, Claude decides what to remember, 200-line index + topic files, already converges on fat-index pattern (LEARN-011)
   - Cons: Claude controls content (not user-curated), may duplicate or conflict with brain system, still rolling out (opt-in), 200-line index cap
   - Best for: Session-to-session continuity for quick facts, not for structured domain knowledge

## Rationale
These mechanisms are **complementary, not competing**. The likely architecture is layered:
- **Rules** for always-on session hygiene (brain loading protocol, handoff rules, dedup rules)
- **Skills** for on-demand brain operations (search, deposit, recall, ingest)
- **@path imports** for stable project-specific knowledge (the project's SPEC-000 equivalent)
- **Auto memory** left to Claude for its own housekeeping, doesn't replace brain system

The open question is which to implement FIRST. Skills are highest-impact (they make brain operations native to Claude Code) but also highest-effort. Rules are lowest-effort (just `.md` files in a directory) but least powerful.

## Consequences
- Implementing skills requires designing SKILL.md files with proper frontmatter, supporting files, and dynamic context injection
- Rules implementation is trivial — copy brain RULE files to `.claude/rules/` with minor reformatting
- @path imports need a stable CLAUDE.md that references the right brain files
- All three can coexist — no exclusive choice needed
- brain.py may need a `brain export --target claude-code` command to automate the bridge

## Revisit Conditions
- When starting implementation (Phase 2) — choose the first mechanism to build
- When Claude Code's auto memory exits opt-in — reassess overlap with brain system
- After first real project (Donchian bot) reveals which delivery patterns are actually needed vs. theoretical
