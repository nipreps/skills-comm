---
name: datalad-container-run
description: >
  Auto-invoke when about to execute a command inside a container (Singularity .sif file,
  Apptainer image, Docker image) that produces output files inside a DataLad dataset.
  Trigger on "run in container", "run with Singularity", "run with Apptainer",
  "run with Docker", "containerized analysis", "remove a container", "unregister container",
  or /datalad-container-run. Records both the command and the container image in dataset
  provenance. Do NOT trigger for bare datalad run commands without a container — use
  datalad-run for those.
argument-hint: [container-name command]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-container-run

Wrap a command in `datalad container-run` to record the container image, the command,
inputs, and outputs in the dataset history. The container image content hash is annexed,
so the full computational environment is reproducible via `datalad rerun`.

Always load `${CLAUDE_PLUGIN_ROOT}/references/container-run.md` before any container
registration or container-run step.

## Steps

1. **Identify command and container** — read `$ARGUMENTS` or extract from conversation
   context. Determine:
   - The container image (`.sif` path, Docker image name, Singularity/Apptainer URL)
   - The command to run inside the container
   If either is ambiguous or missing, ask the user to specify both before continuing.

2. **Verify DataLad context** — check whether cwd is inside a DataLad dataset:
   ```bash
   ls .datalad/
   ```
   - **Dataset found**: continue.
   - **No dataset found**: ask the user:
     > "No DataLad dataset detected. Would you like to:
     > 1. Initialize one here with `/datalad-init`
     > 2. Run the container command bare (no provenance tracking)"
     Wait for their choice.

3. **Check for unsaved changes** — run `datalad status`. If the output shows modified
   or untracked files, prompt the user to save first with `/datalad-save` or confirm
   they want to proceed anyway.

4. **Container registration check** — run `datalad containers-list` to see registered
   containers:
   - **Container already registered**: proceed to step 5.
   - **Not registered**: guide the user through `datalad containers-add`:
     a. Ask for a short name (identifier) for the container.
     b. Confirm the image URL or local `.sif` path (`--url`).
     c. Ask which runtime to use; load `${CLAUDE_PLUGIN_ROOT}/references/container-run.md`
        and show the call-format options table (Singularity, Apptainer, Docker).
     d. Construct and display the `datalad containers-add` command:
        ```
        datalad containers-add <name> \
          --url <image-url-or-path> \
          --call-fmt "<call-format>"
        ```
     e. Execute after user confirmation. On failure, show error and stop.

5. **Gather run parameters** — ask the user (or infer from context) for:
   - **`-i` (inputs)**: files or glob patterns the command reads (omit if none)
   - **`-o` (outputs)**: files or glob patterns the command writes (required if outputs exist)
   - **`-m` (message)**: a meaningful description of what this run does (required)

6. **Construct and show the full command** — build the complete invocation and display
   it before executing:
   ```
   datalad container-run \
     --container-name <name> \
     -m "<message>" \
     [-i <input>...] \
     [-o <output>...] \
     "<command>"
   ```
   Then ask: > "Ready to execute? (yes / edit)"

7. **Execute and report** — after user confirmation, run the constructed command.
   - On **success**: report the commit hash (includes container image hash), output files
     recorded, and that the container image and command are now in dataset history.
   - On **failure**: show error output; note that nothing was committed.

## Removing a registered container (`datalad containers-remove`)

When the user wants to deregister a container:

1. **List registered containers** to confirm the name:
   ```bash
   datalad containers-list
   ```

2. **Warn the user** — removing a container drops its registration and annexed image
   from the dataset. Runs that used this container remain in history but cannot be
   replayed (the image would need to be re-added):
   > "Removing '<name>' will drop the container image from the dataset. Past runs
   > referencing it will no longer be replayable unless you re-add the image. Proceed?"

3. **Remove after confirmation**:
   ```bash
   datalad containers-remove <name>
   ```

4. **Save the change**:
   ```bash
   datalad save -m "remove container <name>"
   ```

## Constraints

- Always load `${CLAUDE_PLUGIN_ROOT}/references/container-run.md` before any container
  registration or container-run step.
- Never call `datalad container-run` with an unregistered container name — always verify
  with `datalad containers-list` first.
- Never skip showing the full constructed command before executing.
- Always require a meaningful `-m` message — never use empty or placeholder messages.
- For pipelines inside the container, wrap as `"bash -c 'cmd1 | cmd2'"` passed to the
  container call.
- The `--call-fmt` must contain both `{img}` and `{cmd}` placeholders — if either is
  missing, the container will be invoked incorrectly. Flag this to the user.
- For `containers-remove`: always confirm before executing and always follow with
  `datalad save` to record the removal.
