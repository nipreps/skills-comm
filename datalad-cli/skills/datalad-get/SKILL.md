---
name: datalad-get
description: >
  Auto-invoke when a user cannot open a file because content is missing or shows as a
  broken symlink, wants to download annexed file content, fetch data from a sibling, or
  initialize an absent subdataset. Trigger on "get this file", "download content",
  "fetch data", "retrieve", "I can't open this file", "content missing", "file is empty",
  "broken symlink", or /datalad-get. Do NOT trigger for plain file copies or downloads
  unrelated to DataLad datasets.
argument-hint: <path-or-glob> [-r] [-n]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-get

Retrieve annexed file content or initialize absent subdatasets. `datalad get` fetches
content from configured siblings (remotes) and makes files accessible locally.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null || git rev-parse --show-toplevel
   ```
   If no dataset is found, inform the user and stop — `datalad get` only works inside
   a DataLad dataset.

2. **Identify targets** — read paths, globs, or subdataset handles from `$ARGUMENTS`.
   If not specified, ask the user what they want to retrieve. For large datasets with many
   files, mention `--jobs N` (e.g., `--jobs 4`) to retrieve content in parallel.

   Determine the nature of each target:
   - **File or directory**: retrieve annexed content (`datalad get <path>`)
   - **Subdataset path**: may need `-n` (handle only) or full content (`-r`)

3. **Determine retrieval mode** — ask or infer:
   - **Full content** (default): downloads file data so files are accessible
   - **Handle only** (`-n`): clones the subdataset without downloading file content —
     useful to inspect structure before committing to a large download
   - **Recursive** (`-r`): retrieves content in all subdatasets under the path

4. **Construct command**:
   - Single file or directory:
     ```
     datalad get <path>
     ```
   - Recursive (all subdatasets + files):
     ```
     datalad get -r <path>
     ```
   - Subdataset handle only (no file content):
     ```
     datalad get -n <subdataset-path>
     ```
   Show the command before executing.

5. **Execute and confirm** — run the command. After completion, verify content is
   accessible:
   ```bash
   ls -lh <path>
   ```
   Report whether files are now readable (regular files, not broken symlinks).

## Reference

Load `${CLAUDE_PLUGIN_ROOT}/../references/subdataset-patterns.md` for the absent/present
subdataset model, the `-n` handle-only pattern, and the neuroimaging nested layout.

Load `${CLAUDE_PLUGIN_ROOT}/../references/global-options.md` when the user asks about
`--on-failure` behavior during recursive gets, wants JSON output, needs to override a
config value, or asks why a get is failing (suggest `-l debug`).

## Constraints

- `datalad get` is **read-only with respect to dataset metadata** — it never modifies
  tracked state or creates new commits.
- Distinguish "content missing" (needs `datalad get`) from "file untracked" (needs
  `datalad save`) — do not confuse the two.
- Never modify `.gitmodules` directly — if a subdataset is absent, use `datalad get -n`
  to initialize it, not manual git submodule commands.
- Always show the command before executing.
- If retrieval fails due to no configured sibling, suggest running `datalad siblings`
  to check available remotes and `datalad siblings enable -s <name>` if a special
  remote needs to be activated.
