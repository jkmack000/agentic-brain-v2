# LEARN-006: Claude Code Memory System (CLAUDE.md + Auto Memory + Rules)
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://code.claude.com/docs/en/memory -->
<!-- tags: claude-code, CLAUDE-md, auto-memory, memory-hierarchy, rules, imports, configuration -->
<!-- links: SPEC-000, LEARN-004, LEARN-005 -->

## Two Memory Types

1. **Auto Memory** — Claude automatically saves project patterns, key commands, preferences. Persists across sessions.
2. **CLAUDE.md files** — Markdown files you write and maintain with instructions/rules for Claude.

Both loaded into context at session start. Auto memory loads only first 200 lines of MEMORY.md.

---

## Memory Hierarchy (Priority Order)

| Type | Location | Scope | Shared With |
|------|----------|-------|-------------|
| Managed policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) / `/etc/claude-code/CLAUDE.md` (Linux) / `C:\Program Files\ClaudeCode\CLAUDE.md` (Win) | Org-wide | All users |
| Project memory | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared | Via source control |
| Project rules | `./.claude/rules/*.md` | Modular per-topic | Via source control |
| User memory | `~/.claude/CLAUDE.md` | Personal, all projects | Just you |
| Project local | `./CLAUDE.local.md` | Personal, this project | Just you (auto-gitignored) |
| Auto memory | `~/.claude/projects/<project>/memory/` | Claude's auto notes | Just you (per project) |

More specific instructions take precedence over broader ones. Parent dir CLAUDE.md files load at launch; child dir files load on demand.

---

## Auto Memory Details

### What Claude Remembers Automatically
- Project patterns: build commands, test conventions, code style
- Debugging insights: solutions, common error causes
- Architecture notes: key files, module relationships
- Your preferences: communication style, workflow habits

### Storage Structure
```
~/.claude/projects/<project>/memory/
├── MEMORY.md          # Index, first 200 lines loaded every session
├── debugging.md       # Topic files loaded on demand
├── api-conventions.md
└── ...
```

Project path derived from git repo root — all subdirs share one memory dir. Git worktrees get separate dirs.

### Control
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` to force off
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=0` to force on
- Tell Claude directly: "remember that we use pnpm, not npm"
- `/memory` to open file selector

---

## CLAUDE.md Imports (@path Syntax)

```markdown
See @README.md for project overview and @package.json for npm commands.
# Additional Instructions
- Git workflow: @docs/git-instructions.md
- Personal: @~/.claude/my-project-instructions.md
```

- Relative paths resolve relative to the containing file, not cwd
- First-time imports show approval dialog (one-time per project)
- Not evaluated inside code spans/blocks
- Recursive imports supported, max depth 5
- `/memory` shows what's loaded

### Multi-Worktree Trick
Use home-directory import so all worktrees share personal instructions:
```markdown
- @~/.claude/my-project-instructions.md
```

---

## Modular Rules (.claude/rules/)

```
.claude/rules/
├── frontend/
│   ├── react.md
│   └── styles.md
├── backend/
│   ├── api.md
│   └── database.md
└── general.md
```

- All `.md` files loaded automatically as project memory
- Same priority as `.claude/CLAUDE.md`
- Recursive discovery in subdirs
- Symlinks supported (share rules across projects)

### Path-Specific Conditional Rules
```yaml
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules
- All endpoints must include input validation
```

Rules without `paths` apply to all files. Glob patterns supported: `**/*.ts`, `src/**/*`, `*.{ts,tsx}`.

### User-Level Rules
`~/.claude/rules/` — personal rules across all projects, loaded before project rules.

---

## Key Takeaways for Brain System

1. **Auto memory is a parallel to our brain system.** Claude already has a per-project persistent memory system. Brain files could integrate with or complement auto memory rather than compete with it.
2. **The hierarchy is the delivery mechanism.** Brain knowledge could be delivered via:
   - `.claude/rules/*.md` for modular, topic-specific knowledge (maps to our RULE files)
   - `@path` imports from brain files into CLAUDE.md
   - Auto memory for Claude's own discoveries during sessions
3. **Path-specific rules** could scope brain knowledge to relevant code areas — e.g., trading rules only active when editing trading code.
4. **200-line limit on auto memory** means MEMORY.md must be an index (like our INDEX-MASTER) with details in topic files — validates our fat-index approach.
5. **Symlinks for shared rules** could link brain files across multiple projects.
