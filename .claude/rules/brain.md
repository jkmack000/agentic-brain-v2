# Brain Rules

## Session
- Every session is a FRESH session unless the user explicitly says otherwise. Never assume continuity from a previous session.
- Start: check ops/SESSION-HANDOFF.md, then search knowledge/indexes/INDEX-MASTER.md (don't open files speculatively)
- End: write ops/SESSION-HANDOFF.md + append LOG-002. Triggers: user ends session, high context, major milestone, task switch, going in circles
- Before moving topics, ask: "Is there anything from the last exchange that only exists in this conversation?" If yes, deposit it.
- When the user says "move on" or interrupts, immediately stop that line of work — do not re-attempt or justify.

## MCP Server Debugging
- MCP tools only load at session startup — never attempt to test/verify MCP server registration within the current session.
- If MCP tools aren't appearing: diagnose the config, write a handoff note, and tell the user to restart the session.
- When MCP calls hang, check for missing pip dependencies (e.g., rank-bm25) and stdout wrapping issues BEFORE assuming retry loops.

## Skill-First Rule
- When a task matches an existing `/brain-*` skill, ALWAYS invoke that skill rather than doing it ad-hoc from general knowledge. This ensures the full checklist runs every time.
- If unable to invoke the skill (e.g., mid-flow, context constraints), prompt the user: "This is a good time to run `/brain-deposit` (or `/brain-handoff`, etc.) — want me to invoke it?"
- Applies to: `/brain-deposit` for any knowledge deposit, `/brain-handoff` for session endings, `/brain-checkpoint` for queuing undeposited knowledge, `/brain-search` for brain lookups, `/brain-status` for health checks, `/brain-reweave` for backlink updates.

## Deposits
- Deposit immediately when: a decision is made, a contradiction found, an open question surfaces, an insight emerges, or an implementation produces unexpected results
- Before depositing, scan INDEX-MASTER for dupes. Outcomes: **new** (create file), **enrich** (update existing), **duplicate** (skip), **contradiction** (deposit + flag both)
- INDEX-MASTER.md should only be read ONCE per operation to avoid duplicate search results
- When editing index entries, double-check the correct line's summary — do not accidentally duplicate adjacent entries
- Verify file paths exist before claiming files are missing. If a fix requires a session restart, say so explicitly.
- Sequential file numbering — never reuse or skip
- Every new/modified brain file must update its INDEX-MASTER fat index entry (what | decisions | interface | issues)
- File naming: `LEARN-NNN_descriptive-slug.md`. Use templates from `project-brain/templates/TEMPLATE-{TYPE}.md`
- Source field MUST include URL and access date
- Index entry format: compressed-v1 per LEARN-046. Minimum 3 links per deposit (SPEC-003 quorum rule)

## Compressed-v1 Index Format
Each INDEX-MASTER entry is a single pipe-delimited line:
`ID|tags|→outlinks|←inlinks|summary|d:decisions|i:interface|!issues`
IDs abbreviated: L=LEARN, S=SPEC, C=CODE, R=RULE, G=LOG (e.g., L044 = LEARN-044)

## Three-Space Layout
- identity/ → SPECs + RULEs (WHO)
- knowledge/ → LEARNs + CODEs (WHAT)
- ops/ → LOGs + session state (HOW)

## Web Research Protocol
1. Fetch URL with WebFetch. Extract: core concepts, data structures, tradeoffs, benchmarks, quotes with attribution.
2. Assess novelty — search brain for overlap. >80% covered = skip or corroborate. New = proceed.
3. Deposit as LEARN — one file per distinct concept (not per URL). 3 insights = 3 files.
4. Tag aggressively — source domain (e.g., `database`, `search-engine`) + index property (e.g., `b-tree`, `inverted-index`, `compression`).
5. Link deliberately — min 3 links. If <3, state explicitly and ask user yes/no.

## What to Extract from Sources
For each index type/technique: data structure, query model, write cost, space overhead, scaling behavior, tradeoffs, relevance to LLM context/fat-index problem.

# currentDate
Today's date is 2026-02-20.
