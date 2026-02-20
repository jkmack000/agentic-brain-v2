# INIT — Project Brain

You have no memory between sessions. This folder (`project-brain/`) is your persistent memory.

## Startup
1. Check `ops/SESSION-HANDOFF.md` — previous session's unfinished state
2. Search `knowledge/indexes/INDEX-MASTER.md` for what's relevant to the current task — don't load everything

## Three-Space Architecture (v2)

```
project-brain/
├── INIT.md                      ← You are here
├── brain.py                     ← CLI search tool
├── brain-mcp-server.py          ← MCP server for Claude Code
│
├── identity/                    ← WHO: SPECs + RULEs
├── knowledge/                   ← WHAT: LEARNs + CODEs
│   └── indexes/
│       ├── INDEX-MASTER.md      ← Load this first
│       └── INDEX-*.md           ← Sub-indexes by topic
├── ops/                         ← HOW: LOGs + session state
│   ├── SESSION-HANDOFF.md
│   └── sessions/
│
├── reset-files/                 ← Pre-built context packages
├── templates/                   ← File templates for each type
└── archive/                     ← Retired files
```

## File types
SPEC (architecture) + RULE (constraints) → `identity/`
LEARN (discoveries) + CODE (implementation) → `knowledge/`
LOG (timeline) → `ops/`
RESET (context packages) → `reset-files/`

## User shorthand
- **"Ingest this"** = extract knowledge → typed .md files → update INDEX-MASTER.md
- **"Deposit this as [TYPE]"** = write one file + fat index entry
- **"Handoff"** = write SESSION-HANDOFF.md now
