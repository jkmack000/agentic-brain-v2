# Deposit Queue
<!-- type: OPS -->
<!-- updated: 2026-02-20 -->

Pending deposits that haven't been written as brain files yet. Items are added during sessions when full deposit isn't practical (e.g., mid-flow insight, context running low). Process this queue at the start of the next session or during a `/brain-checkpoint` pass.

## Format

Each entry:
```
### [TYPE] Short description
- **Context:** Why this matters
- **Links:** Likely connections (file IDs)
- **Priority:** HIGH / MEDIUM / LOW
- **Added:** YYYY-MM-DD
```

## Queue

_Empty — no pending deposits._
