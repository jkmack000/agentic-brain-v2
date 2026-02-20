# RULE-005 — User Prime Directive and Working Style
<!-- type: RULE -->
<!-- tags: user-preference, workflow, prioritization, scope-discipline, session-management -->
<!-- created: 2026-02-17 -->
<!-- status: ACTIVE -->
<!-- links: RULE-002, LEARN-034 -->

## Prime Directive

**Organized, trackable, provable work > token efficiency.**

When these goals conflict, always choose the path that produces committed, indexed, verifiable artifacts over the path that saves tokens.

## Lane Discipline

The user self-identifies as multi-directional — prone to exploring multiple directions and mixing contexts within a session. The assistant must:

1. **Enforce lane discipline** — resist scope expansion until current work is committed and proven
2. **One task at a time** — finish and commit before starting the next
3. **Name the lane change** — if the user pivots mid-task, explicitly acknowledge it, capture the abandoned task's state (SESSION-HANDOFF or Open Question), then proceed
4. **Don't enable tangents** — if a discussion produces an interesting but off-track idea, deposit it (LEARN/LOG/Open Question) and return to the current task

## Practical Implications

- Don't optimize a session plan for token efficiency at the cost of leaving work uncommitted
- Prefer smaller, committed increments over ambitious multi-file changes that risk session death
- When the user says "let's also..." mid-task, pause and ask: "Should we finish [current task] first?"
- Every session should produce at least one commit with deposited knowledge
