# LEARN-012 — Brain Operational Drift: Template Divergence and Multi-Brain Sync
<!-- type: LEARN -->
<!-- tags: operational, drift, sync, templates, INIT-md, multi-brain, maintenance -->
<!-- created: 2026-02-14 -->
<!-- source: observed during project-brain development across multiple sessions -->
<!-- links: SPEC-000, LOG-002 -->

## Discovery
Two operational edge cases discovered as the brain system matures:

### 1. Template Drift — brain.py init vs. living INIT.md
The `brain.py init` command generates an INIT.md from a hardcoded template. But the manually-evolved INIT.md in project-brain has grown significantly beyond that template. It now includes:
- Mandatory LOG-002 timeline appending rule
- Deduplication rules for ingestion
- Periodic consolidation instructions
- User shorthand commands (Ingest, Deposit, Index, Handoff)
- SESSION-HANDOFF trigger conditions (80% context, task switches, milestones, etc.)

Any new brain created with `brain init` gets the old, minimal template — missing all these operational improvements.

### 2. Multi-Brain Sync — INIT.md content drift across brains
When multiple brains exist (e.g., project-brain + Donchian.bot/project-brain), their INIT.md files can diverge. Operational rules added to one brain's INIT.md don't propagate to others. Each brain independently evolves its operational rules, creating inconsistency.

## Context
Template drift noticed during the Tier 1 docs batch ingestion session when INIT.md was updated with the LOG-002 timeline rule. The Donchian brain's INIT.md was not updated. Multi-brain sync identified as a generalization of the same problem.

## Evidence
- brain.py `init` command contains a static INIT.md template (hardcoded in brain.py)
- project-brain/INIT.md has been modified at least 3 times since initial generation (dedup rules, shorthand commands, timeline rule, handoff triggers)
- Donchian.bot/project-brain/INIT.md has not received these updates

## Impact
- New brains start with stale operational knowledge
- Existing brains diverge on operational procedures
- User must manually propagate improvements across brains
- Violates the principle that the brain system should be self-maintaining

## Action Taken
Flagged for resolution. Two approaches to consider:
1. **Single source of truth:** INIT.md template lives as a file (not hardcoded), `brain init` copies it, `brain sync` propagates updates. INIT.md becomes versioned — brains track which version they have.
2. **Separate concerns:** Split INIT.md into two parts — project-specific content (stays per-brain) and operational rules (shared, version-synced). Operational rules could live in a separate file like `BRAIN-RULES.md` that `brain sync` manages.

Neither implemented yet. Priority: low until a third brain is created, at which point the problem becomes urgent.
