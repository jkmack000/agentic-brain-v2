# LEARN-056 — Chat Platforms as Inter-Session Message Bus for LLM Agents
<!-- type: LEARN -->
<!-- tags: inter-session,message-bus,Slack,communication,push-vs-pull,handoff,multi-agent,blackboard,coordination,context-window -->
<!-- created: 2026-02-21 -->
<!-- source: conversation analysis — bridging SESSION-HANDOFF.md limitations with real-time messaging -->
<!-- links: LEARN-026, LEARN-015, LEARN-047, LEARN-034, SPEC-001, LEARN-040 -->

## Discovery
Chat platforms (Slack, Discord, Teams) can serve as a push-based message bus between isolated LLM context windows, complementing pull-based file handoffs. The key insight is directionality: SESSION-HANDOFF.md requires the new session to know to check it (pull), while a chat channel allows the ending session to push state and the next session to receive chronological history. This pattern becomes genuinely valuable at the multi-agent scale — concurrent Claude Code instances coordinating through a shared channel is the blackboard pattern (LEARN-026) implemented on commodity infrastructure.

## Context
Emerged from discussing whether the Claude Slack app could be useful for a single-user developer. The interesting application isn't human-to-Claude chat — it's Claude-to-Claude coordination using Slack as the transport layer between sealed context windows.

## Evidence

### Push vs Pull Handoff Comparison
| Property | SESSION-HANDOFF.md (pull) | Chat channel (push) |
|----------|--------------------------|---------------------|
| Direction | New session reads file | Old session posts, new session reads history |
| Timing | End of session only | Continuous mid-session posting |
| Structure | Single doc, overwritten each time | Append-only log with timestamps |
| Multi-agent | One writer at a time | Multiple sessions post concurrently |
| Discovery | Must know to check the file | Chronological history, harder to miss |
| Latency | Zero (local file) | Network round-trip (API call) |
| Cost | Zero | API calls + potential token cost reading history |

### Implementation Path
- **Outgoing (session → channel):** `curl -X POST` to Slack webhook, triggered by Claude Code hooks (PostToolUse, Stop, or custom)
- **Incoming (channel → session):** SessionStart hook reads channel history via Slack API, injects as context
- **Reactive:** Slack bot could trigger new Claude Code sessions based on channel messages

### Where Each Pattern Wins
- **Single user, sequential sessions:** SESSION-HANDOFF.md wins — simpler, zero latency, zero cost, already implemented
- **Multiple concurrent agents:** Chat channel wins — append-only semantics, natural ordering, no write conflicts
- **Hybrid (multi-brain architecture from SPEC-001):** Architect brain and coder brain each in separate Claude Code instances, coordinating through shared channel. Channel provides real-time awareness that file-based handoff lacks.

### Relation to Existing IPC Patterns (LEARN-026)
Chat-as-message-bus maps to the **blackboard pattern** where INDEX-MASTER is the current blackboard. Slack adds: real-time notification (vs polling), natural message ordering, built-in history search, and zero custom infrastructure. Tradeoff: external dependency, network latency, and messages are less structured than brain deposits.

### Beyond Slack
The pattern generalizes to any persistent append-only channel:
- GitHub Issues/Discussions (already integrated with code)
- Discord channels (free, bot-friendly)
- Simple append-only log file on shared filesystem
- Redis pub/sub or NATS for low-latency machine-to-machine
- Even email (async, universally supported, archival)

The transport matters less than the pattern: **push-based, append-only, multi-writer, chronologically ordered**.

## Impact
- **Extends LEARN-026:** New IPC pattern — chat-as-blackboard. Not covered in the 6-framework survey.
- **Extends LEARN-034:** Addresses the knowledge capture gap — mid-session findings could be pushed to channel immediately rather than waiting for end-of-session deposit.
- **Relevant to SPEC-001:** Multi-brain architecture needs a coordination layer. Chat channel is lowest-friction option before building custom IPC.
- **Practical threshold:** Not worth implementing for single-user sequential sessions (our current mode). Worth prototyping when running 2+ concurrent Claude Code instances.

## Action Taken
Deposited as architectural pattern. No implementation — current single-session workflow is well-served by SESSION-HANDOFF.md + brain deposits. Revisit when multi-agent coordination becomes active (SPEC-001 scope).
