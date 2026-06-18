---
name: datalad-diff
description: >
  Auto-invoke inside a DataLad dataset (.datalad/ present) when the user wants to compare
  file states between revisions, commits, or branches. Trigger on "what changed between
  commits", "show diff", "compare revisions", "what was different", "changes since HEAD",
  or /datalad-diff. Read-only — never modifies any files.
argument-hint: [revision-range] [paths...]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-diff

Compare file-level state between two points in a DataLad dataset's history. `datalad diff`
reports which files changed and their annex state transitions — it does not show line-level
content diffs.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or any
   parent:
   ```bash
   ls .datalad/ 2>/dev/null || git rev-parse --show-toplevel
   ```
   - **Dataset found**: continue.
   - **No dataset found**: inform the user; suggest plain `git diff` for non-DataLad repos.

2. **Determine the comparison scope** — read `$ARGUMENTS` and conversation context to
   identify what the user wants to compare. Map to one of these forms:

   | User intent | Command form |
   |-------------|-------------|
   | Working tree vs last commit | `datalad diff` (no args) |
   | Working tree vs specific commit | `datalad diff --from <hash>` |
   | Two specific commits | `datalad diff --from <hash-a> --to <hash-b>` |
   | Named revision (branch, tag) | `datalad diff --from <ref>` |

   If the scope is ambiguous, ask the user:
   > "Are you comparing the current working tree to HEAD, or two specific commits?
   > If comparing commits, please provide the commit hashes or branch names."

3. **Construct and run the diff command**:
   ```bash
   datalad diff [--from <ref>] [--to <ref>] [paths...]
   ```
   Show the command before running it. Present the full output to the user.

4. **Interpret the output** — explain the change types shown:

   | Type | Meaning |
   |------|---------|
   | `added` | File did not exist in the earlier revision; exists in the later one |
   | `deleted` | File existed in the earlier revision; removed in the later one |
   | `modified` | File content changed between revisions |
   | `untracked` | File is present locally but outside the compared revision range |

   For annexed files, note that `datalad diff` reports pointer-level changes (key
   changed), not byte-level diffs.

5. **Clarify line-level diffs if asked** — `datalad diff` is file-level only. If the
   user needs to see line-by-line content changes, point them to:
   ```bash
   git diff <hash-a> <hash-b> -- <path>
   ```
   This works for git-tracked files; annexed file content must be retrieved first with
   `datalad get <path>` before `git diff` can show it.

## Constraints

- Read-only — never stage, commit, or modify any file.
- Always show the constructed command before running it.
- Always explain that `datalad diff` is file-level, not line-level, and direct the user
  to `git diff` when they need line-level comparisons.
- If the user provides only one hash/ref, treat it as `--from` (compare that ref to the
  current working tree) and confirm this interpretation before running.
- Do not use `git diff` as a substitute — `datalad diff` correctly handles annexed file
  pointers and subdataset boundaries.
