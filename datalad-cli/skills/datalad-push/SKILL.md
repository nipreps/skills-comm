---
name: datalad-push
description: >
  Auto-invoke when the user wants to transfer saved dataset state to a remote, publish
  a dataset, upload annexed content to a sibling, share changes with collaborators, or
  push to GitHub, OSF, or other storage. Trigger on "push to remote", "publish dataset",
  "upload to sibling", "share changes", "push to GitHub", "send to storage", or
  /datalad-push. Do NOT trigger for plain git push in repos without DataLad context.
argument-hint: --to <sibling> [--data {nothing|anything|auto-if-wanted}] [-r]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-push

Transfer saved dataset state — git history and/or annexed file content — to a configured
sibling (remote). Respects publish-depends ordering so annexed data reaches storage
before git history reaches the git host.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, inform the user and stop.

2. **Check for uncommitted changes** — run `datalad status`:
   ```bash
   datalad status
   ```
   If the working tree is dirty, warn:
   > "There are unsaved changes. Push will only transfer already-committed state. Save
   > first with `datalad save -m '...'`?"
   Wait for the user to save or confirm they want to push the current committed state.

3. **Identify target sibling** — read from `$ARGUMENTS`. If not provided, list available
   siblings and ask which one to push to:
   ```bash
   datalad siblings
   ```

4. **Determine data mode** — present the choice:
   - **auto-if-wanted** (default): pushes only content the sibling has declared it wants
     via its `annex-wanted` expression. This is the default but **only works when the
     sibling has `annex-wanted` configured** — if not configured, no content will be pushed
   - **nothing**: push git history only, skip all annexed content
   - **anything**: push all locally present annexed content regardless of wanted rules

   Ask if annexed data handling is unclear from context.

5. **Determine recursion** — ask if the user wants to push subdatasets too:
   > "Push subdatasets recursively as well? (`-r`)"
   If yes, also mention `--on-failure ignore` — without it a single subdataset failure
   aborts the entire recursive push. With it, failures are logged and the push continues
   across remaining subdatasets.

6. **Construct and show command**:
   ```
   datalad push --to <sibling> [--data {nothing|anything|auto-if-wanted}] [-r]
   ```
   Show the full command before executing.

7. **Execute and report** — run the command. Report:
   - Which git refs were pushed
   - How many annexed objects were transferred (if any)
   - If a `--publish-depends` sibling was pushed first, note that too

## Reference

Load `${CLAUDE_PLUGIN_ROOT}/../references/siblings-and-remotes.md` for publish-depends
ordering, `--data` mode details, and why annexed content must reach storage before git
history reaches the git host.

Load `${CLAUDE_PLUGIN_ROOT}/../references/global-options.md` when the user asks about
`--on-failure` for recursive pushes, wants JSON output from push results, or needs to
debug a failed push (`-l debug`).

## Constraints

- Always check for a dirty working tree before pushing — never push without this check.
- Always show the full command before executing.
- Warn if the target sibling has no `--publish-depends` configured and annexed content
  is present in the dataset:
  > "This sibling has no storage dependency configured. Annexed file content may not be
  > accessible to consumers who clone the git history. Consider setting up a storage
  > sibling and adding `--publish-depends`."
- Never use `git push` directly inside a DataLad dataset — it bypasses annexed content
  handling and publish-depends ordering.
