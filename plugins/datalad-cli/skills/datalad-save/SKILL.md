---
name: datalad-save
description: >
  Auto-invoke inside a DataLad dataset (.datalad/ present) when about to use git add,
  git commit, or when saving code changes, scripts, or configs. Trigger on "save my
  changes", "commit this", "record these edits", "checkpoint my work", or /datalad-save.
  Replaces git add + git commit inside DataLad datasets. Do NOT trigger in plain git
  repos without .datalad/ — use normal git there.
argument-hint: [message] [paths...]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-save

Record code changes, configuration edits, and non-run file modifications in a DataLad
dataset. `datalad save` is the correct replacement for `git add` + `git commit` inside
a DataLad dataset — it handles both git-tracked and annexed files correctly.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or any
   parent directory:
   ```bash
   ls .datalad/ 2>/dev/null || git rev-parse --show-toplevel
   ```
   - **Dataset found**: continue.
   - **No dataset found** (plain git repo or not tracked): fall back to standard
     `git add` + `git commit` workflow and inform the user:
     > "No DataLad dataset detected — using plain git commit instead."

2. **Run `datalad status`** — show the user what has changed:
   ```bash
   datalad status
   ```
   Present the output. If nothing is modified or untracked, stop:
   > "Nothing to save — working tree is clean."

3. **Determine save scope** — based on `$ARGUMENTS` and conversation context:
   - If specific paths are given (e.g., `code/analysis.py configs/`), save only those paths
   - If no paths given, save all changes (`datalad save` without path arguments saves everything)
   - Show the user which scope will be used and confirm if ambiguous

4. **Get or confirm the commit message** — read from `$ARGUMENTS` or ask:
   > "What should the commit message be? (describe what changed and why)"
   Wait for the user's message. Never proceed with an empty or placeholder message.

5. **Construct and show the save command**:
   ```
   datalad save -m "<message>" [paths...]
   ```
   Show it to the user before executing.

6. **Execute and confirm** — run the command. Then run `datalad status` again and show
   the output to confirm the working tree is clean. Report the commit hash.

## Constraints

- Always require a meaningful `-m` message — never save with an empty string or
  placeholder like "save" or "update".
- Never use `git add` or `git commit` inside a DataLad dataset — `datalad save` handles
  both annexed and git-tracked files correctly; raw git commands can corrupt annex state.
- Never use `git annex add` manually — DataLad manages annex staging automatically.
- Always make the save scope explicit: tell the user whether all changes or specific
  paths are being saved.
- Always run `datalad status` before saving to show the user what will be recorded.
- Always run `datalad status` after saving to confirm a clean working tree.
- If the user asks to save outputs produced by a script, redirect them to `datalad run`
  instead — outputs should be recorded with the command that created them, not as
  standalone saves.
- Use `datalad save --to-git <path>` to force a file into git tracking rather than annex
  (useful for small config files, `.gitignore` fragments, etc. that should not be annexed).
- Use `datalad save --version-tag <tag>` to tag an analysis milestone after saving.
