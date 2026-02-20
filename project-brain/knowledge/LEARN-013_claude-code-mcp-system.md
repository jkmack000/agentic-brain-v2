# LEARN-013 — Claude Code MCP System: Configuration, Transports, and Brain Server Architecture
<!-- type: LEARN -->
<!-- tags: claude-code, MCP, model-context-protocol, transports, tools, resources, prompts, brain-server -->
<!-- created: 2026-02-14 -->
<!-- source: code.claude.com/docs/en/mcp.md -->
<!-- links: SPEC-000, LEARN-002, LEARN-005, LEARN-008, LEARN-010 -->

## Discovery
MCP (Model Context Protocol) in Claude Code is far deeper than surface mentions in existing LEARNs. It supports three transport types, three scoping levels, OAuth/header authentication, dynamic tool updates, automatic tool search for context optimization, @-mentionable resources, prompts-as-slash-commands, Claude Code as an MCP server, plugin-bundled servers, and enterprise managed deployment. A brain MCP server is a viable and well-supported path.

## Context
Fetched from official MCP docs during Tier 2 ingestion. Existing coverage was limited to: MCP as environment config option (LEARN-005), `mcp__server__tool` matcher pattern (LEARN-008), background subagents can't use MCP (LEARN-009), MCP as context cost concern (LEARN-010).

## Key Details

### Three Transport Types
| Transport | Flag | Status | Use Case |
|-----------|------|--------|----------|
| HTTP | `--transport http` | **Recommended** | Cloud-based servers |
| SSE | `--transport sse` | Deprecated | Legacy only |
| stdio | `--transport stdio` | Active | Local tools, custom scripts |

Windows-specific: stdio servers using `npx` need `cmd /c` wrapper. Python-based servers avoid this.

### Three Configuration Scopes
| Scope | Flag | Storage | Visibility |
|-------|------|---------|------------|
| local (default) | `--scope local` | `~/.claude.json` under project path | Personal, this project |
| project | `--scope project` | `.mcp.json` at project root | Team-shared, version-controlled |
| user | `--scope user` | `~/.claude.json` global section | Personal, all projects |

Precedence: local > project > user. Project-scoped servers require user approval prompt.

### `.mcp.json` Format with Environment Variable Expansion
```json
{
  "mcpServers": {
    "server-name": {
      "command": "/path/to/server",
      "args": [],
      "env": {"KEY": "${VAR:-default}"}
    }
  }
}
```
`${VAR}` and `${VAR:-default}` syntax in command, args, env, url, headers. Missing required var with no default = parse failure.

### Authentication
- **OAuth 2.0:** Add server → run `/mcp` → browser login → tokens stored and auto-refreshed
- **Pre-configured OAuth:** `--client-id`, `--client-secret` (masked input or `MCP_CLIENT_SECRET` env var), `--callback-port`. Secret stored in system keychain.
- **Headers:** `--header "Authorization: Bearer token"` or `--header "X-API-Key: key"`

### Output Limits
- Warning threshold: 10,000 tokens
- Hard max: 25,000 tokens (override via `MAX_MCP_OUTPUT_TOKENS` env var)
- Startup timeout: `MCP_TIMEOUT` env var (milliseconds)

### Tool Search (Context Optimization)
Auto-activates when MCP tool descriptions exceed 10% of context. Tools are deferred and discovered on-demand via search. Config: `ENABLE_TOOL_SEARCH` = `auto` (default), `auto:N` (custom %), `true`, `false`. Requires Sonnet 4+ / Opus 4+ (Haiku does not support). Server `instructions` field is critical for discoverability.

### MCP Resources (@-mentions)
Servers expose resources referenceable with `@server:protocol://path`:
- `@brain:learn://LEARN-005` — specific brain file
- `@brain:index://MASTER` — master index
- Appear in autocomplete, fuzzy-searchable, auto-fetched as attachments

### MCP Prompts as Slash Commands
Format: `/mcp__servername__promptname`. Arguments space-separated. Results injected into conversation.

### Claude Code AS an MCP Server
`claude mcp serve` exposes Claude's tools (View, Edit, LS, etc.) to external MCP clients.

### Dynamic Tool Updates
Servers can send `list_changed` notifications; Claude Code auto-refreshes available tools without reconnection.

### Enterprise Managed MCP
`managed-mcp.json` at system paths (macOS: `/Library/Application Support/ClaudeCode/`, Linux: `/etc/claude-code/`, Windows: `C:\Program Files\ClaudeCode\`). Supports allowlist/denylist policies via `allowedMcpServers`/`deniedMcpServers` with serverName, serverCommand, or serverUrl matching.

### Anthropic MCP Registry
API at `api.anthropic.com/mcp-registry/v0/servers` — discovery endpoint for commercial MCP servers.

## Impact

### Brain MCP Server Architecture (Viable Path)
1. Build Python MCP server using MCP SDK
2. Register via stdio: `claude mcp add --transport stdio brain -- python brain-server.py`
3. Scope as `--scope user` for cross-project availability
4. Expose **tools**: `search_brain`, `read_learning`, `get_index`
5. Expose **resources**: `@brain:learn://LEARN-005`, `@brain:spec://SPEC-000`, `@brain:handoff://latest`
6. Expose **prompts**: `/mcp__brain__search`, `/mcp__brain__handoff`, `/mcp__brain__status`
7. Use `list_changed` notifications when brain content updates

### Token Budget Design
Brain MCP responses should stay under 10K tokens (warning threshold). Validates fat-index architecture: return index summaries, not full files. Tool Search at 10% context means brain server should keep tool definitions lean.

### Team Sharing via `.mcp.json`
Commit `.mcp.json` with brain server config using `${VAR:-default}` for portable paths. Team gets brain access automatically.

## Action Taken
Deposited as LEARN-013. Brain MCP server identified as high-priority implementation target (validates LEARN-002's #1 ranking of MCP wrapper). No code written yet.
