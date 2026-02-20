# LEARN-029: Git Worktree Workflows for Parallel Agents
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: git, worktrees, parallel-agents, isolation, multi-brain, concurrent, prover -->
<!-- links: SPEC-001, LEARN-024, LEARN-018 -->

## 1. Git Worktree Mechanics

### What Worktrees Are
A git worktree is a linked working directory that shares the same `.git` data (object store, refs, config) as the main checkout. Each worktree gets its own independent HEAD, index (staging area), and working files. The underlying Git objects (commits, blobs, trees) are shared — adding a worktree costs only the disk space of the checked-out files, not a full clone.

### Shared vs. Per-Worktree State

| Shared Across All Worktrees | Per-Worktree (Isolated) |
|------------------------------|-------------------------|
| Object store (commits, blobs, trees) | Working directory files |
| Branch refs (`refs/heads/*`) | HEAD (current branch pointer) |
| Tag refs (`refs/tags/*`) | Index / staging area |
| Remote refs (`refs/remotes/*`) | `refs/bisect/*`, `refs/worktree/*`, `refs/rewritten/*` |
| Git config (`.git/config`) | Worktree-specific config |

### Branch Exclusivity Constraint
**A branch can only be checked out in one worktree at a time.** This is a hard safety constraint. If two worktrees had the same branch checked out and one committed, the other would silently become dirty. Git refuses `git worktree add` for an already-checked-out branch unless `--force` is used (which is almost never appropriate).

**Implication for Prover:** Each agent brain MUST work on its own branch. This is not optional — it is enforced by Git itself.

### File Structure Internals
Within a linked worktree, `$GIT_DIR` points to a private directory (e.g., `/path/main/.git/worktrees/feature-x`) and `$GIT_COMMON_DIR` points back to the main repo's `.git/`. A `.git` **file** (not directory) at the worktree root contains this path reference.

### Lifecycle Commands

```bash
# Create a new worktree with a new branch
git worktree add ../prover-donchian-wt -b agent/donchian-task-042

# Create from existing branch
git worktree add ../prover-coder-wt agent/coder-task-043

# List all worktrees
git worktree list

# Lock a worktree (prevents pruning — useful for network/portable drives)
git worktree lock ../prover-donchian-wt --reason "agent session in progress"

# Unlock
git worktree unlock ../prover-donchian-wt

# Remove cleanly (fails if dirty unless --force)
git worktree remove ../prover-donchian-wt

# Prune stale administrative files (worktree dir already deleted manually)
git worktree prune

# Dry-run prune to check for stale entries
git worktree prune --dry-run
```

---

## 2. Worktrees for Parallel AI Agents

### The Core Pattern
Each AI agent session gets its own worktree on its own branch. Agents work in complete file-system isolation — reads and writes never interfere. When done, their branches merge back to a shared integration branch.

```
project-repo/                     # Main checkout (orchestrator lives here)
  .git/                           # Shared object store
project-repo-agent-donchian/      # Worktree: agent/donchian branch
project-repo-agent-coder/         # Worktree: agent/coder branch
project-repo-agent-frontend/      # Worktree: agent/frontend branch
```

### How Letta Uses Worktrees
Letta's "Context Repositories" system uses git-backed, file-based memory for agents. Key patterns:
- **Concurrent subagents** each get an isolated worktree to process and write to memory
- A **"sleep-time" background process** reviews conversation history, persists important info to the memory repo in its own worktree, then merges back automatically — avoiding conflicts with the running agent
- **Defragmentation** launches a subagent in a worktree that reorganizes memory files (splitting large files, merging duplicates), then merges the result
- All memory changes are **automatically versioned with informative commit messages**
- Merge conflicts between learned context are resolved through **standard git operations**

