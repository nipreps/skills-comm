---
name: datalad-clone
description: >
  Auto-invoke when the user wants to obtain a copy of a dataset from a URL or path,
  install a dataset, add a nested subdataset, or link external data as input to a project.
  Trigger on "clone a dataset", "get a copy of", "install dataset", "add subdataset",
  "link this data as input", or /datalad-clone. Use instead of `git clone` when working
  with DataLad datasets. Do NOT trigger for plain git repos without DataLad context.
argument-hint: <source-url-or-path> [dest-path]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-clone

Obtain a copy of a DataLad dataset from a URL or local path. Optionally register it as
a subdataset inside an existing DataLad dataset (YODA-style nested layout).

## Steps

1. **Identify source** — read the source URL or path from `$ARGUMENTS`. If not provided,
   ask the user for the source before continuing. If the URL begins with `ria+`, this is
   a RIA store. Accepted formats: `ria+ssh://user@host/path`, `ria+http://host/path`,
   `ria+file:///local/path`. Load `${CLAUDE_PLUGIN_ROOT}/../references/siblings-and-remotes.md`
   for RIA store URL details.

2. **Determine mode** — decide whether this clone should be:
   - **Standalone**: a new independent dataset (no `-d` flag)
   - **As a subdataset**: nested inside the current dataset (`-d .`)

   Check whether the current working directory is a DataLad dataset:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   - If **inside a dataset** and the user mentions "input data", "nested", "subdataset",
     or a target path like `inputs/raw/sub-01` — default to subdataset mode
   - If **not inside a dataset** or the user says "standalone" — use standalone mode
   - If **ambiguous** — ask:
     > "Should this be registered as a subdataset of the current dataset, or cloned
     > as a standalone dataset?"

3. **Determine destination path** — read from `$ARGUMENTS` or derive from the source
   name (last path/URL component, minus `.git`). Show the planned destination and confirm
   if it differs from what the user expects.

4. **Construct and show command**:
   - Standalone:
     ```
     datalad clone <source> [<dest>]
     ```
   - As subdataset:
     ```
     datalad clone -d . <source> <dest>
     ```
   When cloning on the same filesystem (e.g., HPC scratch → project directory),
   `--reckless=shared-local` skips the safety copy and is substantially faster. Only use
   on trusted local filesystems.
   Always show the full command before executing.

5. **Execute** — run the command. Report the installed path and the commit SHA recorded.

6. **Post-clone reminder** (subdataset mode only) — after cloning as a subdataset, the
   superdataset's working tree is modified but not yet committed. Remind the user:
   > "The subdataset pointer is not yet saved. Run:
   > `datalad save -m 'add <name> as subdataset'`
   > to record it in the superdataset history."

## Reference

Load `${CLAUDE_PLUGIN_ROOT}/../references/subdataset-patterns.md` when the user asks
about nested layouts, why `-d .` is needed, or the YODA neuroimaging project structure.

Load `${CLAUDE_PLUGIN_ROOT}/../references/yoda-layout.md` when the user asks about the
YODA directory layout, `.gitattributes` rules, or how `inputs/` and `outputs/` are
structured.

## Constraints

- Never use `git clone` for DataLad datasets — use `datalad clone` to preserve annex
  configuration and special remote registrations.
- Never use `datalad install` — it is a deprecated alias for `datalad clone`.
- Never use `git submodule add` directly — DataLad manages submodule entries via
  `datalad clone -d .`.
- Always show the full command before executing.
- Always prompt for a follow-up `datalad save` after a subdataset clone.
