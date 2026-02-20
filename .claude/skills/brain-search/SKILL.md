---
name: brain-search
description: Search the Project Brain using BM25 ranking with link propagation — finds relevant knowledge without opening files
argument-hint: "<query> — keywords to search for in brain indexes"
disable-model-invocation: false
user-invocable: true
---

# Brain Search

Search the Project Brain for knowledge matching the query. Uses BM25 scoring over fat indexes with structural boosts and link propagation.

## Instructions

### Primary: Use brain.py BM25 search
1. Run: `uv run project-brain/brain.py search "$ARGUMENTS"` via Bash
2. If the command succeeds, present the results directly to the user
3. If no matches found, suggest related terms the user could try

### Fallback: Manual scan (if brain.py fails)
If the Bash command fails (uv not available, Python error, etc.):
1. Read `project-brain/knowledge/indexes/INDEX-MASTER.md`
2. Check the Sub-Indexes section — if any sub-index cluster summary matches the query, also read that sub-index file
3. Search all fat index entries for terms matching: **$ARGUMENTS**
4. Rank by: Tags > Summary > Key decisions > Known issues > file name
5. Present results as a ranked list

### Always
- **Do NOT open any brain files** — results come entirely from fat index entries
- Ask the user if they want to open any of the matched files
