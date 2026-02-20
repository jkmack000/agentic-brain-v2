# SPEC-000 — Project Brain: LLM Memory System Architecture
<!-- type: SPEC -->
<!-- tags: architecture, overview, memory-system, fat-index, master-spec -->
<!-- created: 2026-02-14 -->
<!-- status: FOUNDATIONAL — this is the first LTM file, load it at the start of every Claude Code session -->

## What This Is

A project memory system that gives LLMs (Large Language Models) persistent long-term memory across sessions. It solves the core limitation of LLM-assisted development: context windows are finite, append-only, and reset between sessions.

The analogy is the human memory system:
- **Long-Term Memory (LTM):** Persistent .md files on disk. Fat-indexed. Domain knowledge, rules, decisions, learnings, code interfaces. Survives across all sessions.
- **Short-Term / Working Memory (STM):** The LLM's context window. Temporary. Small, fast, task-specific. Loaded from LTM via search → reset file.
- **Recall process:** Get a task → search fat indexes → build reset file → load into fresh context → do the work.

---

## Core Problem

LLMs have a hard context window (~200K tokens). Of that:
- ~40-50K consumed by system instructions
- ~10-20K for conversation
- ~130-140K usable working space

Every token consumed is permanent within a session. There is NO way to "forget" or "compact" mid-session. Every file opened costs its full token count.

This means:
- Opening files speculatively wastes tokens
- Searching through files inside context is expensive
- Large projects cannot fit in a single session
- Knowledge from past sessions is lost unless persisted to disk

---

## The Solution: Fat Indexing

### Thin Index (bad — forces file opens)
```
| ID | File | Tags |
| CODE-001 | donchian_monthly.py | donchian, monthly |
```
Tags alone can't answer "do I need to open this file?" — forces opening it. Tokens wasted.

### Fat Index (good — answers questions without file opens)
```
## CODE-001
- **Type:** CODE
- **File:** CODE-001_donchian_monthly.py
- **Tags:** donchian, monthly, indicator, breakout
- **Links:** SPEC-001, LEARN-001
- **Summary:** Calculates 20-period Donchian channel on monthly
  OHLCV data. Uses UTC midnight for month boundary. Returns
  upper_band, lower_band, midline as pandas Series. Handles
  partial months by excluding current incomplete month.
- **Interface:** `calc_donchian_monthly(df, period=20) → dict`
- **Known issues:** None open
```
~75-100 tokens per entry. 1,300 entries fit in usable context. Summary often answers the question without opening the file.

### Fat Index Entry Rules
Every entry MUST answer: "Do I need to open this file?"
1. **What** the file does/contains (one sentence)
2. **Key decisions** made inside it
3. **Interface/contract** — inputs and outputs
4. **Open issues** — so the LLM doesn't chase a file expecting answers it doesn't have

---

## File Type System

All project files are typed. Type determines the file's role in the knowledge base.

| Type | Purpose | Examples |
|------|---------|---------|
| SPEC | Design decisions, architecture | System architecture, API interface requirements |
| CODE | Implementation | Python modules, scripts, configs |
| RULE | Business/trading rules and their evolution | Entry/exit criteria, risk management |
| LEARN | Discovered knowledge (edge cases, gotchas) | "Crypto has no standardized monthly close" |
| LOG | Decision rationale, debugging history | "Why we chose 20 vs 55 period" |
| RESET | Curated context packages for specific tasks | Pre-built bundles of file references + summaries |

LEARN and LOG types are critical — they capture knowledge that would otherwise be lost in chat history. They are what make this system a living memory rather than static documentation.

---

## Directory Structure

```
project-brain/
├── INDEX-MASTER.md              ← Always loaded first. Fat index of everything.
├── indexes/
│   ├── INDEX-indicators.md      ← Sub-index by domain
│   ├── INDEX-signals.md
│   ├── INDEX-execution.md
│   └── INDEX-learnings.md
├── brain-search.py              ← External search tool (runs OUTSIDE context)
├── reset-files/
│   ├── RESET-TEMPLATE-*.md      ← Reusable task playbooks
│   └── RESET-<task>-<date>.md   ← Generated per-task context packages
├── templates/
│   ├── TEMPLATE-SPEC.md
│   ├── TEMPLATE-CODE.md
│   ├── TEMPLATE-RULE.md
│   ├── TEMPLATE-LEARN.md
│   ├── TEMPLATE-LOG.md
│   └── TEMPLATE-RESET.md
├── specs/
├── code/
├── rules/
├── learnings/
└── logs/
```

### Hierarchical Navigation (for scale)
When project exceeds ~75 files:
- INDEX-MASTER.md (~30 lines) → points to sub-indexes
- Sub-indexes (~20-50 entries each) → point to files
- Three levels deep, minimal token waste
- Navigation cost: ~8,000-10,000 tokens (5% of usable context)

---

## Session Workflows

### Search → Reset → Work Pattern
```
Session 1 (SEARCH — disposable):
  Load INDEX-MASTER.md
  → Chase fat indexes to identify needed files
  → Output: RESET file listing exact endpoints + summaries
  Context consumed: 50-80K on navigation (thrown away)

Session 2 (WORK — efficient):
  Fresh 200K context
  Load ONLY the RESET file + listed endpoint files
  Context consumed: 15-30K on relevant material
  Remaining: 170K+ for actual work
```

The search session is disposable. The work session is maximally efficient.

