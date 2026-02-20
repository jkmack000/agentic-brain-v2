# LEARN-015 — Claude Code Agent Teams: Multi-Session Coordination for Brain Operations
<!-- type: LEARN -->
<!-- tags: claude-code, agent-teams, coordination, multi-agent, task-list, messaging, experimental -->
<!-- created: 2026-02-14 -->
<!-- source: code.claude.com/docs/en/agent-teams.md -->
<!-- links: SPEC-000, LEARN-005, LEARN-009 -->

## Discovery
Agent teams are a fundamentally different coordination layer from subagents. Teammates are full independent Claude Code sessions (not child processes), connected by a shared task list with dependency tracking and an inter-agent messaging mailbox. This is the pattern for coordinated parallel brain operations.

## Context
LEARN-009 covers subagents (child processes that report back to caller). Agent teams are structurally different: teammates form a mesh (any-to-any messaging), have their own full context windows, and coordinate via shared state (task list + mailbox). Experimental feature requiring `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.

## Key Details

### Four Components
| Component | Description |
|-----------|-------------|
| Team Lead | Main session that creates team, spawns teammates, coordinates |
| Teammates | Full independent Claude Code instances, each with own context |
| Task List | Shared, file-locked, with states (pending/in-progress/completed) + dependency tracking |
| Mailbox | Inter-agent messaging — direct (peer-to-peer) or broadcast (all teammates) |

### Inter-Agent Messaging
- **Direct messaging**: any teammate → any other teammate (not just lead)
- **Broadcast**: send to all teammates (costs scale with team size)
- **Automatic delivery**: no polling needed
- **Idle notifications**: teammates auto-notify lead when finished

Key difference from subagents: subagents report only to caller. Teammates form a mesh.

### Shared Task List Mechanics
- Three states: pending → in-progress → completed
- **Dependency tracking**: pending tasks with unresolved deps can't be claimed
- **File locking**: prevents race conditions on simultaneous claims
- **Self-claiming**: teammates can grab next unassigned, unblocked task
- Completing a task automatically unblocks dependents

Storage: `~/.claude/teams/{team-name}/config.json` + `~/.claude/tasks/{team-name}/`

### Delegate Mode
`Shift+Tab` cycles lead into coordination-only mode: spawning, messaging, shutting down, managing tasks. Lead cannot implement code. Pure orchestration role.

### Plan Approval Gates
Teammates work in read-only plan mode → submit plan to lead → lead auto-reviews and approves/rejects with feedback → rejected teammate revises in plan mode. Lead criteria configurable (e.g., "only approve plans that include test coverage").

### Quality Gate Hooks
- **TeammateIdle**: fires when teammate is about to go idle. Exit code 2 sends feedback and keeps teammate working.
- **TaskCompleted**: fires when task is being marked complete. Exit code 2 prevents completion with feedback.

Both events are already documented in LEARN-008's 14-event table. They are agent-team-specific — only fire during team sessions.

### Limitations
- No session resumption with in-process teammates
- Task status can lag (teammates sometimes fail to mark tasks completed)
- No nested teams (teammates can't spawn their own teams)
- Split panes not supported in VS Code terminal, Windows Terminal, or Ghostty
- One team per session at a time; lead is fixed for lifetime

### Context Loading
Teammates load project context (CLAUDE.md, MCP, skills) + spawn prompt. Lead's conversation history does NOT carry over. All necessary context must be in spawn prompt or CLAUDE.md/skills.

## Impact

### Brain Operations via Agent Teams
1. **Parallel ingestion**: spawn teammates per source document, lead deduplicates and consolidates. Teammates can message each other: "have you already covered X?"
2. **Parallel search with convergence**: teammates search different brain areas (SPEC vs LEARN vs RULE), share findings via messaging, converge on unified answer
3. **Brain maintenance team**: indexing, dedup detection, cross-reference validation, staleness checks — all parallel with dependency-aware task ordering
4. **Delegate mode for brain orchestration**: lead breaks down "consolidate all learnings about X" into tasks, assigns, synthesizes, never touches files directly

### Brain Quality Gates
- **TaskCompleted hook**: validate brain file format (frontmatter, tags, links) before allowing task to complete
- **TeammateIdle hook**: check for incomplete cross-references, send feedback to fix

### Cost Warning
Agent teams use ~7x more tokens than standard sessions (from costs docs). Brain maintenance via teams should be budgeted carefully.

### Context Independence is Critical
Teammates don't inherit lead's conversation. Brain files must be self-contained — all context (format rules, dedup rules, which files to read) must be in spawn prompt, CLAUDE.md, or skills.

## Action Taken
Deposited as LEARN-015. Agent teams identified as the coordination layer for complex brain operations (consolidation, parallel ingestion). Not yet available on stable — experimental flag required. No code written yet.
