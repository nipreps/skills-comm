---
name: datalad-subdatasets
description: >
  Auto-invoke when the user wants to list nested datasets, inspect the subdataset tree,
  check which subdatasets are absent or present, set a property on a subdataset
  registration, or run a command across all subdatasets. Trigger on "list subdatasets",
  "show nested datasets", "check subdataset status", "what subdatasets exist", "subdataset
  is absent", "set subdataset property", "run on all subdatasets", "foreach dataset",
  "iterate over subdatasets", or /datalad-subdatasets. Do NOT trigger for plain git
  submodule commands outside a DataLad dataset.
argument-hint: [--state absent|present] [-r] [--set-property name value path] [foreach-dataset]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-subdatasets

Inspect the subdataset tree and manage subdataset properties. Lists all registered
subdatasets, their state (present/absent), and the commit SHA they are pinned to.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, inform the user and stop.

2. **Determine action** — read from `$ARGUMENTS` or conversation context:
   - **inspect** (default): list all subdatasets
   - **recursive listing**: list the full tree
   - **filter absent**: show only uninitialized subdatasets
   - **set property**: modify a `.gitmodules` entry for a specific subdataset

3. **Construct and run command**:

   ### inspect (default)
   ```bash
   datalad subdatasets
   ```

   ### recursive listing
   ```bash
   datalad subdatasets -r
   ```

   ### filter absent
   ```bash
   datalad subdatasets --state absent
   ```

   ### set property
   Show the command and confirm before running — this modifies `.gitmodules`:
   ```
   datalad subdatasets --set-property <property-name> <value> <subdataset-path>
   ```
   Common properties: `url` (change where the subdataset is fetched from).

   ### run a command across subdatasets (`datalad foreach-dataset`)
   When the user wants to execute a command on every subdataset in the tree, use
   `datalad foreach-dataset`. Gather:
   - The command or DataLad command to run (as a string)
   - Whether to recurse (`-r`) into nested subdatasets
   - Whether to include the superdataset (`--include-super`)

   ```bash
   datalad foreach-dataset [-r] [--include-super] -- <command>
   ```

   Examples:
   ```bash
   # Run datalad status on every subdataset
   datalad foreach-dataset -r -- datalad status

   # Update all subdatasets
   datalad foreach-dataset -r -- datalad update --how=merge

   # Check annex usage in every subdataset
   datalad foreach-dataset -r -- git annex info --fast
   ```

   Always show the full command before executing and warn that errors in one subdataset
   will be reported but processing continues for the rest.

4. **Interpret output** — explain the results to the user:
   - `state: present` — the subdataset is cloned and accessible locally
   - `state: absent` — the subdataset is registered in `.gitmodules` but not yet cloned;
     files are not accessible
   - `gitshasum` — the exact commit the superdataset has pinned for this subdataset

5. **Suggest follow-up** based on what's found:
   - For **absent** subdatasets:
     > "Run `datalad get -n <path>` to initialize the subdataset handle without
     > downloading content, or `datalad get <path>` to initialize and retrieve all files."
   - For **present** subdatasets that appear out-of-date:
     > "Run `datalad update -s origin --how=merge` to pull the latest state."
   - For a large tree with many absent subdatasets:
     > "Run `datalad get -r .` to initialize and retrieve all absent subdatasets and
     > their content at once."

## Reference

Load `${CLAUDE_PLUGIN_ROOT}/../references/subdataset-patterns.md` for the absent/present
model, neuroimaging layout examples, recursive get patterns, and `.gitmodules` structure.

## Constraints

- The **query actions are read-only** — `datalad subdatasets` and `--state` filters do
  not modify any state.
- For `--set-property`: always show the command and ask the user to confirm before
  running — it modifies `.gitmodules`, which is a tracked file that requires a subsequent
  `datalad save` to record the change.
- Never edit `.gitmodules` directly — use `datalad subdatasets --set-property` or
  DataLad's other subdataset management commands.
- Never use `git submodule` commands directly inside a DataLad dataset unless explicitly
  debugging at the git level — DataLad's abstraction layer must be kept consistent.
