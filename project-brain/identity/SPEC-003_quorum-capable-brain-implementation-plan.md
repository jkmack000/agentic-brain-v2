# SPEC-003 — Quorum-Capable Brain Implementation Plan
<!-- type: SPEC -->
<!-- tags: quorum-sensing, implementation, INDEX-MASTER, brain-deposit, brain-status, backlinks, tensions, open-questions, clusters -->
<!-- created: 2026-02-17 -->
<!-- status: ACTIVE -->
<!-- links: LEARN-032, SPEC-000, LEARN-031, LEARN-003 -->

## Context

LEARN-032 defines a 7-rule quorum sensing framework for LLM knowledge management. This spec is the prescriptive implementation plan — what changes, in what order, and how each change maps to the framework rules.

## Decision

Implement quorum sensing in 4 priority tiers (P0→P3), where each tier is independently valuable and builds on the previous. All changes are additive — no existing functionality is removed or broken.

## Implementation Plan

### P0 — Index Structure (Rules 3, 4, 2)
These changes make INDEX-MASTER.md the coordination medium.

#### P0.1: OPEN QUESTIONS section in INDEX-MASTER.md
- **Rule:** 3 (chemoattractant gradients)
- **What:** Add an `## Open Questions` section after the fat index entries. Each entry: question text, source file(s), date first raised, status (open/researched/answered).
- **Format:**
  ```markdown
  ## Open Questions
  | Question | Source | Raised | Status |
  |----------|--------|--------|--------|
  | Frontend stack preference? | SPEC-001 | 2026-02-16 | open |
  ```
- **Seed:** Populate from SESSION-HANDOFF.md "Open Questions (Carried Forward)" section.

#### P0.2: TENSIONS section in INDEX-MASTER.md
- **Rule:** 4 (contradiction preservation)
- **What:** Add a `## Tensions` section. Each entry: tension description, files on each side, state (OPEN/BLOCKING/RESOLVED), evidence summary.
- **Format:**
  ```markdown
  ## Tensions
  | Tension | Side A | Side B | State | Notes |
  |---------|--------|--------|-------|-------|
  | Temporal vs topological decay | (Grok, common practice) | LEARN-032 (connection-based) | RESOLVED | Topological chosen — relevance is relationships not recency |
  ```
- **Seed:** Scan existing files for any contradictions or disagreements.

#### P0.3: Backlinks in fat index entries
- **Rule:** 2 (maximize binding sites)
- **What:** Add a `Backlinks:` field to each fat index entry listing files that reference it. Currently entries have `Links:` (forward references) but no reverse.
- **Method:** Scan all files' `<!-- links: ... -->` frontmatter, build reverse map, add `Backlinks:` to each index entry.

### P1 — Deposit & Status Enhancements (Rules 2, 3, 5, 6)
These changes enforce the framework at deposit time and surface system health.

#### P1.1: Minimum 3 links per deposit
- **Rule:** 2 (maximize binding sites)
- **What:** Update `/brain-deposit` skill to require minimum 3 links (forward links + tags count). Skill should warn if under threshold and suggest connections.

#### P1.2: Required "what this doesn't answer" in deposit
- **Rule:** 3 (chemoattractant gradients)
- **What:** Update `/brain-deposit` skill to prompt for open questions. Add the responses to the file's content AND aggregate into INDEX-MASTER.md OPEN QUESTIONS section.

