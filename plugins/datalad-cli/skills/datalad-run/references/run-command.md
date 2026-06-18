# `datalad run` Command Reference

## Core Syntax

```
datalad run -m "<message>" [-i <input>...] [-o <output>...] "<command>"
```

The command string must be quoted as a single argument. DataLad records it verbatim in
the commit message so it can be replayed exactly.

---

## Flag Reference

| Flag | Long form | Purpose |
|---|---|---|
| `-m` | `--message` | Commit message describing the run (required; use a meaningful sentence) |
| `-i` | `--input` | Input path(s) — DataLad unlocks (gets) these from annex before running |
| `-o` | `--output` | Output path(s) — DataLad unlocks these before running, stages them after |
| `-d` | `--dataset` | Dataset to run in (default: current working directory dataset) |
| `--explicit` | | Require explicit `-i`/`-o` declarations; fail if undeclared files change |
| `--expand` | | Expand glob patterns in `-i`/`-o` at record time (`{inputs}` or `{outputs}`) |
| `--dry-run` | | Show what would be run without executing (useful for checking the command) |
| `--rerun-since` | | Rerun all recorded commands since a given commit |
| `--assume-ready` | | Skip the input unlock step (use when inputs are already unlocked) |

---

## What `-i` (input) does

1. Calls `datalad get <input>` to retrieve file content from annex before the command runs
2. Records the input path in the commit provenance so the exact files consumed are known
3. Supports glob patterns: `-i "inputs/data/*.nii.gz"`

Omit `-i` only if the command reads no files (rare). If inputs are omitted and the
command reads annexed files, it may fail because the content is not retrieved.

---

## What `-o` (output) does

1. Calls `git annex unlock <output>` before the command runs so the command can write to it
2. After the command exits successfully, stages the output files and commits them
3. Supports glob patterns: `-o "outputs/sub-*/results.tsv"`

If you forget `-o`, the outputs remain as untracked modifications in the working tree —
they are not recorded in the dataset history. Always declare outputs.

---

## Glob Pattern Usage

```bash
# Multiple inputs
datalad run -m "process all subjects" \
  -i "inputs/sub-*/anat/*.nii.gz" \
  -o "outputs/sub-*/anat_processed.nii.gz" \
  "bash process_all.sh"

# Template expansion (use {inputs} and {outputs} in command)
datalad run -m "convert format" \
  --expand inputs \
  -i "inputs/*.csv" \
  "python convert.py {inputs}"
```

---

## Pipeline Wrapping Pattern

Pipes and multi-step shell commands must be wrapped in a single quoted string:

```bash
datalad run -m "extract and sort results" \
  -i "outputs/raw_results.txt" \
  -o "outputs/sorted_results.txt" \
  "bash -c 'grep PASS outputs/raw_results.txt | sort > outputs/sorted_results.txt'"
```

For complex pipelines, prefer writing a script in `code/` and calling it:

```bash
datalad run -m "run full analysis pipeline" \
  -i "inputs/" \
  -o "outputs/" \
  "bash code/run_analysis.sh"
```

---

## Replaying Recorded Commands (`datalad rerun`)

Every successful `datalad run` is recorded as a commit with provenance metadata. To
replay a command:

```bash
# Replay the most recent datalad run
datalad rerun

# Replay a specific commit
datalad rerun <commit-sha>

# Replay a range of commits
datalad rerun <start-sha>..<end-sha>
```

`datalad rerun` re-executes the command exactly as recorded, re-fetches inputs if needed,
and creates a new commit. The replay is also recorded, creating a chain of provenance.

---

## Recording Download Provenance (`datalad download-url`)

To record where a file came from when downloading it:

```bash
datalad download-url -m "download reference atlas from source" \
  https://example.com/atlas.nii.gz \
  --path inputs/atlas.nii.gz
```

This creates a commit that records the URL, file content, and download time — satisfying
YODA P2 (record data origins) without requiring a full subdataset.

---

## Common Pitfalls

**Forgetting `-o`**: Outputs remain as untracked modifications after the command. Fix:
run `datalad save -m "..."` manually to record them, or rerun with `-o` declared.

**Unclean working tree**: `datalad run` may warn or fail if there are unsaved changes.
Run `datalad status` first; if changes exist, `datalad save -m "..."` them first.

**Pipe commands not wrapped**: `datalad run -m "msg" "cmd1 | cmd2"` will fail because
the shell interprets the pipe before DataLad sees the string. Always use
`"bash -c 'cmd1 | cmd2'"`.

**Using `datalad run` for no-output commands**: Commands like `ls`, `git log`, or
`cat` produce no files to track. Run these bare — using `datalad run` adds an empty
commit with no value.

---

## When NOT to Use `datalad run`

- Exploratory commands that produce no files (`ls`, `git log`, `head`, `cat`)
- Interactive sessions (Jupyter notebooks run interactively — save output cells manually)
- Commands that modify source code in `code/` — use `datalad save` for those
- Installing software or system packages — those are environment setup, not analysis steps