### ccswarm: Multi-Agent Orchestration
[ccswarm](https://github.com/nwiizo/ccswarm) is a Rust-based orchestration framework that coordinates specialized AI agents (Frontend, Backend, DevOps, QA pools) in worktree-isolated environments using Claude Code. Key design:
- Each agent gets an independent worktree copy of the code
- Multiple agents write code simultaneously
- Each agent runs tests upon completion
- **Code merges only if tests pass** — main branch stays stable
- Session persistence and real-time monitoring via Terminal UI

### Crystal: Parallel Session Manager
[Crystal](https://github.com/stravu/crystal) lets you run one or more sessions with Claude Code or Codex on isolated copies of your code, so you can work on multiple tasks instead of waiting for agents to finish.

### incident.io's Production Pattern
incident.io routinely runs 4-5 parallel Claude Code agents, each on different features:
- Built a bash function that creates worktrees and launches Claude with one command
- Auto-completion of existing worktrees and repositories
- Isolated worktrees with **username prefixes** for identification
- Each conversation stays completely isolated
- Build times faster, feature development accelerated

---

## 3. Concurrent File Access and Safety

### Why Worktrees Solve Concurrent Access
Without worktrees, multiple agents on the same checkout cause:
- **File system corruption** — one agent writes while another reads
- **Git lock errors** — `index.lock` contention when multiple processes stage/commit
- **Branch confusion** — one agent switches branches while another is mid-operation

### Lock File Mechanism
Git creates an `index.lock` file during operations that modify the index (staging area). This ensures atomic index updates. With worktrees, each worktree has its **own** index file at `.git/worktrees/<name>/index`, so lock contention between worktrees is eliminated for staging and committing.

### Object Database Safety
The shared object database uses its own locking. `git gc` and `git maintenance` take a lock on the object database. Key safety properties:
- **Commits from different worktrees are safe** — Git's object model is append-only and content-addressed; two agents creating commits on different branches write non-conflicting objects
- **Concurrent `git gc`** is prevented by its own lock file
- **Ref updates** (branch pointer moves) use atomic ref transactions — two worktrees updating different branches simultaneously is safe
- **Same-branch concurrent updates** are prevented by the branch exclusivity constraint

### What Can Go Wrong

| Scenario | Risk Level | Mitigation |
|----------|-----------|------------|
| Two agents commit to different branches simultaneously | **Safe** | Built-in: separate indexes, separate branches |
| Two agents run `git gc` simultaneously | **Safe** | Built-in: object DB lock prevents concurrent GC |
| Agent worktree deleted while another references shared objects | **Safe** | Objects persist in shared store; `git worktree prune` cleans admin files only |
| Stale `.lock` file from crashed agent | **Low risk** | Delete the lock file: `rm .git/worktrees/<name>/index.lock` |
| Both agents modify the same file on different branches | **Safe during work** | Conflict surfaces at merge time, not during parallel work |
| `git gc --aggressive` during active agent work | **Low risk** | Avoid running aggressive GC while agents are active |

---

## 4. Claude Code + Worktrees

### Running Multiple Claude Code Sessions
Each Claude Code session runs in its own terminal/process. To use worktrees:

```bash
# Terminal 1: Orchestrator on main
cd /path/to/prover
claude

# Terminal 2: Donchian agent in worktree
cd /path/to/prover-agent-donchian
claude

# Terminal 3: Coder agent in worktree
cd /path/to/prover-agent-coder
claude
```

Each Claude Code instance is fully independent — separate context window, separate file system view, separate git state. They can all run simultaneously without interference.

### The `--add-dir` Flag
`--add-dir` extends a Claude Code session's workspace to include additional directories. This is useful for:
- Monorepos where an agent needs to see multiple packages
- Cross-referencing between a worktree and the main checkout
- Giving an orchestrator agent visibility into specialist worktrees

```bash
# Orchestrator can see all agent worktrees
claude --add-dir ../prover-agent-donchian --add-dir ../prover-agent-coder
```

**Caution:** `--add-dir` gives read/write access. If the orchestrator modifies files in an agent's worktree while the agent is active, conflicts are possible. Use `--add-dir` for read-only coordination (reviewing results) rather than concurrent writes.

### Claude Code Branch Awareness
Claude Code detects the current branch via `git status`. In a worktree, it correctly identifies the worktree's branch (not the main checkout's branch). CLAUDE.md files in the worktree root are loaded normally.

### Programmatic Session Launch
For automated orchestration:

```bash
# Launch Claude Code non-interactively with a prompt
cd /path/to/prover-agent-donchian
claude --print "Implement the Donchian channel indicator per SPEC-003" \
       --output-format json

# Or with a prompt file
claude --print --input-file task-prompt.md
```

### Feature Request: Native Worktree Support
There is an open feature request (anthropics/claude-code#24850) for Claude Code to natively offer implementing approved plans in a new git worktree, rather than requiring manual worktree setup.

---

## 5. Practical Patterns for Prover

### Branch Naming Convention

```
agent/<brain-name>/<task-id>
```

Examples:
- `agent/donchian/task-042-implement-atr`
- `agent/coder/task-043-refactor-signals`
- `agent/frontend/task-044-dashboard-layout`
- `agent/orchestrator/session-2026-02-17`

This convention:
- Groups all agent branches under `agent/` prefix (easy to list, filter, clean up)
- Identifies which brain owns the branch
- Includes task ID for traceability

### Recommended Directory Layout

```
prover/                                # Main repo — orchestrator brain
  .git/                                # Shared object store
  project-brain/                       # Orchestrator's brain files
  src/                                 # Source code

prover-wt-donchian/                    # Worktree for Donchian brain
  project-brain/                       # Donchian sees same brain (but on its branch)
  src/

prover-wt-coder/                       # Worktree for Coder brain
prover-wt-frontend/                    # Worktree for Frontend brain
```

**Alternative — bare repo layout** (cleaner for many worktrees):
```
prover.git/                            # Bare repo (no working files, just .git data)
prover-main/                           # Worktree for main branch (orchestrator)
prover-donchian/                       # Worktree for Donchian agent
prover-coder/                          # Worktree for Coder agent
prover-frontend/                       # Worktree for Frontend agent
```

The bare repo layout avoids the asymmetry of one "special" main checkout. All worktrees are peers. Create with:
```bash
git clone --bare <repo-url> prover.git
cd prover.git
git worktree add ../prover-main main
git worktree add ../prover-donchian -b agent/donchian/init
```

### Orchestrator Workflow

```bash
#!/bin/bash
# orchestrate-session.sh — Create worktrees, launch agents, merge results

REPO_DIR="/path/to/prover"
TASK_ID="session-$(date +%Y%m%d-%H%M)"

# 1. Create worktrees for each agent
cd "$REPO_DIR"
git worktree add "../prover-wt-donchian" -b "agent/donchian/$TASK_ID"
git worktree add "../prover-wt-coder" -b "agent/coder/$TASK_ID"

# 2. Launch Claude Code sessions (in background or separate terminals)
cd "../prover-wt-donchian"
claude --print --input-file /path/to/donchian-task.md &

cd "../prover-wt-coder"
claude --print --input-file /path/to/coder-task.md &

# 3. Wait for agents to finish
wait

# 4. Merge results back
cd "$REPO_DIR"
git merge --no-ff "agent/donchian/$TASK_ID" -m "Merge Donchian agent results"
git merge --no-ff "agent/coder/$TASK_ID" -m "Merge Coder agent results"

# 5. Cleanup
git worktree remove "../prover-wt-donchian"
git worktree remove "../prover-wt-coder"
git branch -d "agent/donchian/$TASK_ID"
git branch -d "agent/coder/$TASK_ID"
```

### Merge Strategy
1. **Agents work on different files** (ideal) — merge is trivially clean
2. **Agents touch overlapping files** — git's 3-way merge resolves most cases
3. **True conflicts** — require human (or orchestrator LLM) resolution
4. **Recommended:** Use `--no-ff` merges to preserve agent branch history for audit trail
5. **Test before merge:** Each agent should run tests in its worktree before signaling completion. Only merge branches where tests pass.

### Cleanup and GC

```bash
# After session: remove worktrees and prune
git worktree remove ../prover-wt-donchian
git worktree remove ../prover-wt-coder
git worktree prune

# Periodic: clean up merged agent branches
git branch --merged main | grep "agent/" | xargs git branch -d

# git gc automatically prunes worktree admin files older than 3 months
git gc
```

**Automation rule:** After every orchestration session, remove worktrees and delete merged agent branches. Never leave stale worktrees — their locked branches cannot be checked out elsewhere.

### Brain File Coordination in Prover
When multiple agents share the same brain directory (e.g., `project-brain/`):
- Each agent sees brain files from its branch's perspective
- If agents create new LEARN/LOG files, they will conflict at merge time (same filenames)
- **Solution A:** Pre-allocate file number ranges per agent (e.g., Donchian gets LEARN-100-199, Coder gets LEARN-200-299)
- **Solution B:** Agents write to agent-specific directories (e.g., `project-brain/learnings/donchian/`)
- **Solution C:** Orchestrator is the only writer to the brain; agents return results in a structured format (RESULT template from SPEC-001) and the orchestrator deposits into the brain
- **Recommended for Prover:** Option C — aligns with SPEC-001's CONTEXT-PACK/RESULT communication pattern and avoids merge conflicts in brain files entirely

---

## 6. Limitations and Gotchas

### Submodule Support Is Incomplete
- Git's documentation explicitly warns: "Multiple checkout in general is still experimental, and the support for submodules is incomplete."
- Each worktree gets its own copy of submodule working directories (not hardlinks) — more disk usage
- Must run `git submodule update --init` in each new worktree
- Worktrees containing submodules cannot be moved with `git worktree move`
- **Prover impact:** If the repo uses submodules, expect friction. Prefer subtrees or monorepo structure.

### Windows-Specific Issues
- **Long paths:** Windows has a 260-character path limit by default. Worktree paths add nesting depth. Enable long paths: `git config --system core.longpaths true` and enable the Windows registry key `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`
- **Symlinks:** Git symlinks on Windows require either Administrator privileges or Developer Mode. Worktree `.git` files (not symlinks) work fine, but symlinks *within* repos may break across worktrees
- **Path separators:** Git on Windows handles forward slashes, but external tools may not. Be consistent
- **File locking:** Windows locks open files more aggressively than Unix. If an agent has a file open and the worktree is being removed, `--force` may be needed
- **Antivirus:** Real-time scanning can slow worktree creation and cause spurious lock files. Exclude development directories

### Performance Considerations
- **Disk space:** Each worktree duplicates the working tree files (but NOT the .git objects). For a repo with 500MB of working files, 4 worktrees = ~2GB of working files + 1 shared .git
- **Build caches:** Build artifacts (node_modules, __pycache__, .venv, target/) are per-worktree and NOT shared. Agents installing dependencies in each worktree multiplies disk and time cost
- **IDE/tooling conflicts:** Language servers, file watchers, and dev servers in multiple worktrees can conflict on ports and resources
- **cmake/ccache:** Build caching systems that use absolute paths won't share cache across worktrees (different absolute paths)

### Stale Worktree Detection
- If a worktree directory is deleted manually (rm -rf) instead of `git worktree remove`, Git retains stale administrative entries
- Stale worktrees lock their branches — the branch cannot be checked out elsewhere
- Fix: `git worktree prune` clears stale entries
- Prevention: Always use `git worktree remove` for cleanup, never manual deletion
- `git gc` auto-prunes worktree admin files older than 3 months

### Runtime Environment Is NOT Isolated
Worktrees isolate the **file system** but NOT:
- Network ports (two agents running servers will collide)
- Databases (shared local DB state)
- Environment variables (unless explicitly set per-process)
- System resources (CPU, memory shared across all agents)

**For Prover:** This is fine — Prover agents work on code/brain files, not running servers. But if agents need to run backtests that use shared resources (databases, APIs), coordinate access through the orchestrator.

---

## 7. Decision Matrix for Prover

| Approach | Isolation | Complexity | Merge Cost | Best For |
|----------|-----------|------------|------------|----------|
| Single repo, sequential agents | None | Low | None | Simple tasks, one brain at a time |
| Worktrees, branch-per-agent | File-level | Medium | Low-Medium | Parallel brain sessions (Prover's target) |
| Full clones per agent | Complete | High | High (no shared refs) | Untrusted agents, different remotes |
| Docker + worktrees | Full (incl. runtime) | High | Low-Medium | Agents that run servers or use shared resources |

**Recommendation for Prover Phase 1:** Worktrees with branch-per-agent, orchestrator-only brain writes (Option C from Section 5), `--no-ff` merges for audit trail, automated cleanup after each session. This gives the isolation needed for parallel Claude Code sessions while keeping the brain files conflict-free.

---

## Sources
- [Git Worktree Official Documentation](https://git-scm.com/docs/git-worktree)
- [Git Worktrees for Parallel AI Coding Agents — Upsun](https://devcenter.upsun.com/posts/git-worktrees-for-parallel-ai-coding-agents/)
- [Letta: Context Repositories — Git-based Memory for Coding Agents](https://www.letta.com/blog/context-repositories)
- [ccswarm: Multi-Agent Orchestration with Claude Code](https://github.com/nwiizo/ccswarm)
- [Crystal: Parallel AI Sessions in Git Worktrees](https://github.com/stravu/crystal)
- [incident.io: Shipping Faster with Claude Code and Git Worktrees](https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees)
- [Claude Code Common Workflows Documentation](https://code.claude.com/docs/en/common-workflows)
- [Nx Blog: How Git Worktrees Changed My AI Agent Workflow](https://nx.dev/blog/git-worktrees-ai-agents)
- [Git Worktrees: The Complete Guide for 2026 — DevToolbox](https://devtoolbox.dedyn.io/blog/git-worktrees-complete-guide)
- [Git Worktree Best Practices and Tools — GitHub Gist](https://gist.github.com/ChristopherA/4643b2f5e024578606b9cd5d2e6815cc)
- [Nick Mitchinson: Using Git Worktrees for Multi-Feature Development with AI Agents](https://www.nrmitchi.com/2025/10/using-git-worktrees-for-multi-feature-development-with-ai-agents/)
- [Claude Code Native Worktree Support Feature Request (Issue #24850)](https://github.com/anthropics/claude-code/issues/24850)
- [Git Worktree: Pros, Cons, and the Gotchas — Josh Tune](https://joshtune.com/posts/git-worktree-pros-cons/)
