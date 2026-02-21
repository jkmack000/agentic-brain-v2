# LEARN-055 — Hierarchical Swarm Topology with Queen-Worker Model
<!-- type: LEARN -->
<!-- tags: multi-agent,swarm,hierarchy,queen-worker,consensus,Byzantine,Raft,Gossip,topology,claude-flow,orchestration -->
<!-- created: 2026-02-21 -->
<!-- source: https://github.com/ruvnet/claude-flow (v3 architecture analysis) -->
<!-- links: LEARN-027, LEARN-026, LEARN-015, LEARN-038, LEARN-053 -->

## Discovery
claude-flow implements a hierarchical "queen-led" swarm topology with three specialized queen types and eight worker types, using distributed consensus (Raft, Byzantine, Gossip) for coordination. While overengineered for a dev tool, the hierarchy maps to real engineering org structures and introduces consensus voting on code changes — multiple agents review before merge.

## Context
Discovered while analyzing claude-flow beyond its memory/indexing system. Most multi-agent frameworks (L027) use flat pools or simple orchestrator-worker patterns. claude-flow's hierarchy is the most structured agent topology encountered in this research.

## Evidence
**Queen types (three specializations):**
1. **Strategic Queen** — long-term planning, goal decomposition, resource allocation across swarms
2. **Tactical Queen** — task-level decomposition, immediate work assignment, deadline management
3. **Adaptive Queen** — runtime rebalancing, detecting bottlenecks, reassigning workers dynamically

**Worker types (eight specializations):**
Coder, Tester, Reviewer, Architect, Security, Documentation, DevOps, Research — each with constrained tool access and domain-specific prompts.

**Consensus mechanisms:**
- **Raft** — leader election among queens, log replication for task state
- **Byzantine fault tolerance** — consensus voting where agents may produce conflicting results (relevant for code review where "correct" is subjective)
- **Gossip protocol** — lightweight status propagation across the swarm

**Comparison to existing patterns:**
| Pattern | Source | Topology | Coordination |
|---------|--------|----------|-------------|
| Fan-out/fan-in | L027 | Flat | Orchestrator-controlled |
| Agent teams | L015 | Mesh | Shared task list + mailbox |
| Orchestrator-worker | L038 | Star | Single orchestrator |
| Queen-worker swarm | claude-flow | Hierarchical tree | Consensus + delegation |

**Overengineering assessment:**
- Byzantine tolerance assumes agents actively produce malicious/conflicting outputs — unlikely in a single-user dev tool
- Raft consensus adds latency for leader election — unnecessary when one orchestrator suffices
- However, consensus voting on code changes (3 agents must agree before merge) is genuinely useful for quality assurance

## Impact
- **Extends L027**: New orchestration pattern — hierarchical swarm with typed queens. Not covered by existing 6-framework survey.
- **Consensus for code review**: The idea of mandatory multi-agent agreement before code changes is worth noting for any multi-agent coding system
- **Brain analogy**: Queen hierarchy parallels our three-space architecture — identity (strategic), knowledge (tactical), ops (adaptive). Different organizing principle, similar separation of concerns.
- **Caution**: Complexity cost is real. Simple orchestrator-worker (L038) covers 90% of use cases. Hierarchical swarms are justified only when agent count exceeds ~10-20 and tasks have genuine interdependencies.

## Action Taken
Deposited as research finding. No implementation planned — our brain operates single-agent. Pattern catalogued for reference if multi-agent coordination becomes relevant.
