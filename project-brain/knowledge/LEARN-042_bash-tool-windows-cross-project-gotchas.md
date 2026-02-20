# LEARN-042 — Bash Tool Windows & Cross-Project Gotchas
<!-- type: LEARN -->
<!-- updated: 2026-02-18 -->
<!-- tags: claude-code, bash, windows, powershell, cross-project, file-operations, gotchas -->
<!-- links: LEARN-019, RULE-001, LEARN-010 -->

## Discovery
When running Bash tool commands on Windows to operate on a different project (C:\coder-brain from C:\agentic-brain), two major gotchas emerged:

1. **PowerShell variable expansion fails inside Bash tool.** The Bash tool uses a bash shell, so PowerShell's `$_.Name` and `$_.FullName` are interpreted as bash variable expansions (`$_` = last argument in bash). This silently produces garbage — every file shows the same empty/wrong name.
2. **Cross-project file operations don't need cloning.** Read, Write, Edit, and Glob tools accept absolute paths to ANY directory on disk. You can directly create/modify files in `C:\coder-brain` while Claude Code's working directory is `C:\agentic-brain`. No need to clone, checkout, or change directory.

## Patterns

### PowerShell-in-Bash: Don't use variable expansion
```bash
# BROKEN — $_.Name is bash-expanded to empty string
powershell -Command "Get-ChildItem -Path 'C:\foo' -Recurse | ForEach-Object { Write-Host $_.Name }"

# WORKS — use -Name flag instead of ForEach-Object
powershell -Command "Get-ChildItem -Path 'C:\foo' -Recurse -Name"

# WORKS — use Python for anything with iteration/variables
python -c "
import os
for f in os.listdir(r'C:\foo'):
    print(f)
"
```

### Cross-project operations: Use absolute paths, not git clone
```
# DON'T do this:
git clone https://github.com/user/other-repo /tmp/other-repo
# Then operate on /tmp/other-repo

# DO this — tools accept absolute paths:
Read tool:  file_path = "C:\other-project\file.md"
Write tool: file_path = "C:\other-project\new-file.md"
Edit tool:  file_path = "C:\other-project\existing-file.md"
Glob tool:  path = "C:\other-project", pattern = "**/*.md"

# For git operations in other repos, use full paths:
cd "C:/other-project" && git add ... && git commit ... && git push
```

### When Python beats PowerShell (on Windows Bash tool)
- **File scanning with metadata extraction** — Python's `os.walk()` + `re` for parsing frontmatter
- **Any loop with variable references** — PowerShell `$_` collides with bash
- **JSON/YAML parsing** — `json.load()` / `re.findall()` more reliable than PowerShell piping
- **Path handling** — `os.path.join()` handles both separators consistently

## Key Insight
The Bash tool's shell is bash on Windows, not PowerShell. PowerShell is available as a *command* (`powershell -Command "..."`) but variable expansion within the quoted string is processed by bash first. This double-interpretation is the root cause. Use PowerShell only for simple flag-based commands (like `-Name`, `-Filter`) that don't need `$_` or `$variable` references.

## Impact
- **Wasted 5+ tool calls** debugging PowerShell variable expansion before switching to Python
- **Nearly cloned coder-brain unnecessarily** before realizing absolute paths work for all file tools
- **Pattern for future cross-project operations:** Use file tools with absolute paths for reads/writes, bash with `cd` only for git operations

## Action Taken
Deposited as LEARN-042. Enriches LEARN-019 (Windows path handling) with broader bash-on-Windows patterns.

## Known Issues
- Glob tool may not work with paths on different drives (untested with D:\, E:\)
- `find` command (Unix) doesn't exist on Windows — use `Glob` tool or Python `os.walk()`
