---
name: brain-checkpoint
description: Scan conversation for undeposited knowledge and add to QUEUE.md
disable-model-invocation: false
user-invocable: true
---

# Brain Checkpoint

Scan the current conversation for knowledge that should be deposited but hasn't been yet. Add findings to the deposit queue.

## Instructions

1. **Read the queue:** Read `project-brain/ops/QUEUE.md` for existing pending items.

2. **Scan conversation memory** for undeposited knowledge:
   - Decisions made but not recorded as SPEC or LOG files
   - Contradictions discovered between existing knowledge and new findings
   - Insights or edge cases that emerged during work
   - Implementation details that would be useful in future sessions
   - Open questions that surfaced but weren't captured

3. **Dedup against brain:** For each candidate, run `/brain-search` (or scan INDEX-MASTER mentally) to check if it's already deposited. Skip anything already captured.

4. **Dedup against queue:** Skip anything already in QUEUE.md.

5. **Add new entries** to `project-brain/ops/QUEUE.md` under the `## Queue` section. Replace `_Empty — no pending deposits._` if present. Use the format:
   ```
   ### [TYPE] Short description
   - **Context:** Why this matters
   - **Links:** Likely connections (file IDs)
   - **Priority:** HIGH / MEDIUM / LOW
   - **Added:** YYYY-MM-DD
   ```

6. **Report:**
   ```
   ## Checkpoint Complete
   - Scanned: [N conversation exchanges]
   - New queue entries: [N]
   - Already deposited: [N skipped]
   - Queue total: [N pending]
   ```

7. **Offer next step:** Ask the user if they want to:
   - Deposit the HIGH priority items now (run `/brain-deposit` for each)
   - Leave them in the queue for a future session
   - Discard any entries that aren't worth keeping
