---
name: brain-deposit
description: Deposit new knowledge into the Project Brain with dedup checking
argument-hint: "[TYPE] [description] — e.g., LEARN discovered edge case in auth flow"
disable-model-invocation: false
user-invocable: true
---

# Brain Deposit

Create a new brain file with dedup checking and index update.

## Instructions

1. **Parse arguments:** Extract TYPE and description from: **$ARGUMENTS**
   - If TYPE is missing, ask the user. Valid types: SPEC, CODE, RULE, LEARN, LOG
   - If description is missing, ask the user what they want to deposit

2. **Dedup check:** Read `project-brain/knowledge/indexes/INDEX-MASTER.md` and scan all fat index entries for overlap with the proposed deposit. Report any related existing files:
   ```
   ## Dedup Check
   - Related: [FILE-ID] — [why it's related]
   - Related: [FILE-ID] — [why it's related]
   - Verdict: [NEW / ENRICH existing / SKIP duplicate]
   ```
   If verdict is ENRICH, ask the user whether to update the existing file or create a new one.
   If verdict is SKIP, explain why and stop (unless user overrides).

3. **Determine file number:** Find the highest existing number for this TYPE and increment by 1.

4. **Read the template:** Read `project-brain/templates/TEMPLATE-{TYPE}.md` for the correct format.

5. **Link check (Rule 2 — maximize binding sites):** Before writing, ensure the deposit has **minimum 3 links** (forward links to related files). Count links from the `<!-- links: -->` frontmatter. Tags do NOT count toward the minimum.
   - If under 3 links, suggest connections by scanning INDEX-MASTER for related files by tags/topic.
   - Show the user the proposed links and ask for confirmation.
   - Do NOT proceed with fewer than 3 links unless the user explicitly overrides.

6. **Open questions (Rule 3 — chemoattractant gradients):** Ask the user:
   > "What does this file NOT answer? What open questions remain?"
   - Add their response to the file under an `## Open Questions` or `## Known Issues` section (whichever fits the template).
   - If the user says "none", accept it — but prompt once.

7. **Write the file:** Create the new file in the correct v2 directory:
   - SPEC → `project-brain/identity/`
   - CODE → `project-brain/knowledge/`
   - RULE → `project-brain/identity/`
   - LEARN → `project-brain/knowledge/`
   - LOG → `project-brain/ops/`

8. **Schema validation:** Run `uv run project-brain/brain.py validate [file-path]` to check the new file passes schema.

9. **Update INDEX-MASTER.md:** Add a compressed-v1 fat index entry to `project-brain/knowledge/indexes/INDEX-MASTER.md` under the correct section. Update `total-files` count. Update backlinks on linked files.

10. **Confirm:**
   ```
   ## Deposited
   - File: [path]
   - Links: [N forward links, N backlinks updated]
   - Open questions: [added to INDEX-MASTER / none]
   - Schema: [PASS / warnings]
   - Index: Updated (total files: N)
   ```