#### P1.3: Tag cluster detection in `/brain-status`
- **Rule:** 5 (cluster quorum)
- **What:** `/brain-status` should group files by shared tags, identify clusters with 5+ files, and flag clusters approaching "mental squeeze point" (where fat index summaries can't capture the distinctions).

#### P1.4: Quiet file detection in `/brain-status`
- **Rule:** 6 (topological decay)
- **What:** `/brain-status` should list files with 0 inbound links (backlinks). These are candidates for review: reconnect, confirm quiet, or retire.

### P2 — Consolidation & Vitality (Rules 5, 6, 7)
These changes support the ongoing health of the brain.

#### P2.1: Synthesis vs maintenance consolidation distinction
- **Rule:** 5 (cluster quorum)
- **What:** Document two consolidation modes: (1) **Maintenance** — dedup, fix broken links, tighten summaries (safe, routine). (2) **Synthesis** — merge cluster into new understanding, create higher-level file, retire source files (significant, needs review). Consolidation prompts should distinguish which mode.

#### P2.2: Vitality scoring + retirement workflow
- **Rule:** 6 (decay)
- **What:** Score each file: inbound links + outbound links + tag count + recency of last reference. Surface in `/brain-status`. Provide retirement workflow: archive file to `project-brain/archive/`, remove from INDEX-MASTER, add note to LOG-002.

#### P2.3: CLUSTERS section in INDEX-MASTER.md
- **Rule:** 7 (index is the medium)
- **What:** Add `## Clusters` section grouping related files by detected tag overlap. Each cluster: name, member files, link density, squeeze-point assessment.

### P3 — Sub-Index Design (Rule 7)

#### P3.1: Sub-index design along cluster boundaries
- **Rule:** 7 (index is the medium)
- **What:** When INDEX-MASTER exceeds mental squeeze point, split into sub-indexes aligned with detected clusters (not arbitrary alphabetical or type-based splits). INDEX-MASTER becomes a directory of cluster summaries. Cross-cluster links preserved in master.
- **Trigger:** Not file count — the "mental squeeze point" where INDEX-MASTER can no longer be scanned in one pass without losing important distinctions.

## Consolidation Guide

### Two Modes

| Mode | Purpose | Risk | Review Required? |
|------|---------|------|-----------------|
| **Maintenance** | Dedup, fix broken links, tighten summaries, update stale entries | Low — no information loss | No — routine housekeeping |
| **Synthesis** | Merge cluster files into higher-level understanding, create new file(s), retire sources | Medium — files retired | Yes — human confirms retirements |

### Maintenance Mode

**Triggers:** Run maintenance when any of:
- INDEX-MASTER has entries with stale summaries (file content has evolved past the fat index)
- Broken backlinks detected (a file references a non-existent ID)
- Tag inconsistencies (same concept tagged differently across files)
- After a batch ingestion (new files may overlap with existing)

**Checklist:**
1. Run `/brain-status` — note orphans, ghosts, quiet files, count mismatches
2. Fix all orphans (add fat index entry) and ghosts (remove entry or restore file)
3. Scan quiet files — add missing backlinks where genuine references exist
4. Compare duplicate-candidate entries (similar tags, overlapping summaries) — tighten without merging
5. Verify all `<!-- links: -->` frontmatter matches actual references in file content
6. Update INDEX-MASTER `total-files` count
7. Rebuild content hashes (`uv run brain.py reindex`)
8. Commit with message: "Maintenance consolidation: [summary]"

### Synthesis Mode

**Triggers:** Run synthesis when:
- A tag cluster reaches "mental squeeze point" — fat index summaries can't capture distinctions between files
- Multiple files say the same thing from different angles with no unique contribution
- A cluster has accumulated enough knowledge to produce a higher-level understanding

**Checklist:**
1. Run `/brain-status` — identify the target cluster
2. Read all files in the cluster (this is one of the few times opening many files is justified)
3. Draft the synthesis file (new LEARN or SPEC) that captures the higher-level understanding
4. Identify source files that are fully subsumed by the synthesis — mark as retirement candidates
5. **Get human review** — present the synthesis + retirement list for approval
6. Deposit the synthesis file via `/brain-deposit`
7. Retire approved source files (see Retirement Workflow below)
8. Update all backlinks that pointed to retired files → point to synthesis file
9. Commit with message: "Synthesis consolidation: [cluster] — N files → 1, M retired"

### Vitality Score

Each file receives a vitality score measuring its connectedness in the brain graph:

```
vitality = (inbound_links × 3) + (outbound_links × 1) + (tag_count × 0.5)
```

- **Weights:** Inbound links matter most (being referenced = alive), outbound second, tags least
- **No recency factor** — Rule 6: topological, not temporal
- **Thresholds:**
  - `vitality < 2.0` → "review candidate" — may need link enrichment or retirement
  - `vitality < 1.0` → "retirement candidate" — likely orphaned or subsumed
- **RULEs exempt from low-vitality flags** — they are structurally leaf-type (consume knowledge but aren't referenced; LEARN-033 finding)

### Retirement Workflow

1. `/brain-status` flags retirement candidates (vitality < 1.0, excluding RULEs)
2. Human reviews and confirms which files to retire
3. Move file to `project-brain/archive/` (preserves git history, recoverable)
4. Remove fat index entry from INDEX-MASTER, add HTML comment: `<!-- retired: FILE-ID, YYYY-MM-DD, reason -->`
5. Update backlinks on files that linked TO the retired file (remove or redirect to replacement)
6. Update `total-files` count in INDEX-MASTER header
7. Rebuild content hashes (`uv run brain.py reindex`)
8. Append LOG-002 entry documenting the retirement
9. Commit with message: "Retire FILE-ID: [reason]"

### When NOT to Consolidate
- Don't consolidate files that cover the same topic from genuinely different angles (e.g., competitive analysis vs implementation guide)
- Don't consolidate across file types (a LEARN and a RULE about the same topic serve different purposes)
- Don't consolidate during a work session — consolidation is a dedicated session type
- Don't consolidate prematurely — wait for the mental squeeze point, not an arbitrary file count

## Sub-Index Format Spec

### When to Create a Sub-Index
- A tag cluster reaches "mental squeeze point" — fat index summaries can't capture distinctions
- Triggered by quality not count (though 10+ files in a cluster is a strong signal)
- First sub-index created at 48 files: `claude-code` cluster (15 files, 31% of brain)

### Sub-Index Structure
- **Location:** `project-brain/indexes/INDEX-{cluster-name}.md`
- **Header:** YAML-style HTML comments with type, cluster-tag, updated date, member-count, parent
- **Content:** Full fat index entries for all member files (moved from INDEX-MASTER, not copied)
- **Additions:** Vitality score per entry (not present in INDEX-MASTER entries)

### INDEX-MASTER Integration
- Individual file entries are removed from INDEX-MASTER (replaced with HTML comment noting the move)
- A **cluster summary entry** is added to the Sub-Indexes section:
  ```markdown
  ### {cluster-name} (Sub-Index)
  - **File:** indexes/INDEX-{cluster-name}.md
  - **Members:** N files (FILE-ID, FILE-ID, ...)
  - **Summary:** One-line description of what the cluster covers
  - **Squeeze point:** Active/approaching/no
  ```

### Cross-Cluster Links
- File IDs are globally unique — cross-references work regardless of which index contains the entry
- A file in the claude-code sub-index can link to a file in INDEX-MASTER and vice versa
- Backlinks reference file IDs, not index locations — no update needed when files move between indexes

### Search Workflow with Sub-Indexes
1. Scan INDEX-MASTER fat index entries (includes cluster summaries)
2. If cluster summary matches query → load the sub-index
3. Scan sub-index entries to find specific files
4. One extra hop, but saves tokens by not loading 15+ entries on every session

## Rationale

- **P0 first** because it's all additive structure in INDEX-MASTER — zero risk, immediate value, enables P1-P3.
- **P1 second** because it enforces quality at deposit time — every future file benefits.
- **P2 third** because it requires enough files + backlink data to be meaningful.
- **P3 last** because sub-indexes are triggered by squeeze point, not file count.

## Interface / Contract

- INDEX-MASTER.md gains 3 new sections: `## Open Questions`, `## Tensions`, `## Clusters`
- Fat index entries gain `Backlinks:` field
- `/brain-deposit` skill gains: link minimum check, open questions prompt
- `/brain-status` skill gains: cluster detection, quiet file detection, vitality scoring

## Constraints

- All changes must be backward-compatible — existing brain files remain valid
- No automatic decay or retirement — human review required for all removals
- Tensions are never auto-resolved — evidence accumulation only
- Sub-index split is never triggered by file count alone

## Open Questions

- ~~Should CLUSTERS section be auto-generated by `/brain-status` or manually maintained?~~ **RESOLVED:** Auto-generated by `/brain-status`, user pastes into INDEX-MASTER.
- ~~What vitality score threshold triggers the "review" flag?~~ **RESOLVED:** vitality < 2.0 = review candidate, < 1.0 = retirement candidate. RULEs exempt (leaf-type).
- ~~Should retired files be git-deleted or moved to `archive/` directory?~~ **RESOLVED:** Move to `project-brain/archive/` — preserves git history, recoverable.

## Implementation Status

- **P0:** COMPLETE (2026-02-17) — Open Questions (22 items), Tensions (4 items), Backlinks on all entries
- **P1:** COMPLETE (2026-02-17) — `/brain-deposit` enforces min 3 links + open questions; `/brain-status` reports quiet files, tag clusters, tensions/questions counts. Tested in production — all 9 deposit steps validated, topology data produced correctly.
- **P2:** COMPLETE (2026-02-17) — Consolidation guide (maintenance vs synthesis modes), vitality scoring formula (inbound×3 + outbound×1 + tags×0.5), retirement workflow with archive/, CLUSTERS section in INDEX-MASTER (8 clusters, claude-code largest at 15), OQs #13/#14/#15 resolved.
- **P3:** COMPLETE (2026-02-17) — First sub-index created: `indexes/INDEX-claude-code.md` (15 files). INDEX-MASTER restructured: individual entries replaced with cluster summary + HTML comments. Sub-index format spec documented. Cross-cluster links preserved.

## Changelog

- 2026-02-17: Created from SESSION-HANDOFF.md design decisions
- 2026-02-17: P0+P1 implemented and validated in production
- 2026-02-17: P2 implemented — consolidation guide, vitality scoring, retirement workflow, CLUSTERS section, archive/ directory, OQs resolved
- 2026-02-17: P3 implemented — first sub-index (claude-code, 15 files), sub-index format spec, INDEX-MASTER restructured
