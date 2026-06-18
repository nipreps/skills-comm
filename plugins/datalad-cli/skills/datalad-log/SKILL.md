---
name: datalad-log
description: >
  Auto-invoke when the user wants to browse dataset history, find what command produced
  a specific output, inspect recorded run provenance, or audit past analyses. Trigger on
  "show run history", "what command produced this", "browse dataset history", "find the
  run that made this file", "show provenance", "list recorded runs", "what was the last
  run", or /datalad-log. Do NOT trigger for running new commands (use datalad-run) or
  replaying existing runs (use datalad-run's rerun section).
argument-hint: [path-or-commit]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-log

Browse the recorded history of a DataLad dataset: list run commits, inspect what a
specific run recorded, and trace which command produced a given output file.

## Steps

### Browsing run history

1. **Verify DataLad context** — check for `.datalad/` in the current directory:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If not in a dataset, stop and inform the user.

2. **List recorded runs** — show the run history with:
   ```bash
   datalad log --oneline
   ```
   Or to show only `datalad run` commits (excludes saves, checkpoints, manual commits):
   ```bash
   git log --oneline --grep="datalad run"
   ```
   Present the output as a numbered list showing commit SHA and message.

3. **Inspect a specific run** — when the user wants detail on a particular commit:
   ```bash
   datalad rerun --report <sha>
   ```
   This shows the run record (command, inputs, outputs, message) without re-executing.
   Report:
   - The original command
   - Declared inputs (`-i`)
   - Declared outputs (`-o`)
   - Commit message
   - Timestamp

### Tracing output provenance

When the user asks "what command produced `<file>`":

1. **Find commits that touched the file**:
   ```bash
   git log --oneline -- <path>
   ```

2. **Check each commit for a run record**:
   ```bash
   datalad rerun --report <sha>
   ```
   If the commit is a `datalad run` commit, this shows the full run metadata.
   If it is a plain save or checkpoint, report that instead.

3. **Report the full provenance chain** — if the file was produced by a run, show:
   - Which commit recorded it
   - The command that produced it
   - The declared inputs to that command

### Identifying checkpoint commits

The auto-checkpoint hook creates commits with messages like:
```
[datalad] checkpoint 2026-03-12T14:05:22Z: code/analysis.py outputs/result.csv
```
These are **not** run records — they are auto-saves. They will appear in `git log` and
`datalad log` output. To show only `datalad run` commits (excludes checkpoints and saves):
```bash
git log --oneline --grep="\[datalad run\]"
```
Note: using `--invert-grep` with multiple `--grep` flags uses OR logic and will not
correctly exclude checkpoints — use the single `--grep="\[datalad run\]"` form instead.

## Constraints

- Never re-execute a run when the user only wants to inspect it — always use
  `datalad rerun --report` for inspection, not `datalad rerun` alone.
- Always distinguish between `datalad run` commits (provenance records) and plain save
  commits or checkpoint commits in your report.
- If `datalad log` is not available (older DataLad), fall back to
  `git log --oneline --grep="datalad run"` and explain the fallback.
- For file-level differences between two commits, direct the user to `/datalad-diff`.
