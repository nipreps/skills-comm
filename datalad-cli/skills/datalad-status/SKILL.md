---
name: datalad-status
description: >
  Auto-invoke inside a DataLad dataset (.datalad/ present) when the user asks what has
  changed, what is modified, what files are untracked, or what the current dataset state
  is. Trigger on "what changed", "check state", "show modified", "what's untracked",
  "dataset status", or /datalad-status. Read-only — never modifies any files.
argument-hint: [paths...]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-status

Inspect the current state of a DataLad dataset — what files are modified, untracked,
added, or deleted — without making any changes.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or any
   parent:
   ```bash
   ls .datalad/ 2>/dev/null || git rev-parse --show-toplevel
   ```
   - **Dataset found**: continue.
   - **No dataset found**: inform the user and suggest `/datalad-init` or plain `git status`.

2. **Run `datalad status`** — optionally scoped to paths from `$ARGUMENTS`:
   ```bash
   datalad status [paths...]
   ```
   Present the full output to the user. Additional flags to mention if relevant:
   - `--annex` — shows verbose annex content state (number of copies, remote presence)
     for each annexed file; useful for understanding data availability
   - `--untracked=no` — suppresses untracked files from output (useful in large repos
     with many untracked directories that would otherwise clutter the output)

3. **Interpret the status symbols** — explain each symbol present in the output:

   | Symbol | Meaning |
   |--------|---------|
   | `modified` | Content changed since last save |
   | `untracked` | File exists on disk but is not recorded in the dataset |
   | `deleted` | File was tracked but is now missing from disk |
   | `added` | New file staged but not yet saved |
   | `clean` | No changes — working tree matches the last commit |

   For annexed files, also explain:
   - **content present**: file pointer exists and content is available locally
   - **content missing**: file pointer exists but content was dropped (pointer only)

4. **Suggest next actions** — based on what was found:
   - Modified or untracked files → suggest `/datalad-save`
   - Missing annex content → suggest `datalad get <path>` to retrieve it
   - Output files that should have been produced by a command → suggest `/datalad-run`
   - Clean working tree → confirm no action needed

## Constraints

- Read-only — never run any command that modifies the dataset, stages files, or commits.
- Always explain every status symbol that appears in the output — never show raw output
  without interpretation.
- If the user asks about a specific path, scope the status command to that path.
- Do not confuse `datalad status` (dataset state) with `git status` — they overlap but
  DataLad status correctly handles annexed files that git would misreport.
