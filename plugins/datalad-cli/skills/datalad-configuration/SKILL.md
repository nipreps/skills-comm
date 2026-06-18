---
name: datalad-configuration
description: >
  Auto-invoke when the user wants to read or change DataLad or git-annex configuration
  within a dataset — e.g., setting annex backend, configuring credential helpers,
  adjusting dataset-level variables, or inspecting current config values. Trigger on
  "configure the dataset", "set annex backend", "check dataset config", "set datalad
  config", "change git config in this dataset", "configure credential", or
  /datalad-configuration. Do NOT trigger for global git config unrelated to DataLad.
argument-hint: [get|set|unset] [section.key] [value] [--scope dataset|local|global]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-configuration

Read and write dataset-scoped, clone-local, or global DataLad/git configuration using
`datalad configuration`. This is the DataLad-aware wrapper around `git config` that
handles DataLad-specific keys and scopes correctly.

## Scopes

| Scope | Where stored | Effect |
|-------|-------------|--------|
| `dataset` | `.datalad/config` (committed) | Applies to all clones of this dataset |
| `local` | `.git/config` (not committed) | Applies only to this clone |
| `global` | `~/.gitconfig` | Applies to all repos for this user |

Use `dataset` scope for settings that should travel with the dataset (e.g., annex
backend choice). Use `local` for clone-specific overrides (e.g., credential paths).

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   Configuration can still be inspected/set globally even outside a dataset, but warn
   the user if no dataset is found.

2. **Determine action** — from `$ARGUMENTS` or conversation context:
   - **get**: read the current value of a config key
   - **set**: write a new value
   - **unset**: remove a key

3. **Execute**:

   ### get
   ```bash
   datalad configuration get <section.key>
   # or list all keys in a section:
   datalad configuration get --scope dataset datalad.
   ```

   For common inspection use cases, also accept bare `git config`:
   ```bash
   git config --list --show-origin
   ```

   ### set
   Gather: key (in `section.key` form), value, and scope. Construct and show:
   ```bash
   datalad configuration set --scope <scope> <section.key>=<value>
   ```

   Multiple keys can be set in one call:
   ```bash
   datalad configuration set \
     --scope dataset \
     "annex.backend=SHA256E" \
     "datalad.ui.progressbar=none"
   ```

   For `dataset` scope: the change writes to `.datalad/config`, which must be committed.
   Suggest: `datalad save -m "configure <key>"` after setting.

   ### unset
   ```bash
   datalad configuration unset --scope <scope> <section.key>
   ```

4. **Show command and execute** — always display the full command before running.

## Common configuration keys

| Key | Scope | Purpose |
|-----|-------|---------|
| `annex.backend` | dataset | Hash backend for new files (`SHA256E` recommended) |
| `annex.largefiles` | dataset | Pattern deciding what goes into annex vs. git |
| `datalad.ui.progressbar` | local/global | Progress output style |
| `datalad.locations.cache` | local/global | Where DataLad caches data |
| `remote.<name>.annex-ignore` | local | Tell annex to ignore a remote |
| `user.name` / `user.email` | local/global | Git author identity |

## Constraints

- Always show the full command before executing.
- For `--scope dataset` changes: always remind the user to `datalad save` after setting —
  `.datalad/config` is a tracked file and the change is not recorded until committed.
- Never use `git config` directly for DataLad-specific keys (`datalad.*`, `annex.*`) —
  use `datalad configuration` to ensure DataLad's validation and defaults are applied.
- If the user asks to configure annex `largefiles` patterns, explain the gitattributes
  alternative (`echo "*.csv annex.largefiles=nothing" >> .gitattributes`) as it is more
  portable and does not require a dataset commit to take effect.
