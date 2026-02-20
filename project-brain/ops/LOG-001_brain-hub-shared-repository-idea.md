# LOG-001 — Brain Hub: Shared Repository for Public Brain Files
<!-- type: LOG -->
<!-- tags: product-direction, brain-hub, repository, crowdsourced, meta-brain, monetization -->
<!-- created: 2026-02-14 -->
<!-- links: SPEC-000 -->

## Decision
Capture the concept of a shared public repository ("Brain Hub") where users can publish, browse, and pull fat-indexed knowledge files across domains. This extends the Project Brain from a local tool into a networked knowledge platform.

## Alternatives Considered
1. **Local-only brains (current)** — each user builds their own knowledge in isolation. Simple, private, but every user rediscovers the same things independently.
2. **Git-based sharing (manual)** — users push brain directories to GitHub and others clone them. Works but no discovery mechanism, no quality control, no fat-index-level browsing.
3. **Brain Hub (proposed)** — centralized or federated repository with a global fat index. Users browse summaries before pulling files. Crowdsourced knowledge with deduplication, quality scoring, and domain organization.

## Rationale
The fat index format already solves the discovery problem — you can evaluate whether a file is useful without opening it. This is the same property needed for a public repository. A global INDEX with fat entries lets users search across millions of files and pull only what's relevant into their local brain.

The value compounds with scale. One person discovers a gotcha (e.g., "crypto exchanges don't have standardized monthly closes") and deposits a LEARN file. Every other crypto project benefits without rediscovering it. Cross-domain patterns emerge: rate limiting, timezone edge cases, API reliability patterns — these transcend any single project.

This is the meta-brain concept realized at scale.

## Proposed Structure
```
brain-hub/
├── INDEX-GLOBAL.md              ← Fat index of all public entries
├── domains/
│   ├── trading/
│   │   ├── donchian-strategies/
│   │   ├── mean-reversion/
│   │   └── crypto-exchange-apis/
│   ├── web-dev/
│   │   ├── react-patterns/
│   │   └── auth-systems/
│   └── data-science/
│       ├── pandas-gotchas/
│       └── ml-pipelines/
```

## Monetization
- **Free:** Browse global index, pull public brain files, push to public
- **Paid:** Private brains on the hub, AI-powered quality scoring of entries, auto-deduplication across the global index, curated domain brain packs, team/org brains

## Competitive Moat
The data itself. A million+ fat-indexed knowledge entries across every domain, each written to be LLM-readable. GitHub has code. Stack Overflow has Q&A. Brain Hub would have *extracted, typed, indexed knowledge* purpose-built for LLM consumption. No one else has this format or this data.

## Consequences
- The local brain format must remain stable — it becomes an interchange format
- Fat index quality matters even more at scale (bad summaries poison discovery)
- Need trust/reputation system for public entries
- Need deduplication at global scale (the same LEARN deposited by 100 users)
- Privacy: users must be able to keep brains private and selectively publish

## Revisit Conditions
- After the local brain system is proven on 2-3 real projects
- When considering turning Project Brain into a product beyond personal use
- If a competitor launches something similar first
