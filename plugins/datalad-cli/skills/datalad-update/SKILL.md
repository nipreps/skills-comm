---
name: datalad-update
description: >
  Auto-invoke when the user wants to fetch changes from a sibling, sync a dataset from
  a remote, pull the latest version of a dataset, or update from a collaborator's push.
  Trigger on "pull updates", "sync from remote", "get latest version", "update from
  sibling", "someone pushed new data", "fetch upstream changes", or /datalad-update.
  Do NOT trigger for plain git fetch/pull in repos without DataLad context.
argument-hint: -s <sibling> [--how {fetch|merge|ff-only}] [--follow parentds] [-r]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-update

Fetch changes from a sibling and optionally integrate them into the current branch.
Handles recursive updates across nested subdataset trees.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, inform the user and stop.

2. **Identify source sibling** — read from `$ARGUMENTS`. If not specified, list available
   siblings and ask:
   ```bash
   datalad siblings
   ```

3. **Determine merge strategy** — ask or infer from context. Present the options:
   - **fetch only** (`--how=fetch`, default): downloads refs and history from the sibling
     but does not touch the working tree. Safe to run anytime; inspect with `git log`.
   - **merge** (`--how=merge`): fetch + merge into the current branch. May create a merge
     commit if histories have diverged.
   - **ff-only** (`--how=ff-only`): fast-forward only. Fails cleanly if histories have
     diverged — use when you want to be sure no unexpected merge occurs.

   Never silently choose a strategy — always make the choice explicit.

4. **Determine recursion** — ask if the update should recurse into subdatasets:
   > "Update subdatasets recursively too? (`-r`)"

5. **For recursive updates with merging** — ask about the `--follow` policy:
   > "When updating subdatasets, should they be pinned to the version recorded in the
   > superdataset (`--follow=parentds`, recommended for reproducibility), or advanced
   > to the sibling's HEAD (`--follow=sibling`)?"

   Explain the difference:
   - `parentds`: checks out each subdataset at the SHA the superdataset has recorded —
     preserves the superdataset's pinned, reproducible state
   - `sibling`: advances each subdataset to the sibling's current HEAD — useful when you
     intentionally want to upgrade all subdatasets and will re-save the superdataset

6. **Construct and show command**:
   ```
   datalad update -s <sibling> --how=<strategy> [--follow=parentds] [-r]
   ```
   Show the full command before executing.

7. **Execute and report** — run the command. After completion:
   - Report what refs were fetched or merged
   - Note if the working tree changed (new commits merged)
   - If fetch-only, suggest running `git log origin/<branch>` to inspect incoming changes
     before merging

## Reference

Load `${CLAUDE_PLUGIN_ROOT}/../references/siblings-and-remotes.md` for `--follow`
semantics and `${CLAUDE_PLUGIN_ROOT}/../references/subdataset-patterns.md` for recursive
update behavior and subdataset pinning.

Load `${CLAUDE_PLUGIN_ROOT}/../references/global-options.md` when the user asks about
`--on-failure` for recursive updates, wants structured output, or needs to debug a
failed update (`-l debug`).

## Constraints

- Never skip the merge-strategy question — a silently applied merge can discard work or
  create unwanted merge commits.
- Always explain what `--follow=parentds` means before using it — users unfamiliar with
  subdataset pinning may be surprised that subdatasets do not advance to the latest HEAD.
- Always show the full command before executing.
- Never use `git pull` inside a DataLad dataset — it bypasses subdataset update logic
  and `--follow` policy.
- If `--how=merge` fails due to diverged histories, inform the user that a manual
  `git merge --allow-unrelated-histories` may be needed as a fallback for first-time
  merges after non-linear setup.
