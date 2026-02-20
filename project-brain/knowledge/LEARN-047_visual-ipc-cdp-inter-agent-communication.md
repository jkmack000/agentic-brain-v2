# LEARN-047: Visual IPC via CDP for Inter-Agent Communication
<!-- type: LEARN -->
<!-- created: 2026-02-19 -->
<!-- tags: multi-agent, IPC, communication, CDP, Puppeteer, screenshots, sweetlink, visual, screen-scraping, collaboration -->
<!-- links: S001, LEARN-026, LEARN-027, LEARN-037 -->

## Context
Discovered via sweetlink project — a CLI tool with a `screenshot` command that auto-detects Chrome DevTools Protocol (CDP) endpoints and captures browser tabs. This enables a novel inter-agent communication pattern: one Claude instance can visually read what another Claude instance is displaying.

## The Pattern
Two or more Claude Code instances collaborate by using CDP screen capture as a communication channel:

1. **Agent A** works in a browser-visible environment (terminal, web UI, IDE)
2. **Agent B** runs `sweetlink screenshot` which connects to Chrome DevTools (default `http://127.0.0.1:9222`)
3. If CDP endpoint is available, Puppeteer grabs the tab directly; otherwise falls back to daemon/html2canvas renderer
4. Agent B reads the screenshot using multimodal vision — natively understands text, code, diagrams, errors
5. Agent B acts on what it sees, producing its own visible output for Agent A to capture in return

## Implementation Details (sweetlink)
- **Auto-detection**: `sweetlink screenshot` probes `http://127.0.0.1:9222` for running Chrome DevTools
- **Custom endpoint**: `--devtools-url` flag for non-default CDP endpoints
- **Manual capture**: `tools/sweetlink-snap.js` provides standalone CDP capture (same logic as CLI)
- **Documentation**: `docs/cli/sweetlink-screenshots.md`

## Comparison with Other IPC Approaches

| Approach | Structured? | Cross-machine? | Setup cost | Bandwidth | Latency |
|----------|------------|----------------|------------|-----------|---------|
| File-based (L026 stigmergy) | Yes | No (shared FS) | Low | High | Low |
| CONTEXT-PACK (S001) | Yes | Yes (git) | Medium | Medium | Medium |
| Sub-agents (L009) | Yes | No (same process) | Low | High | Low |
| Teams (L015) | Yes | No (same machine) | Medium | Medium | Medium |
| Sandbox Agent (L037) | Yes | Yes (HTTP) | High | Medium | Medium |
| **Visual/CDP (this)** | **No (visual)** | **Yes (network)** | **Medium** | **Low** | **High** |

## Advantages
- **No shared filesystem needed** — works across machines, containers, VMs
- **Language/tool agnostic** — anything visible on screen is capturable
- **Leverages multimodal vision** — Claude reads screenshots natively, including code, errors, diagrams, terminal output
- **Asynchronous** — snapshot on demand, no handshake protocol required
- **Non-invasive** — doesn't require the observed agent to expose an API or write to shared state
- **Debugging-friendly** — humans can see exactly what agents see

## Limitations
- **Lossy** — visual parsing less reliable than structured data (OCR errors, truncated text, ambiguous formatting)
- **Slower** — screenshot capture + vision processing vs direct file read
- **Bandwidth-limited** — one screenful at a time vs arbitrary data sizes
- **Requires browser/CDP** — not all agent environments expose a CDP endpoint
- **One-directional per capture** — need explicit turn-taking or polling for bidirectional communication

## Prover Relevance
Could serve as **Option E** for S001 multi-brain coordination, especially for:
- Cross-machine agent collaboration (orchestrator on one machine, specialists on others)
- Monitoring/observing agent progress without interrupting their work
- Debugging multi-agent pipelines by capturing what each agent sees
- Hybrid approach: structured IPC (CONTEXT-PACK) for data, visual IPC for status/monitoring

## Key Insight
This inverts the typical agent communication model. Instead of agents writing structured messages for each other, agents simply work normally and observers capture their visible state. This is closer to how human teams collaborate — looking at each other's screens — than traditional IPC protocols.

## Puppeteer Reference
- **Docs**: https://pptr.dev
- **Quick use**: `npx puppeteer screenshot <url> --output <path>`
- **Install**: `npm install puppeteer` (bundles Chromium) or `puppeteer-core` (bring your own browser)
- **CDP connection**: `puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' })` to attach to existing Chrome
- **When needed**: web UI verification, visual regression testing, scraping GUI-only data, cross-machine agent monitoring

## Known Issues
- OCR accuracy on code/terminal output not measured — may degrade with dense text or non-standard fonts
- CDP auto-detection assumes localhost — remote agents need explicit `--devtools-url`
- No built-in turn-taking or synchronization — agents must coordinate capture timing externally
