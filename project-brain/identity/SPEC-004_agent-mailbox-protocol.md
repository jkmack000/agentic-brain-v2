# SPEC-004: Agent Mailbox Protocol (AMP)
<!-- type: SPEC -->
<!-- created: 2026-02-19 -->
<!-- tags: multi-agent, IPC, communication, protocol, file-based, stigmergy, mailbox, Claude-Code -->
<!-- links: SPEC-001, LEARN-026, LEARN-027, LEARN-047, LEARN-009 -->

## Purpose
A lightweight file-based protocol for two or more Claude Code instances to communicate on the same machine. Zero infrastructure — the filesystem is the message bus.

## Design Principles
1. **No shared writes** — each agent owns its outbox directory. Others read only.
2. **Individual message files** — one file per message prevents append corruption.
3. **Sequence numbers** — monotonic ordering, gap detection for missed messages.
4. **Self-describing** — every message carries enough context to act on without history.
5. **Human-readable** — markdown files a human can inspect mid-conversation.

---

## Directory Layout

```
amp/                          ← shared root (any agreed-upon path)
├── PROTOCOL.md               ← this spec (agents read on first contact)
├── ROSTER.md                 ← agent registry (who's participating)
├── agents/
│   ├── alpha/                ← Agent Alpha's outbox (Alpha writes, others read)
│   │   ├── 001.md
│   │   ├── 002.md
│   │   └── ...
│   └── bravo/                ← Agent Bravo's outbox (Bravo writes, others read)
│       ├── 001.md
│       ├── 002.md
│       └── ...
└── shared/                   ← shared state (coordinated writes via claim files)
    ├── STATE.md              ← current task state, goals, progress
    └── ARTIFACTS.md          ← shared work products, references
```

## Agent Registration

On startup, each agent appends to `ROSTER.md`:

```markdown
## Agents

| ID | Role | PID | Started | Status |
|----|------|-----|---------|--------|
| alpha | orchestrator | 12345 | 2026-02-19T11:30:00 | active |
| bravo | specialist | 12346 | 2026-02-19T11:30:05 | active |
```

Agent IDs must be unique. Use simple names (alpha, bravo, coder, researcher, etc.).

---

## Message Format

Each message is a standalone `.md` file in the agent's outbox:

```markdown
<!-- amp-version: 1 -->
<!-- from: alpha -->
<!-- to: bravo -->
<!-- seq: 003 -->
<!-- type: REQUEST -->
<!-- timestamp: 2026-02-19T11:32:15 -->
<!-- re: bravo/002 -->

## Subject
Search the brain for MCP transport patterns

## Body
I need to understand how MCP stdio transport works on Windows.
Focus on gotchas and failure modes. Return a summary with file IDs.

## Context
Working on fixing MCP server hang. See shared/STATE.md for full context.

## Expected Response
- Summary of relevant findings (< 500 words)
- List of brain file IDs consulted
- Any new discoveries to deposit
```

### Required Fields
| Field | Description |
|-------|-------------|
| `amp-version` | Protocol version (currently `1`) |
| `from` | Sender agent ID |
| `to` | Recipient agent ID (`*` for broadcast) |
| `seq` | Sender's monotonic sequence number (zero-padded 3 digits) |
| `type` | Message type (see below) |
| `timestamp` | ISO 8601 timestamp |

### Optional Fields
| Field | Description |
|-------|-------------|
| `re` | Reference to a previous message (`agent-id/seq`) |
| `priority` | `low`, `normal` (default), `high`, `critical` |
| `ttl` | Time-to-live in minutes (message expires after this) |

### Message Types
| Type | Purpose | Expects Response? |
|------|---------|-------------------|
| `REQUEST` | Ask the other agent to do something | Yes |
| `RESPONSE` | Answer to a REQUEST | No |
| `STATUS` | Progress update, no action needed | No |
| `HANDOFF` | Transfer ownership of a task | Yes (ACK) |
| `ACK` | Acknowledge receipt | No |
| `ERROR` | Something went wrong | Depends |
| `DONE` | Agent is finished, signing off | No |

---

## Polling Protocol

Agents check for new messages by reading the other agent's outbox:

```
1. Glob: amp/agents/<other-agent>/*.md
2. Compare filenames against last-processed sequence number
3. Read any new messages in sequence order
4. Process and respond as needed
5. Repeat after completing current work unit
```

### Polling Frequency
- **Active conversation**: Check after each tool use or work unit
- **Background work**: Check every 3-5 tool uses
- **Idle/waiting**: Check every 30 seconds via Bash sleep loop

### Implementation (Claude Code)
```
# Check for new messages from bravo (agent alpha does this)
Glob: amp/agents/bravo/*.md

# Read the latest unprocessed message
Read: amp/agents/bravo/003.md

# Write response to own outbox
Write: amp/agents/alpha/004.md
```

