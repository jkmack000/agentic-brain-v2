# LEARN-004: Context Engineering for Claude Code
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: https://thomaslandgraf.substack.com/p/context-engineering-for-claude-code (Thomas Landgraf, Substack) -->
<!-- tags: context-engineering, claude-code, knowledge-files, token-management, research-workflow, CLAUDE-files -->
<!-- links: SPEC-000, LEARN-001, LEARN-002 -->

## Core Thesis

Effective AI-assisted development depends on **context engineering** — providing AI assistants with purpose-built knowledge foundations rather than relying on general training data. Developers who thrive won't be those writing optimal prompts, but those **architecting superior contexts**.

## Three Pillars of Context Engineering

1. **Project Architecture Knowledge** — Class hierarchies, libraries, frameworks, and design patterns stored in `CLAUDE` files (Claude Code's native config format).
2. **Product Requirements Documentation** — Specifications from user stories and customer interviews stored as `*.prd.md` files.
3. **Deep Technical Knowledge** — Specialized understanding of core technologies, algorithms, and middleware components stored as dedicated knowledge documents.

## Research-Driven Knowledge Document Workflow

### The Problem
AI assistants hallucinate on specialized/advanced features. Example: Eclipse Ditto (digital twin platform) where AI hallucinated about complex policy management, Web of Things Thing Models integration, and Resource Query Language (RQL) syntax.

### Three-Step Solution

**Step 1: Initial Deep Research (OpenAI Deep Research)**
- Comprehensive research on advanced features, implementation details, common pitfalls
- Architecture: Sequential 6-agent pipeline
- Speed: 7-30 minutes (sometimes days)
- Output: 25-36 pages with 100+ citations
- Strength: Exhaustive, comprehensive analysis

**Step 2: Refinement (Claude Research)**
- Validate technical details, identify gaps, add production-ready implementation patterns
- Architecture: Parallel orchestrator-worker (1-20+ agents)
- Speed: 2-5 minutes consistently
- Output: 7-page overviews with 20-25 sources
- ~0% source hallucination rate (dedicated citation agents)
- 0.56-second search query latency (Brave Search integration)
- Strength: Speed + enterprise tool integration (MCP connects to Jira, Confluence, Google Workspace, 7,000+ apps via Zapier)

**Step 3: Master Context Creation**
- Combine outputs from both tools into production-ready knowledge documents
- Result: Transforms AI from "confused junior developer into knowledgeable architect"

## Critical Best Practices

### 1. Rigorous Knowledge File Review
"One incorrect API pattern means every future implementation will be wrong." Domain expert validation is mandatory. A single wrong pattern propagates through every session that loads the file.

**Relevance to Brain System:** Validates our need for confidence indicators (LEARN-003 recommendation). Every LEARN/SPEC deposited should be expert-reviewed, especially API patterns and implementation details.

### 2. Strategic Context Splitting
Break large knowledge files (50KB+) into modular components. Example:
- `ditto-advanced-knowledge-policies.md` (access control)
- `ditto-advanced-knowledge-wot.md` (Thing Models)
- `ditto-advanced-knowledge-rql.md` (query language)

**Relevance to Brain System:** Directly validates our fat-index approach. Our system already does this — each LEARN/SPEC is a focused file. The 50KB threshold is a useful benchmark for when to split.

### 3. Token Management
- Monitor context usage with `/compact` and `/clear` commands in Claude Code
- Watch for "Compacting context" messages — these indicate knowledge files are being discarded
- Pre-computed knowledge documents provide instant access vs. real-time research

**Token Economics:**
- Single research session: 100,000+ tokens at $40-70 cost
- Processing time: 5-30 minutes per session
- Real-time research during development is economically unfeasible
- Front-loading research into documents is dramatically cheaper at scale

**Relevance to Brain System:** Validates our SESSION-HANDOFF at 80% context rule. Also validates the entire brain architecture — pre-computed knowledge files are the economically rational approach.

### 4. Living Documentation Pattern
Enrich knowledge files with code references:
```
For production-ready policy implementation, see @src/policies/DeviceAccessPolicy.cpp
```

Creates feedback loops where "knowledge files become living documents that grow smarter with every successful implementation."

**Relevance to Brain System:** Actionable improvement. Our LEARN/SPEC files could reference actual code paths using `@path` notation. This would make knowledge files bidirectionally linked to implementation — not just abstract knowledge but pointers to working code.

## Key Takeaways for Brain System

1. **Validated:** Our architecture is aligned with emerging best practices — fat indexing, modular knowledge files, token-conscious loading, and session management all map directly to Landgraf's recommendations.
2. **New technique:** Two-phase research workflow (OpenAI breadth → Claude refinement) is a concrete methodology for the `brain ingest` pipeline when ingesting from external domains.
3. **Actionable:** Add `@path` code references to LEARN/SPEC files as implementations are built — creates living documentation feedback loop.
4. **Benchmark:** 50KB as the threshold for splitting knowledge files into sub-documents.
5. **Economic argument:** Front-loaded knowledge documents beat real-time research by orders of magnitude in token cost — useful for justifying brain system investment to skeptics.
