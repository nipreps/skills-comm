---
name: datalad-untrack
description: >
  Auto-invoke inside a DataLad dataset (.datalad/ present) when the user wants to free
  disk space by dropping annexed content, remove a file from the dataset entirely, stop
  tracking a file, or unlock an annexed file for in-place editing. Trigger on "drop file
  content", "free disk space", "untrack file", "remove from dataset", "stop tracking",
  "delete this file from the dataset", "unlock this file", "I need to edit an annexed
  file", "make this file writable", or /datalad-untrack. Do NOT trigger for plain file
  deletion outside a DataLad dataset.
argument-hint: [paths...]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-untrack

Remove annexed content from local storage or remove a file from the dataset entirely.
These are two distinct operations with very different consequences. Load
`${CLAUDE_PLUGIN_ROOT}/../references/annex-content-states.md` to reason about annex state
before choosing the operation.

## Steps

0. **Check if the user wants to edit (not drop/remove)** — if the user wants to edit an
   annexed file in place, use `datalad unlock` rather than drop or remove. Editing a
   locked annex file without unlocking first corrupts the annex pointer. See the
   **Unlocking** section below for the full workflow.

1. **Verify DataLad context** — check for `.datalad/` in the current directory or any
   parent:
   ```bash
   ls .datalad/ 2>/dev/null || git rev-parse --show-toplevel
   ```
   - **Dataset found**: continue.
   - **No dataset found**: inform the user. For plain git repos, use `git rm` instead.

2. **Identify the target files** — read paths from `$ARGUMENTS` or conversation context.
   If no paths are specified, ask the user to name the files before continuing.

3. **Check annex state for each target** — run:
   ```bash
   git annex whereis <path>
   datalad status <path>
   ```
   Report:
   - Whether content is present locally
   - How many remote copies exist (if any)
   - Whether the file is annexed or git-tracked only

4. **Present the two-path choice** — show the user a clear decision:

   > **Option A — Drop content** (`datalad drop`):
   > Frees local disk space. The file pointer stays in the dataset. Content can be
   > restored later with `datalad get` IF a remote copy exists.
   >
   > **Option B — Full remove** (`datalad remove` + `datalad save`):
   > Deletes the file pointer from the dataset history. Irreversible locally.
   > The file will no longer appear in `datalad status` or `git ls-files`.

   Ask the user which they want before proceeding.

5. **Warn about remote availability** (Option A only) — if `git annex whereis` shows
   the only copy is `here` (local), warn:
   > "Warning: no remote copy of this content exists. Dropping will make the content
   > unrecoverable unless you have a backup. Use `--nocheck` only if you accept
   > permanent data loss. Proceed?"
   Wait for explicit confirmation before continuing.

6. **Execute the chosen workflow**:

   **Option A — Drop**:
   ```bash
   datalad drop <path>
   ```
   Confirm with `datalad status <path>` that content is now absent (pointer remains).

   **Option B — Full remove**:
   ```bash
   datalad remove <path>
   datalad save -m "remove <path>"
   ```
   Confirm with `datalad status` that the file no longer appears.

7. **Report outcome** — summarize what was done:
   - For drop: disk space freed, pointer retained, how to restore (`datalad get`)
   - For remove: file removed from history, commit recorded

## Unlocking annexed files for in-place editing (`datalad unlock`)

When the user wants to **edit** an annexed file in place (not drop or remove it):

1. **Explain what unlock does** — annexed files are write-protected symlinks. `datalad
   unlock` replaces the symlink with the actual file content, making it writable. After
   editing, `datalad save` re-annexes the file.

2. **Check annex state** — verify the file has content locally (otherwise unlock will
   fail because there's nothing to materialize):
   ```bash
   git annex whereis <path>
   ```
   If content is absent, run `datalad get <path>` first.

3. **Unlock the file**:
   ```bash
   datalad unlock <path>
   ```
   Or unlock multiple files: `datalad unlock <path1> <path2>` or `datalad unlock .`
   to unlock everything in the current directory.

4. **Inform the user** that the file is now writable. After they finish editing, remind
   them to re-annex with:
   ```bash
   datalad save -m "edit <path>"
   ```
   This re-locks the file and records the change in history.

## Constraints

- Never run `git rm` or bare `rm` on an annexed file — this corrupts annex state.
  Always use `datalad drop` or `datalad remove`.
- Always check `git annex whereis` before dropping to assess data loss risk.
- Always warn explicitly when only one copy of content exists before dropping.
- For full removes, always follow `datalad remove` with `datalad save` — the removal
  is not recorded in history until saved.
- Always present the two-path choice and wait for the user's decision — never infer
  which operation to use without asking.
- For `unlock`: always verify content is present locally before unlocking — a pointer-only
  file cannot be unlocked until `datalad get` retrieves the content.
- After `unlock`, always remind the user to `datalad save` when done — unlocked files
  are not re-annexed until saved.
- Load `${CLAUDE_PLUGIN_ROOT}/../references/annex-content-states.md` when reasoning about
  what content states mean or when the user asks about annex concepts.
