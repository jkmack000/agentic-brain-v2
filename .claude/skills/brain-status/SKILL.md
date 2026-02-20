---
name: brain-status
description: Show Project Brain health — file counts, orphans, index coverage
disable-model-invocation: false
user-invocable: true
---

# Brain Status

Report the health and status of the Project Brain.

## Instructions

1. **Run brain.py status:** Execute `uv run project-brain/brain.py status` via Bash for file counts, orphans, stale entries, and hash manifest health.

2. **Read INDEX-MASTER.md:** Read `project-brain/knowledge/indexes/INDEX-MASTER.md` for open questions, tensions, and cluster data.

3. **Check SESSION-HANDOFF.md:** Read `project-brain/ops/SESSION-HANDOFF.md` if it exists — when was it last written?

4. **Report** a summary including:
   - Files by type (from brain.py status output)
   - Orphans and ghosts
   - Open questions count and any blocking tensions
   - Cluster status and squeeze points
   - Last handoff timestamp
   - Any issues found
