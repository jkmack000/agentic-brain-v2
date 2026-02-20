# LEARN-037 — Sandbox Agent SDK: Remote Coding Agent Execution
<!-- type: LEARN -->
<!-- tags: sandbox-agent, multi-agent, execution, isolation, HTTP, session-persistence, MCP, agent-agnostic, prover, infrastructure -->
<!-- created: 2026-02-17 -->
<!-- source: Web research across sandboxagent.dev (quickstart, architecture, custom-tools, session-persistence, security, llms.txt) -->
<!-- links: SPEC-001, LEARN-026, LEARN-027, LEARN-014 -->

## Discovery

Sandbox Agent is an open-source Rust CLI/SDK that runs coding agents (Claude Code, Codex, OpenCode, Amp, Pi) inside isolated sandbox environments and controls them over a universal HTTP/SSE API. It solves the problem SPEC-001 identifies: how to run specialist agents with isolation, persistence, and coordination.

## Architecture

### Core Components

```
Browser → Your Backend → Sandbox Agent Server (inside sandbox) → Agent Process
                              ↕ HTTP/SSE
                         Event Stream + Session State
```

1. **Client SDK** (TypeScript) — connects to server via HTTP
2. **Server** (Rust static binary) — runs inside the sandbox, manages agent lifecycle
3. **Agents** — lazily installed on first session creation (Claude Code, Codex, OpenCode, Amp, Pi)
4. **Event Stream** — universal schema covering tool calls, permissions, file edits across all agents

### Recommended Topology

Three-tier: browser → backend → sandbox. Backend handles auth, routing, session affinity. Sandbox Agent recommends **actors** (Rivet) over serverless functions — agent workloads need long-lived connections, session routing, and state persistence.

## Key Capabilities

| Feature | Detail | Prover Relevance |
|---------|--------|-----------------|
| **Agent-agnostic API** | One HTTP API for Claude Code, Codex, OpenCode, Amp, Pi | Could swap agent models per brain |
| **Session persistence** | In-memory, SQLite, Postgres, IndexedDB, Rivet Actors | Solves sub-agent statelessness (SPEC-001 Option B limitation) |
| **Session replay** | Configurable replay on reconnect (max 50 events / 12K chars) | Recovery after orchestrator restart |
| **Custom MCP tools** | MCP servers (stdio/http) per session | Brain search as MCP tool per sandbox |
| **Custom Skills** | SKILL.md + script files at `/opt/skills/{name}/` | Brain skills deployable per sandbox |
| **File system API** | Read, write, upload, mkdir, move inside sandbox | Code artifact management |
| **Inspector UI** | Built-in web debugger at `/ui/` | Debug specialist agent sessions |
| **Observability** | OpenTelemetry integration | Token/cost tracking per brain |
| **Security** | Backend-first auth, token-based access, RBAC | Per-brain access control |

## Installation & Usage

```bash
# Install
npm install -g @sandbox-agent/cli@0.2.x
# Or: curl -fsSL https://sandboxagent.dev/install.sh | sh

# Start server
sandbox-agent server --no-token --host 0.0.0.0 --port 2468
```

```typescript
// TypeScript SDK
const sdk = SandboxAgent.start({ baseUrl: "http://localhost:2468" });
const session = await sdk.createSession({
  agent: "claude",
  sessionInit: { cwd: "/", mcpServers: [] }
});
const result = await session.prompt([
  { type: "text", text: "Implement the Donchian strategy" }
]);
```

## Custom Tools

Two patterns for giving agents sandbox-local tools:

| Aspect | MCP Server | Skill |
|--------|-----------|-------|
| Mechanism | Agent connects via stdio/http/sse | Agent follows SKILL.md + runs scripts |
| Best for | Typed tool calls, structured protocols | Lightweight task-specific guidance |
| Setup | Bundle MCP server, upload, register via `setMcpConfig()` | Upload script + SKILL.md to `/opt/skills/` |

## Session Persistence

| Backend | Best For |
|---------|---------|
| In-memory | Local dev, ephemeral workloads |
| SQLite | Node.js apps, durable without DB server |
| Postgres | Distributed systems, shared state |
| IndexedDB | Browser apps |
| Rivet Actors | Sandbox orchestration with session routing |

