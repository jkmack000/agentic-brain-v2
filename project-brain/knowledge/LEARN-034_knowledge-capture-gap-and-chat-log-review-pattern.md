# LEARN-034 — Knowledge Capture Gap and Chat Log Review Pattern
<!-- type: LEARN -->
<!-- tags: knowledge-capture, chat-logs, session-management, deposit-workflow, meta-insight, brain-architecture, usability -->
<!-- created: 2026-02-17 -->
<!-- source: Direct observation during quorum sensing implementation session — user reported inability to keep pace with knowledge generation -->
<!-- links: LEARN-032, SPEC-003, LEARN-019, SPEC-000, LEARN-010 -->

## Discovery

The brain system has a knowledge capture gap: insights generated in conversation evaporate unless someone manually deposits them. At production pace (dozens of decisions and insights per session), manual discipline fails. The user explicitly reported "I am barely keeping up with you now." This is a design constraint, not a user error — the system must capture knowledge transparently.

## Context

During the quorum sensing P0+P1 implementation session, the entire quorum framework (7 rules, Grok comparison, gap analysis, implementation plan) had been designed in the previous session but existed only in conversation. It survived only because the handoff was thorough. This session we deposited first, implemented second — much safer, but still relied on the user remembering to ask for deposits.

After implementation and skill testing, the stop hook fired and caught a stale handoff — proving the automated safety net works. But the hook only checks handoff freshness, not whether knowledge has been deposited. A fresh handoff with undeposited knowledge still loses information.

## Evidence

- Previous session: 7-rule framework + Grok comparison + gap analysis + implementation plan — all conversational, zero files written. Would have been lost without handoff.
- This session: 5 items identified as undeposited during end-of-session review (deposit-as-you-go rule, skill validation results, stop hook validation, chat-log-review pattern, pace problem).
- User quote: "I need you to capture all the knowledge and index it for the future."
- Claude Code stores full session transcripts locally — these are a recoverable knowledge source.

## The Three-Layer Solution

### Layer 1: Deposit-as-you-go rule (implemented)
A `.claude/rules/brain-deposit-as-you-go.md` file that changes LLM behavior: deposit decisions and insights immediately when they occur, don't batch at end of session. Seven triggers defined (design decision, contradiction, open question, insight, framework, comparison, unexpected result). Cheapest fix — loaded automatically every session.

### Layer 2: Chat log review
Claude Code stores session transcripts locally. These can be reviewed (by the LLM in a new session) to extract knowledge that was missed during the original session. This is a recovery mechanism — Layer 1 should catch most things, Layer 2 catches what slips through. Pattern: start new session → load chat log → scan for undeposited knowledge → deposit.

### Layer 3: Automated checkpoint (not yet implemented)
A `/brain-checkpoint` skill or enhanced stop hook that scans the conversation for undeposited knowledge before allowing session end. Would ask: "what knowledge from this conversation hasn't been deposited yet?" Most systematic but heaviest to build.

## Impact

- Adds `.claude/rules/brain-deposit-as-you-go.md` to every future session's behavior
- Establishes chat log review as a legitimate knowledge recovery workflow
- Identifies `/brain-checkpoint` as future P1-level enhancement
- Changes the brain's capture model from "pull" (user remembers to deposit) to "push" (system prompts for deposits)

## Action Taken

- Layer 1 implemented: `.claude/rules/brain-deposit-as-you-go.md` created and active
- Layer 2 identified: chat log review pattern documented here for future sessions
- Layer 3 deferred: `/brain-checkpoint` skill for future implementation

## Chat Log Location and Format (Resolved)

Claude Code stores full conversation transcripts as JSONL files:

- **Primary location:** `~/.claude/projects/<project-path-with-dashes>/<session-uuid>.jsonl`
- **Subagent transcripts:** `~/.claude/projects/<project>/<session-uuid>/subagents/agent-<hash>.jsonl`
- **Large tool outputs:** `~/.claude/projects/<project>/<session-uuid>/tool-results/toolu_<id>.txt`
- **User input history (all sessions):** `~/.claude/history.jsonl`

**JSONL format:** Each line is one JSON object with fields:
- `type`: `"user"` | `"assistant"` | `"progress"` | `"file-history-snapshot"` | `"tool_result"`
- `message.content`: The actual text content (user messages or assistant responses with text/tool_use blocks)
- `uuid`, `parentUuid`: For threading
- `sessionId`, `timestamp`, `cwd`, `version`, `gitBranch`: Metadata

**Chat log review workflow:** Start new session → load target session's JSONL → scan for `type: "user"` and `type: "assistant"` lines → extract insights not in existing brain files → deposit. Subagent transcripts are especially valuable — detailed research often evaporates when only summaries reach the main context.

**First review results (2026-02-17):** Reviewed ~11MB across 8 sessions for this project. Found 33 unique undeposited knowledge items. Biggest losses were in subagent transcripts (detailed Freqtrade IStrategy reference, LLM code generation research) where rich research was consumed at summary level.

## Known Issues

- ~~Chat log location and format not yet documented~~ → Resolved above
- Layer 1 adds deposit overhead mid-conversation — may slow down fast-paced sessions
- Layer 3 design not started — needs to decide: stop hook vs skill vs agent-based hook
- No measurement of how much knowledge typically goes undeposited per session (first data point: 33 items across 8 sessions, ~4 per session average)
