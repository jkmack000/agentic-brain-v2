---
name: brain-handoff
description: Write SESSION-HANDOFF.md immediately to capture current session state
disable-model-invocation: false
user-invocable: true
---

# Brain Handoff

Write `project-brain/ops/SESSION-HANDOFF.md` immediately, capturing the current session state.

## Instructions

1. **Read the template:** Read `project-brain/templates/TEMPLATE-SESSION-HANDOFF.md` for the format.

2. **Gather session state** from memory of this conversation:
   - What was being done this session
   - What's completed (cumulative across all sessions if known)
   - What's left / unfinished
   - Any uncommitted decisions or discoveries not yet deposited as brain files
   - Open questions
   - Files created or modified this session
   - Dead ends encountered
   - Recommended next session type and what to load

3. **Write the handoff:** Overwrite `project-brain/ops/SESSION-HANDOFF.md` with the gathered state. Include:
   - `<!-- written: YYYY-MM-DD HH:MM -->` timestamp
   - `<!-- session-type: ... -->` label
   - `<!-- trigger: ... -->` why the handoff was written

4. **Append LOG-002 timeline entry:** Add a dated entry to `project-brain/ops/LOG-002_project-timeline.md` summarizing this session.

5. **Confirm:**
   ```
   ## Handoff Written
   - SESSION-HANDOFF.md updated
   - LOG-002 timeline entry appended
   - Safe to end session
   ```
