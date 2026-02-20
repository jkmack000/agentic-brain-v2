# LEARN-014 — Claude Code Agent SDK: Programmatic API for Brain Automation
<!-- type: LEARN -->
<!-- tags: claude-code, agent-sdk, headless, programmatic, automation, python, typescript, MCP-tools -->
<!-- created: 2026-02-14 -->
<!-- source: code.claude.com/docs/en/headless.md, platform.claude.com/docs/en/agent-sdk/* -->
<!-- links: SPEC-000, LEARN-005, LEARN-010, LEARN-013 -->

## Discovery
The "Claude Code SDK" has been renamed to the **Claude Agent SDK**. It is a full programmatic library (not just CLI flags), available as `pip install claude-agent-sdk` (Python) and `npm install @anthropic-ai/claude-agent-sdk` (TypeScript). It provides native async iterators, typed messages, callback-based permissions, programmatic hooks, in-process custom MCP tools, structured JSON output, and session management — all without spawning CLI processes manually.

## Context
Existing coverage (LEARN-005) only mentions `claude -p` CLI pattern with `--allowedTools`. The SDK is a fundamentally different interface: a library with full Python/TypeScript APIs for building agent-powered applications.

## Key Details

### Two Interfaces: `query()` vs `ClaudeSDKClient`
| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| Session | New each call | Reusable, multi-turn |
| Hooks | No | Yes |
| Custom MCP tools | No | Yes |
| Interrupts | No | Yes |
| Continue chat | No | Yes |

### Critical Configuration Options (Brain-Relevant)
| Parameter | Brain Use |
|-----------|-----------|
| `system_prompt` | Extend Claude's prompt with brain instructions via `{"type": "preset", "preset": "claude_code", "append": "..."}` |
| `setting_sources` | **Defaults to None** — SDK does NOT load CLAUDE.md unless set to `["project"]` |
| `cwd` | Point SDK at brain repo directory |
| `add_dirs` | Access brain files in separate directory |
| `max_turns` / `max_budget_usd` | Cap cost for automated brain operations |
| `output_format` | JSON schema validation on outputs — structured brain deposits |
| `agents` | Programmatic subagent definitions (no .md files needed) |
| `mcp_servers` | Programmatic MCP server config |
| `hooks` | Callback-based hooks (Python functions, not shell scripts) |
| `can_use_tool` | Custom per-tool permission callback with input modification |
| `resume` / `fork_session` | Session continuity and parallel experiments |
| `betas` | `["context-1m-2025-08-07"]` enables 1M context window |

### Custom MCP Tools (In-Process)
```python
@tool("search_brain", "Search brain index", {"query": str, "max_results": int})
async def search_brain(args):
    return {"content": [{"type": "text", "text": results}]}

brain_server = create_sdk_mcp_server(name="brain", version="1.0.0", tools=[search_brain])
options = ClaudeAgentOptions(mcp_servers={"brain": brain_server})
```
No separate process needed. Tool naming: `mcp__{server}__{tool}`.

### Programmatic Hooks (Callbacks, Not Shell Scripts)
```python
async def my_hook(input_data, tool_use_id, context) -> dict:
    return {}  # allow, or {"decision": "block"}, or {"systemMessage": "..."}
```
Python supports: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact.
TypeScript adds: SessionStart, SessionEnd, Notification, PostToolUseFailure, SubagentStart, PermissionRequest.

### Permission Callbacks with Input Modification
```python
async def handler(tool_name, input_data, context):
    if tool_name == "Write" and "/brain/" in input_data.get("file_path", ""):
        return PermissionResultAllow(updated_input={**input_data, "file_path": f"./staging/{input_data['file_path']}"})
    return PermissionResultAllow(updated_input=input_data)
```
Can redirect, modify, or deny any tool call programmatically.

### Structured Output
`output_format={"type": "json_schema", "schema": {...}}` — response validated against schema. Enables brain operations returning structured data (search results, validation reports).

### Message Types and Cost Tracking
`ResultMessage` includes: `duration_ms`, `total_cost_usd`, `num_turns`, `session_id`, `structured_output`. Enables brain operation cost tracking.

### 1M Context Beta
`betas=["context-1m-2025-08-07"]` — 5x context for large brain operations. Compatible with Opus 4.6, Sonnet 4.5, Sonnet 4.

## Impact

### Brain Automation Engine
- **One-shot operations** (`query()`): search, validate, single-file ingest
- **Multi-turn operations** (`ClaudeSDKClient`): guided ingestion interviews, iterative consolidation
- **Custom MCP tools**: in-process `search_brain`, `deposit_brain`, `get_brain_context`
- **Budget controls**: `max_turns` + `max_budget_usd` prevent runaway costs
- **Session resume**: capture `session_id`, resume later for long operations

### Key Constraint
`setting_sources` defaults to None — SDK is isolated. Brain-powered SDK tools must explicitly opt into CLAUDE.md or inject brain knowledge via `system_prompt`.

### Naming Change
"Headless mode" is now officially "Agent SDK." The `-p` flag still works.

## Action Taken
Deposited as LEARN-014. Agent SDK identified as the correct infrastructure for brain automation. No code written yet.