---

## Shared State

`shared/STATE.md` is the coordination hub — both agents read it. Writes are coordinated via claim files:

### Write Coordination (Claim Protocol)
To modify a shared file:
1. Write a claim file: `shared/.claim-STATE-<agent-id>` with timestamp
2. Check for competing claims (other `.claim-STATE-*` files)
3. If no competing claims older than yours, proceed with the write
4. Delete your claim file after writing
5. If competing claim exists, wait and retry

```markdown
<!-- Example: shared/.claim-STATE-alpha -->
<!-- agent: alpha -->
<!-- timestamp: 2026-02-19T11:35:00 -->
<!-- target: STATE.md -->
Claiming STATE.md for update — adding progress on MCP fix.
```

This is optimistic locking — conflicts are rare with two agents on separate tasks.

### STATE.md Structure
```markdown
# Shared State

## Current Goal
Fix the MCP server search_brain hang on Windows.

## Task Assignments
| Task | Owner | Status |
|------|-------|--------|
| Diagnose root cause | alpha | complete |
| Test fix | bravo | in-progress |
| Update brain files | alpha | pending |

## Decisions Made
- Root cause: missing rank-bm25 in venv (not stdout issue)
- Fix: uv sync in project-brain directory

## Shared Artifacts
- Fix commit: 57bb11a
- Relevant brain files: LEARN-041, CODE-001
```

---

## Session Lifecycle

### Startup
1. Agree on `amp/` directory path (human sets this, or first agent creates it)
2. Each agent reads `PROTOCOL.md` (this file)
3. Each agent registers in `ROSTER.md`
4. Each agent creates its outbox directory: `amp/agents/<id>/`
5. First agent writes initial `shared/STATE.md` with goals

### During Work
1. Agents send REQUEST/RESPONSE messages through outboxes
2. Agents update `shared/STATE.md` via claim protocol for major milestones
3. STATUS messages for progress without requiring response
4. Agents poll each other's outboxes between work units

### Shutdown
1. Agent sends DONE message to all others
2. Agent updates ROSTER.md status to `done`
3. Last agent standing writes final STATE.md summary

---

## Error Handling

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Agent crashes | No DONE message, ROSTER still `active` | Surviving agent continues solo, notes in STATE.md |
| Sequence gap | Expected seq N, got N+2 | Send ERROR requesting resend, or proceed with warning |
| Stale claim | Claim file older than 2 minutes | Delete stale claim, proceed |
| Message too large | File > 10KB | Split into multiple messages with `part: 1/3` field |
| Conflicting writes | Both agents claim same shared file | Lower alphabetical agent-id wins (deterministic) |

---

## Example: Two-Agent Brain Research Session

**Setup**: Human launches two Claude Code instances on same project.

```
Human → Alpha: "You're the orchestrator. Research MCP patterns in the brain.
                Bravo will handle code changes. Shared dir: /tmp/amp/"

Human → Bravo: "You're the coder. Alpha will send you research findings.
                Make code changes as directed. Shared dir: /tmp/amp/"
```

**Message flow**:
```
alpha/001.md  → [REQUEST to bravo] Set up your outbox, ACK when ready
bravo/001.md  → [ACK to alpha] Ready. Awaiting instructions.
alpha/002.md  → [REQUEST to bravo] Fix brain.py line 518 — add try/except
                around rank_bm25 import with graceful fallback
bravo/002.md  → [STATUS to alpha] Working on it...
bravo/003.md  → [RESPONSE to alpha] Done. Added try/except, falls back to
                simple substring matching. Tested locally — passes.
alpha/003.md  → [REQUEST to bravo] Also create RULE-006 for uv venv hygiene.
                Here's the content: [...]
bravo/004.md  → [RESPONSE to alpha] RULE-006 written. INDEX-MASTER updated.
alpha/004.md  → [DONE to bravo] All tasks complete. Signing off.
bravo/005.md  → [DONE to alpha] Acknowledged. Signing off.
```

---

## Maker-Checker Patterns

The strongest use case for AMP: independent verification. L027 documents that without maker-checker, multi-agent systems have a **41-86.7% failure rate**. AMP gives you this natively because each agent has a separate context window — the reviewer can't be biased by the coder's reasoning.

### Why AMP beats sub-agents for verification

| Capability | Sub-agent reviewer | AMP reviewer |
|------------|-------------------|--------------|
| Run tests | Limited (no MCP, restricted Write in background) | Full tool access |
| Read full codebase | Yes but eats parent's context | Own 200K window |
| Iterate back-and-forth | Parent must re-spawn each round | Natural conversation |
| Independent judgment | Shares parent's context/bias | Completely separate context |
| Audit trail | Lost after sub-agent returns | Every message is a permanent file |
| Human can observe | Only sees final result | Can read both outboxes in real-time |

