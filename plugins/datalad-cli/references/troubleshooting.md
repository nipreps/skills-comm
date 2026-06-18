# DataLad Troubleshooting Reference

## Step 0: increase log verbosity

Before anything else, re-run the failing command with `-l debug` to see every
git/annex call DataLad makes:

```bash
datalad -l debug <subcommand> [opts]
```

`-l debug` is the fastest way to distinguish a DataLad logic error from a network
issue, a permission problem, or a git-annex version mismatch. Only escalate after
reading the debug output.

---

## First diagnostic: `datalad wtf`

`datalad wtf` ("What The F...") is the standard first step for any DataLad issue.
It reports:
- DataLad version and installed extensions
- git-annex version
- Python version and environment
- Dataset configuration summary
- System platform info

```bash
datalad wtf
datalad wtf -S <section>   # e.g., -S datalad, -S git-annex, -S system
```

Always run `datalad wtf` before reporting a bug or escalating an issue — version
mismatches between DataLad and git-annex are a frequent root cause.

---

## Failed `datalad run` cleanup

When `datalad run` fails mid-execution, outputs declared with `-o` are left **unlocked**
(materialized as regular writable files, not symlinks). Nothing is committed.

**Signs you are in this state**:
```bash
datalad status   # shows unlocked output files as "modified" or "untracked"
git status       # shows annex-unlocked files
```

**Recovery options**:

### Option A — Discard partial outputs and retry
```bash
# Re-lock and discard the partial outputs
git checkout -- <output-path>
# or for all modified annex files:
git checkout -- .
# Then fix the command and re-run
```

### Option B — Save partial outputs as a checkpoint
```bash
datalad save -m "partial run output (failed): <description>"
```
Use this if the partial outputs are useful for debugging. The commit message makes
it clear this is not a successful run.

### Option C — Inspect the exact failure point
```bash
# Check what outputs were declared
git log --oneline -1   # most recent commit (before the failed run)
datalad status         # see what changed
```

**Important**: never leave a dataset in an unlocked state between sessions — the
auto-checkpoint hook will save unlocked files with a checkpoint message, which can
obscure the failure context.

---

## Verifying content integrity: `git annex fsck`

Check that locally present annex content matches its recorded checksum:
```bash
git annex fsck                    # verify all local content
git annex fsck <path>             # verify a specific file
git annex fsck --fast             # skip checksum (just check existence)
git annex fsck --from <remote>    # verify content on a remote
```

Run `fsck` after:
- Copying datasets between machines
- Storage hardware failures or filesystem errors
- Suspecting silent corruption

Output shows `ok` for each intact file, `failed` for corrupt or missing content.

---

## Timestamp issues: `datalad check-dates`

DataLad uses file modification times in some operations. If timestamps are wrong
(e.g., after a tar extraction that reset mtimes), use:
```bash
datalad check-dates
datalad check-dates --annex      # also check annex objects
```

This reports files with timestamps that look suspicious (future dates, epoch=0, etc.).

---

## Common error patterns

### `NoDatasetFound`
DataLad cannot find a dataset in the current directory or any parent.
```bash
# Check where you are
pwd
ls .datalad/ 2>/dev/null    # should exist
# Navigate to dataset root, or run datalad-init
```

### `IncompleteResultsError` during `datalad get`
Content is not available from any configured remote.
```bash
git annex whereis <path>    # see where copies are registered
datalad siblings            # check which siblings are configured
datalad update --merge      # update remote refs before retrying get
```

### `git-annex: not enough copies` on `datalad drop`
Safety check: only one copy exists.
```bash
git annex whereis <path>    # confirm only 'here'
datalad push --to <sibling> # push to a remote first, then retry drop
```

### Slow or hung `datalad push`
Usually waiting for git-annex to transfer large content.
```bash
# Check what is being transferred
git annex copy --to <remote> --json   # more verbose output
# Or push just git history (no content):
git push <remote> <branch>
```

### Submodule mismatch after `datalad update`
Subdataset HEAD is at a different commit than what the superdataset recorded.
```bash
datalad status -r    # shows subdataset state
datalad save -r -m "update subdataset pointers"
```
