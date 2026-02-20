---
name: brain-reweave
description: "Backward pass: update older files that should reference a new deposit"
argument-hint: "[FILE-ID] — e.g., LEARN-052 or --dry-run LEARN-052"
disable-model-invocation: false
user-invocable: true
---

# Brain Reweave

After a new file is deposited, check whether older files it links to should be updated to reference the new knowledge. This is the **backward pass** — the deposit creates forward links, reweave creates the backward awareness.

## Controls

- **1-hop only**: Only check files directly linked from the new deposit (outlinks)
- **Max 5 files**: Never update more than 5 files per reweave pass
- **Dry-run**: Pass `--dry-run` to preview changes without writing

## Instructions

1. **Parse arguments:** Extract FILE-ID and flags from: **$ARGUMENTS**
   - If FILE-ID is missing, ask the user which recent deposit to reweave
   - Check for `--dry-run` flag

2. **Load the deposit:** Read the file for FILE-ID from the brain
   - Extract its outlinks from `<!-- links: ... -->` frontmatter
   - Extract its core discovery/insight (first ## section content, ~2-3 sentences)
   - If the file has no outlinks, report "nothing to reweave" and stop

3. **Identify reweave candidates:** For each outlink target (1-hop only):
   - Read the target file
   - Ask: "Does this older file's content benefit from knowing about the new deposit?"
   - Score relevance: HIGH (the new deposit directly extends, validates, or contradicts this file), MEDIUM (related but tangential), LOW (only loosely connected)
   - Keep only HIGH and MEDIUM candidates
   - If more than 5 candidates, keep only the top 5 by relevance

4. **Preview changes (always show, even without --dry-run):**
   ```
   ## Reweave Plan for [FILE-ID]

   New deposit insight: [2-3 sentence summary]
   Outlinks: [list of linked file IDs]

   ### Candidates (N files)
   1. [TARGET-ID] — [HIGH/MEDIUM] — [what would be added]
   2. [TARGET-ID] — [HIGH/MEDIUM] — [what would be added]
   ...

   ### Skipped (N files)
   - [TARGET-ID] — LOW — [why not worth updating]
   ```

   If `--dry-run`, stop here and report the plan.

5. **Apply changes:** For each candidate:
   - Add a brief note to the target file's `## Impact` or `## Evidence` or `## Related Work` section (whichever exists, prefer Impact)
   - Format: `- **[FILE-ID]** ([date]): [1-2 sentence description of what the new deposit adds]`
   - If no suitable section exists, add a `## Related Developments` section at the end (before any `## Open Questions`)
   - Do NOT rewrite existing content — only append

6. **Update indexes:**
   - Update the fat index entry for each modified target file (update backlinks field)
   - Update LINK-INDEX.md if new edges were created
   - Do NOT modify the new deposit's own index entry

7. **Report:**
   ```
   ## Reweave Complete
   - Source: [FILE-ID]
   - Files updated: [N] of [M] outlinks checked
   - Files skipped: [N] (LOW relevance)
   - Index entries updated: [N]
   ```

## Scope Safety

- NEVER modify more than 5 files in a single reweave
- NEVER follow links beyond 1 hop (no cascading reweave)
- NEVER rewrite existing content in target files — only append
- NEVER modify the source deposit file itself
- If you're uncertain whether an update is warranted, skip it — false negatives are cheaper than false positives