### Reset File Format
```markdown
# RESET — [Task Name]
<!-- generated: YYYY-MM-DD -->
<!-- search-session: consumed ~NNK tokens across N index chains -->

## Task Objective
[What we're building]

## Required Context Files (load these)
1. FILE-ID (interface only, lines 1-25)
2. FILE-ID (full file, ~N lines)

## Key Decisions Already Made
- [Decision 1]
- [Decision 2]

## Estimated Context Load
~N tokens for listed files
~N tokens for this reset file
= ~N tokens total starting context
Remaining for work: ~NK tokens
```

### Ingestion Workflow (for books/documents/source material)
```
Session type: INGESTION

Input: Source material (book chapter, API docs, article, conversation)

Process:
  1. Read source material
  2. Extract knowledge relevant to THIS project
  3. Produce one or more typed LTM files (LEARN, RULE, SPEC, etc.)
  4. Generate fat index entries for each new file
  5. Update INDEX-MASTER.md
  6. Flag conflicts with existing LTM

Output: New LTM files + updated indexes

Key: This is EXTRACTION, not storage. A 40-page chapter becomes
5 files totaling ~300 lines. Compression ratio ~6:1.
Each piece independently searchable.
```

### Comprehension Check (before building modules)
```
You: "Based on current LTM, explain [concept]."
LLM: [answers using only LTM knowledge]
You: [evaluates] → feeds more source material if gaps found
LLM: [ingests → deposits new LTM → re-explains]
You: "Good. Now you're ready to build that module."
```

---

## brain-search.py Specification

External search tool that runs OUTSIDE the LLM context window. This is the force multiplier — it finds relevant files without consuming context tokens on the search process.

### Commands

**`brain init "<project name>"`**
Initialize a project-brain directory with all scaffolding.

**`brain deposit --type <TYPE> --tags "<comma-separated>"`**
Add a new knowledge file. Opens editor, auto-generates fat index entry, registers in INDEX-MASTER.md.

**`brain search "<query>"`**
Search fat indexes by tags and summary content. Returns ranked results with summaries. Does NOT open full files.

**`brain recall "<task description>"`**
Search → select relevant endpoints → generate a RESET file. Estimates token cost.

**`brain status`**
Project overview: file counts by type, index health, last deposit, orphan detection.

**`brain ingest "<source file>"`**
Process a source document, extract knowledge, produce typed LTM files, update indexes. (Requires LLM API call for summarization.)

---

## Product Direction

### What It Is
An LLM project memory manager. Any developer using Claude Code, Cursor, Copilot, or any LLM tool hits the same context window wall. This tool solves it.

### Form Factor
Standalone CLI tool (like git). Works with any folder of .md files. Obsidian-vault compatible by design (Obsidian vaults ARE folders of .md files). Not an Obsidian plugin — no dependency on their ecosystem, review queue, or policies.

### Why Not an Obsidian Plugin
- Obsidian has no paid plugin marketplace
- Plugin review queue is months long
- Standalone tool works with ANY LLM workflow, not just Obsidian users
- Can add Obsidian plugin later as additional distribution channel

### Monetization (future)
- Free: manual fat indexing, templates, basic search, CLI core
- Paid: AI-powered auto-summarization, smart recall, reset file generation, token budget optimization
- The intelligence layer (auto-summarization, smart search) is the paid service

### Competitive Moat
- The fat indexing methodology
- The search → reset → work session pattern
- Pre-built domain templates
- AI summarization quality for auto-generating fat index entries

---

## Phase Plan

### Phase 0: Build the Framework
- Directory structure + scaffolding
- All file templates (SPEC, CODE, RULE, LEARN, LOG, RESET)
- INDEX-MASTER.md with fat indexing rules
- brain-search.py core functionality
- This document (SPEC-000) is the first LTM file

### Phase 1: Build Long-Term Memory (for trading bot)
- Ingest source material (books, docs, conversations)
- Deposit domain knowledge as typed LTM files
- Fat index everything
- Comprehension checks before building
- NO CODE in this phase — just knowledge

### Phase 1.5: Fill Gaps
- Attempt comprehension checks
- Identify missing knowledge
- Targeted ingestion to fill gaps

### Phase 2: Execute Tasks Against LTM
- For each module: fresh session → load index → search → reset → build → test
- Deposit new LEARNs back into LTM (the system grows during build)
- Update fat indexes after every session

---

## First Application: Multi-Timeframe Donchian Trading Bot

4 timeframe Donchian Channel bot (Monthly, Daily, 15-minute, 1-minute). Entry/exit rules based on channel breakouts with timeframe alignment for confluence. Details TBD — this is the test project for the memory system itself.

Trading bot design decisions and exchange/market selection are NOT yet made. Those will be deposited as RULE and SPEC files during Phase 1.

---

## Critical Constraints to Remember

1. **Context is append-only.** Every token stays until session ends. No forgetting mid-session.
2. **Fat indexes must carry enough meaning to skip file opens.** If the summary can't answer "do I need this file?" — the index is too thin.
3. **The search process should happen OUTSIDE context when possible.** brain-search.py exists for this reason.
4. **LTM grows during Phase 2.** Every bug, edge case, and decision discovered during building gets deposited back. The system is alive, not static.
5. **Reset files are the bridge between sessions.** They carry curated context across the hard boundary of a context window reset.
6. **Ingestion is extraction, not storage.** Never dump raw source material into LTM. Compress, restructure, and type it.
