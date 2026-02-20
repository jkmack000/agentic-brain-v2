# LEARN-016 — Claude Code Plugin System: Packaging Brain as a Distributable Extension
<!-- type: LEARN -->
<!-- tags: claude-code, plugins, packaging, distribution, plugin-json, namespacing, marketplace -->
<!-- created: 2026-02-14 -->
<!-- source: code.claude.com/docs/en/plugins.md, code.claude.com/docs/en/plugins-reference.md -->
<!-- links: SPEC-000, LEARN-005, LEARN-007, LEARN-008, LEARN-009, LEARN-013 -->

## Discovery
Claude Code has a complete plugin system for packaging skills, agents, hooks, MCP servers, and LSP servers into distributable, namespaced, version-managed units. This is the official mechanism for turning a brain system into a shareable, installable, updatable package. A `project-brain` plugin could bundle all brain operations as a single installable extension.

## Context
Existing LEARNs mention plugins in passing (LEARN-005 as environment extension, LEARN-007/008/009 as bundling mechanism). The plugin docs reveal a full packaging architecture with manifest schema, namespacing, caching, multi-scope installation, and five distribution channels.

## Key Details

### Plugin Directory Structure
```
project-brain-plugin/
  .claude-plugin/
    plugin.json           # ONLY the manifest goes here
  skills/                 # SKILL.md directories (brain operations)
  agents/                 # Custom subagent .md files
  hooks/
    hooks.json            # Hook configuration
  .mcp.json               # MCP server definitions
  scripts/                # Supporting scripts
```
**Critical gotcha:** Putting skills/agents/hooks INSIDE `.claude-plugin/` causes silent failures. Components go at plugin root.

### plugin.json Manifest (Key Fields)
```json
{
  "name": "project-brain",         // REQUIRED. kebab-case. Becomes namespace.
  "version": "1.0.0",              // semver
  "description": "...",
  "keywords": ["memory", "ltm"],   // Discovery tags
  "skills": "./skills/",           // Custom paths SUPPLEMENT defaults
  "agents": "./agents/",
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json"
}
```
Custom paths supplement default directories — they do NOT replace them. All paths must be relative (`./`).

### Namespacing
All skills auto-namespaced: `/<plugin-name>:<skill-name>`. Brain plugin skills become `/project-brain:search`, `/project-brain:deposit`, etc. Prevents conflicts between plugins.

### Installation Scopes
| Scope | File | Use Case |
|-------|------|----------|
| user | `~/.claude/settings.json` | Personal, all projects (default) |
| project | `.claude/settings.json` | Team-shared via version control |
| local | `.claude/settings.local.json` | Personal, project-specific |
| managed | `managed-settings.json` | Enterprise-managed |

### Five Distribution Sources
| Source | Description |
|--------|-------------|
| Relative path | Copied recursively to plugin cache |
| npm | `npm install` from registry |
| pip | `pip install` from PyPI |
| github | `owner/repo` shorthand |
| url | Any `.git` URL |

### Plugin Caching and Isolation
Plugins are **copied to a cache directory** — they do NOT run in-place.
- Path traversal (`../`) breaks after installation
- **`${CLAUDE_PLUGIN_ROOT}`** resolves to cached plugin directory — must be used in all hook commands, MCP configs, and script paths
- Workaround for external files: symlinks within plugin dir are followed during copy

### MCP Servers in Plugins
```json
{
  "mcpServers": {
    "brain-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/brain-mcp",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```
Auto-start when plugin enabled. Requires Claude Code restart for MCP changes.

### CLI Commands
| Command | Purpose |
|---------|---------|
| `claude plugin install <name> [--scope]` | Install from marketplace |
| `claude plugin validate` | Validate plugin.json |
| `claude --plugin-dir ./path` | Load for dev/testing (multiple allowed) |

### Migration from Standalone `.claude/`
1. Create `plugin/.claude-plugin/plugin.json`
2. Copy skills/, agents/ from `.claude/` to plugin root
3. Extract hooks from settings.json into hooks/hooks.json
4. Test with `--plugin-dir ./plugin`

Post-migration: `/hello` becomes `/plugin-name:hello`.

### Hook Events in Plugins
Plugin hooks support all 14 events documented in LEARN-008, including team-specific events (TeammateIdle, TaskCompleted). Hooks can be defined inline in plugin.json or in a separate hooks/hooks.json file.

## Impact

### Brain System AS a Plugin
The plugin system is the designed distribution mechanism for exactly what we're building:
- **Skills** → brain operations (search, deposit, recall, ingest, sync)
- **Agents** → specialized brain subagents (searcher, validator, depositor)
- **Hooks** → brain automation (SessionStart loading, PreCompact handoff, SessionEnd sync)
- **MCP Server** → structured brain queries via MCP tools + resources

### Architecture Split: Engine vs Data
Plugin caching means brain *engine* (templates, skills, hooks, agents) lives in the cached plugin. Brain *data* (learnings, specs, logs, rules) must remain project-local (e.g., `./project-brain/`). The plugin provides the system; the project provides the knowledge.

### Distribution via Brain Hub
Plugin distribution channels align with LOG-001's Brain Hub concept:
- npm/pip for the brain engine
- GitHub for brain knowledge packs
- Plugin marketplaces for curated domain brains

### Three-Scope Strategy
- user scope: personal brain engine across all projects
- project scope: team standardizes on brain system
- managed scope: enterprise enforces brain system org-wide

## Action Taken
Deposited as LEARN-016. Plugin packaging identified as the distribution path. Architecture split (engine vs data) is a key design decision. No code written yet.