Replay on reconnect: configurable `replayMaxEvents` (default 50) and `replayMaxChars` (default 12K).

## Security Model

- **Backend-first**: SDK runs on backend, not browser — sandbox credentials never reach client
- **Auth flexible**: Sessions, JWT, API keys — enforce before sandbox-bound requests
- **RBAC support**: Owner/Member/Viewer roles with differentiated capabilities
- **Proxy pattern**: Backend transparently forwards requests with internal credentials

## Deployment Options

E2B, Daytona, Docker, Vercel, Cloudflare, local development. Static binary — minimal runtime dependencies.

## Impact on Prover Architecture (SPEC-001)

Sandbox Agent could serve as a **fourth coordination option** alongside the three in SPEC-001:

| Option | Mechanism | Status |
|--------|-----------|--------|
| A | Git worktrees | Designed (Phase 2) |
| B | Claude Code sub-agents | MVP (Phase 1) |
| C | Agent teams | Deferred (experimental, 7x cost) |
| **D** | **Sandbox Agent** | **New option — evaluation needed** |

### Advantages over Option B (sub-agents)
- **Session persistence** — sub-agents are stateless; Sandbox Agent sessions survive across calls
- **MCP tools per session** — each brain can have its own brain-search MCP tool
- **Skills per sandbox** — brain skills deployable without global installation
- **Agent-agnostic** — could use different models per brain (Claude for Coder, cheaper model for data pipeline)
- **Inspector UI** — debug specialist sessions visually
- **File system API** — manage code artifacts in sandboxed environment

### Advantages over Option A (worktrees)
- **No git infrastructure** — sandboxes are isolated by design
- **HTTP API** — orchestrator controls agents programmatically, no shell scripts
- **Session replay** — recovery built-in

### Limitations
- **TypeScript SDK only** — no Python SDK (would need HTTP API directly)
- **Additional infrastructure** — requires running sandbox environments
- **Network dependency** — HTTP communication adds latency vs local sub-agents
- **Early project** — v0.2.x, API may change

### Recommended Evaluation Path
1. Test locally: install CLI, start server, create Claude Code session, send prompt
2. Test MCP tools: configure brain-search as MCP tool in sandbox session
3. Test persistence: create session, send prompts, disconnect, reconnect and verify replay
4. Compare latency/cost vs Option B sub-agents for same task

## Open Questions

1. Can Sandbox Agent sessions receive CONTEXT-PACK messages via the prompt API? (format compatibility)
2. What's the latency overhead of HTTP control vs native sub-agent spawning?
3. Can multiple Sandbox Agent servers run concurrently for parallel specialist brains?
4. How does the agent's file system interact with the host — can it access brain files?

## Rivet Actors — Brain Project Implications

Rivet actors (one of Sandbox Agent's persistence backends) have specific implications for the brain system:

- **Solves handoff loss:** Current model is lossy (SESSION-HANDOFF.md summarizes, next session reconstructs). Rivet actors hold full session state in memory between orchestrator calls — no lossy handoff needed between orchestrator rounds within a workflow.
- **Natural SPEC-001 orchestrator fit:** Each specialist brain (Coder, Donchian, Frontend) as a Rivet actor. Orchestrator sends CONTEXT-PACKs via HTTP, actor maintains working context, brain files on disk remain the durable knowledge layer. Clean separation: Rivet = working memory, brain files = long-term memory.
- **Session routing:** Rivet natively routes follow-up requests to the same actor — exactly what multi-step specialist workflows need.
- **Friction:** Adds runtime infrastructure to a deliberately zero-infrastructure system. Risk of state divergence between actor memory and brain files. Over-engineering at current scale (1 user, 49 files, sub-agent MVP).
- **Verdict:** Phase 2+ infrastructure layer. Doesn't change brain architecture — changes the execution layer wrapping it.

## Action Taken

Research completed and deposited. No implementation yet — evaluation deferred until Prover Phase 1 MVP validates the sub-agent approach. If sub-agents prove limiting (statelessness, lack of per-session tools), Sandbox Agent is the next candidate.
