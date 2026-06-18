---
name: datalad-run
description: >
  Auto-invoke when about to execute a script, pipeline, or transformation that reads
  input data files and writes output files — e.g., `python analysis.py`, `bash process.sh`,
  neuroimaging tools (fMRIPrep, MRIQC, FSL, FreeSurfer), or any shell command that
  produces result files in a DataLad dataset. Also trigger on "run with provenance",
  "track this command", "record this analysis", "replay this run", "rerun a recorded
  command", "download this file with provenance", "record download", or /datalad-run.
  Do NOT trigger for commands that produce no output files (git log, ls, exploratory queries).
argument-hint: [command-to-run]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-run

Wrap a command in `datalad run` to record it in the dataset history with full provenance:
inputs consumed, outputs produced, and the exact command used. On success, DataLad
automatically stages and commits the outputs. On failure, nothing is committed.

## Steps

1. **Identify the command** — read `$ARGUMENTS` or extract from conversation context.
   If the command is ambiguous or missing, ask the user to specify the full command
   string before continuing.

2. **Verify DataLad context** — check whether the current working directory (or the
   project directory) is inside a DataLad dataset:
   ```bash
   ls .datalad/
   ```
   - **Dataset found**: continue.
   - **No dataset found**: ask the user:
     > "No DataLad dataset detected in the current directory. Would you like to:
     > 1. Initialize one here with `/datalad-init`
     > 2. Run the command bare (no provenance tracking)"
     Wait for their choice. If bare, run the command directly and stop.

3. **Check for unsaved changes** — run `datalad status`. If the output shows modified
   or untracked files, prompt:
   > "There are unsaved changes in the dataset. DataLad run records a clean snapshot
   > before executing. Save now with `datalad save -m \"...\"` first?"
   Wait for the user to either save or confirm they want to proceed anyway.

4. **Gather run parameters** — ask the user (or infer from context) for:
   - **`-i` (inputs)**: files or glob patterns the command reads (can be omitted if none)
   - **`-o` (outputs)**: files or glob patterns the command writes (required if outputs exist)
   - **`-m` (message)**: a meaningful description of what this run does (required)

   For pipelines with multiple stages, suggest wrapping as:
   ```
   bash -c 'cmd1 | cmd2'
   ```

   If the user wants to use `--explicit`: all declared output paths (`-o`) must be
   **pre-unlocked** before the run (`datalad unlock <output-path>`). Without pre-unlocking,
   the run will fail with a locked-path error. Confirm outputs are unlocked before constructing
   the command.

4b. **Optional dry-run** — to verify the command before committing, suggest:
   ```
   datalad run --dry-run <command>
   ```
   This executes the command without creating a commit, letting the user confirm
   outputs are produced as expected before recording provenance.

5. **Construct and show the command** — build the full `datalad run` invocation and
   display it to the user before executing:
   ```
   datalad run \
     -m "<message>" \
     [-i <input-path>] \
     [-o <output-path>] \
     "<command>"
   ```
   Multiple `-i` and `-o` flags are allowed. Show the exact command, then ask:
   > "Ready to execute? (yes / edit)"

6. **Execute and report** — after user confirmation, run the constructed command.
   Report:
   - On **success**: the commit hash DataLad created, the output files recorded, and
     that the outputs are now tracked in the dataset history
   - On **failure**: that the command failed and nothing was committed; show the error
     output and suggest how to fix it

## Constraints

- Always show the full constructed `datalad run` command to the user before executing —
  never run silently.
- Never use `datalad run` for commands that produce no output files (e.g., `git log`,
  `ls`, `cat`, exploratory queries). Use bare Bash for those instead.
- Always require a meaningful `-m` message — never use empty or placeholder messages
  like "run" or "analysis".
- Never skip the unsaved-changes check — a dirty working tree can produce misleading
  provenance records.
- For pipeline commands (pipes, multi-step shell), always wrap as `"bash -c 'cmd1 | cmd2'"`.
- Load `${CLAUDE_PLUGIN_ROOT}/references/run-command.md` when the user asks about
  advanced flags (`--explicit`, `--expand`, `--dry-run`), replaying runs (`datalad rerun`),
  or recording download provenance (`datalad download-url`).
- Load `${CLAUDE_PLUGIN_ROOT}/../references/yoda-layout.md` when the user asks about
  YODA directory conventions, where outputs should go, or why inputs are subdatasets.
- Load `${CLAUDE_PLUGIN_ROOT}/../references/troubleshooting.md` when a run fails, the
  user has unlocked output files left over, or asks how to recover from a partial run.
- If the run fails with a "locked" or "permission denied" error on output files, the fix
  is: `datalad unlock <output-path>`, then re-run. Load
  `${CLAUDE_PLUGIN_ROOT}/../references/troubleshooting.md` for the full recovery pattern.
- Load `${CLAUDE_PLUGIN_ROOT}/../references/global-options.md` when the user asks about
  debugging a failed run (`-l debug`), suppressing result output in CI (`-f disabled`),
  overriding annex config for a single run (`-c`), or running against a different working
  directory (`-C`).

## Replaying recorded runs (`datalad rerun`)

When the user wants to replay a previously recorded run:

1. **Identify the target commit** — ask the user for the commit SHA, or use the most
   recent `datalad run` commit if they say "the last run":
   ```bash
   git log --oneline --grep="datalad run" -5
   ```

2. **Construct the rerun command**:
   - Replay the most recent run: `datalad rerun`
   - Replay a specific commit: `datalad rerun <sha>`
   - Replay a range: `datalad rerun <start>..<end>`

3. **Show and confirm** before executing — a rerun re-executes the original command
   with the same inputs and outputs, creating a new commit. This is not reversible.

4. **Report outcome** — on success, note the new commit SHA and that this replay is
   also recorded in dataset history (provenance chain). On failure, show the error.

Load `${CLAUDE_PLUGIN_ROOT}/references/run-command.md` for the full flag reference.

## Recording download provenance (`datalad download-url`)

When the user wants to download a file and record where it came from:

1. **Gather parameters**:
   - URL to download from
   - Local destination path (`--path`)
   - A meaningful message (`-m`)

2. **Construct command**:
   ```bash
   datalad download-url -m "<message>" \
     --path <local-path> \
     <url>
   ```

3. **Show and confirm** — this creates a DataLad commit recording the URL, content
   hash, and download time. The file is annexed automatically.

4. **After download** — suggest verifying with `datalad status` and `git annex whereis`.

Use this instead of `wget`/`curl` whenever the file's origin should be tracked in
dataset history (YODA P2: record data origins).
