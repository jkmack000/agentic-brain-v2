# LEARN-007: Claude Code Skills System (SKILL.md Deep Dive)
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://code.claude.com/docs/en/skills -->
<!-- tags: claude-code, skills, SKILL-md, slash-commands, workflows, configuration -->
<!-- links: SPEC-000, LEARN-005, LEARN-006 -->

## What Skills Are

Skills extend Claude's capabilities via `SKILL.md` files. Claude applies them automatically when relevant, or users invoke with `/skill-name`. Follows the [Agent Skills](https://agentskills.io) open standard.

**Two types of content:**
- **Reference content** — Knowledge Claude applies to current work (conventions, patterns, style guides). Runs inline.
- **Task content** — Step-by-step workflows for specific actions (deploy, commit, code generation). Often manual-only via `disable-model-invocation: true`.

---

## Skill Location & Priority

| Location | Path | Applies To | Priority |
|----------|------|------------|----------|
| Enterprise | Managed settings | All org users | Highest |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects | High |
| Project | `.claude/skills/<name>/SKILL.md` | This project only | Medium |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where enabled | Lowest |

Same-name skills: higher priority wins. Nested `.claude/skills/` dirs auto-discovered in monorepos.

---

## Frontmatter Reference

```yaml
---
name: my-skill              # Display name, becomes /slash-command
description: What it does    # Claude uses to decide when to apply
argument-hint: [issue-num]   # Shown during autocomplete
disable-model-invocation: true  # Manual-only (/name)
user-invocable: false        # Hidden from / menu (background knowledge)
allowed-tools: Read, Grep    # Tool restrictions when active
model: sonnet                # Model override
context: fork                # Run in isolated subagent
agent: Explore               # Which subagent type for context:fork
hooks:                       # Lifecycle hooks scoped to skill
---
```

### Invocation Control Matrix

| Setting | You Can Invoke | Claude Can Invoke | Context Loading |
|---------|---------------|-------------------|-----------------|
| Default | Yes | Yes | Description always, full on invoke |
| `disable-model-invocation: true` | Yes | No | Not in context until invoked |
| `user-invocable: false` | No | Yes | Description always, full on invoke |

---

## String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All args passed when invoking |
| `$ARGUMENTS[N]` or `$N` | Specific arg by 0-based index |
| `${CLAUDE_SESSION_ID}` | Current session ID |

If `$ARGUMENTS` not present in content, args appended as `ARGUMENTS: <value>`.

---

## Supporting Files

```
my-skill/
├── SKILL.md           # Required - overview & navigation
├── reference.md       # Detailed docs - loaded when needed
├── examples.md        # Usage examples - loaded when needed
└── scripts/
    └── helper.py      # Utility script - executed
```

Keep SKILL.md under 500 lines. Move detail to separate files. Reference them so Claude knows what they contain.

---

## Dynamic Context Injection

`!`command`` syntax runs shell commands before skill content sent to Claude:
```yaml
## PR Context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
```

Commands execute immediately as preprocessing. Claude only sees the output.

---

## Running Skills in Subagents

`context: fork` runs skill in isolated context:
```yaml
---
name: deep-research
context: fork
agent: Explore
---
Research $ARGUMENTS thoroughly...
```

Skill content becomes the subagent's task prompt. Agent field specifies execution environment (Explore, Plan, general-purpose, or custom).

---

## Context Budget

Skill descriptions loaded into context = 2% of context window (fallback: 16,000 chars). Too many skills → some excluded. Check with `/context`. Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var.

---

## Key Takeaways for Brain System

1. **Skills ARE the delivery mechanism for brain knowledge.** Each brain SPEC/RULE/LEARN could be exposed as a skill with `user-invocable: false` so Claude loads it automatically when relevant. The description = our fat index summary.
2. **`disable-model-invocation: true`** for brain workflows like `/brain-deposit`, `/brain-ingest`, `/brain-handoff` — user-triggered only.
3. **Supporting files pattern** maps perfectly to brain architecture: SKILL.md = fat index entry, supporting files = the actual brain file content.
4. **Dynamic context injection** (`!`command``) could inject brain search results into skills: `!`uv run brain.py search "$ARGUMENTS"``.
5. **Context budget constraint** (2% of window) limits how many skills can be loaded. Brain system needs to be selective about which knowledge becomes a skill.
6. **`context: fork` + agent: Explore** for brain search operations — keeps search context out of main conversation.