### Pattern 1: Review Gate

Alpha (coder) cannot commit until Bravo (reviewer) sends an ACK. Enforced by convention — Alpha's CLAUDE.md includes the rule "Do not `git commit` until you receive an ACK from Bravo."

```
alpha/001  [REQUEST] Review my changes to brain.py.
           Diff in shared/ARTIFACTS.md. Rationale: [...]

bravo/001  [RESPONSE] Two issues:
           1. try/except too broad — swallows all ImportErrors
           2. No test for the fallback path

alpha/002  [RESPONSE] Fixed both. Narrowed except, added test.
           Updated diff in shared/ARTIFACTS.md.

bravo/002  [ACK] Reviewed. All tests pass. Approved for commit.

alpha/003  [STATUS] Committed: abc1234
```

### Pattern 2: Test-Driven Development

Bravo writes tests first. Alpha implements to pass them. Bravo verifies.

```
bravo/001  [REQUEST] Tests written: test_search_fallback.py
           3 cases: missing dep returns error msg, installed dep returns
           results, partial install returns clear diagnostic.
           Implement to pass these.

alpha/001  [RESPONSE] Implementation done. Running tests...
           2/3 pass. Case 3 (partial install) failing — need clarity
           on what "partial install" means.

bravo/002  [RESPONSE] Partial = rank_bm25 installed but numpy missing
           (transitive dep). Updated test with mock. Re-run.

alpha/002  [RESPONSE] 3/3 passing.

bravo/003  [ACK] Verified independently. All green.
```

### Pattern 3: Adversarial Testing

Bravo's explicit role is to break Alpha's code. Bravo reads the implementation and crafts inputs/scenarios designed to cause failures.

```
bravo/001  [REQUEST] I've read your MCP server. Attacking now.
           Test 1: query with 500 search terms — does BM25 handle it?
           Test 2: file_id with path traversal: "../../etc/passwd"
           Test 3: concurrent search_brain calls — thread safe?

alpha/001  [RESPONSE] Good catches.
           1: BM25 handles it but slow (4.2s) — adding term limit
           2: Path traversal blocked — _resolve_file_id only searches
              within brain dirs. But adding explicit check.
           3: Not thread safe — FastMCP is single-threaded so OK for now.
              Documenting as known limitation.

bravo/002  [RESPONSE] Verified fixes 1+2. Confirmed 3 is safe given
           FastMCP's model. One more: what if INDEX-MASTER.md is deleted
           mid-search? Race condition with file ops.

alpha/002  [RESPONSE] Added existence check before parse. Returns
           clear error instead of traceback.

bravo/003  [ACK] Attack surface covered. No more findings.
```

### Pattern 4: Debug Ping-Pong

Alpha hits a wall — context is polluted with failed attempts. Fresh-eyes Bravo gets the full error context without the baggage.

```
alpha/001  [HANDOFF] I'm stuck. MCP search hangs at 159 tokens.
           Tried: stdout fix (57bb11a), restart, different queries.
           Error context in shared/ARTIFACTS.md.
           Full repro: run search_brain with any query.

bravo/001  [ACK] Taking over investigation.

bravo/002  [STATUS] Found it. Not stdout — rank_bm25 missing from venv.
           The lazy import inside build_bm25_index raises ModuleNotFoundError
           which FastMCP swallows as a hang. uv sync fixes it.

alpha/002  [RESPONSE] That explains why get_index worked — it never
           imports rank_bm25. Applying fix now.
```

### The Audit Trail

Every message file in `amp/agents/` is a **permanent, human-readable record** of:
- What code was written and why (coder's rationale)
- What the reviewer checked (test coverage)
- What failed and how it was fixed (debug history)
- The full chain of reasoning from both sides (provability)

This directly serves the provability requirement (R005): not just "it works" but a documented record showing independent verification occurred, what was tested, and what the outcome was.

---

## Scaling Notes

- **2 agents**: Direct messaging, no routing needed
- **3-5 agents**: Use `to: *` broadcasts for coordination, direct messages for tasks
- **5+ agents**: Consider an orchestrator agent that routes all messages (hub-and-spoke)
- **Cross-machine**: Mount shared directory via SMB/NFS, or switch to LEARN-047 (visual/CDP) for monitoring

## Known Issues
- No encryption — messages are plaintext on filesystem (fine for local, bad for sensitive data)
- Polling wastes tool calls — no filesystem watch/notify from Claude Code
- Claim protocol is optimistic — theoretically two agents could claim simultaneously (sub-second race window)
- No message queue guarantees — if agent crashes mid-write, partial files possible
- Claude Code has no persistent background loop — polling requires cooperative scheduling within the agentic loop
