---
name: datalad-init
description: >
  Create a new DataLad dataset with YODA layout, or initialize provenance tracking in
  an existing directory. Trigger on "create a new DataLad dataset", "set up YODA dataset",
  "initialize data provenance tracking", "start a datalad project", or /datalad-init.
  Does NOT trigger for saving changes (use datalad-save) or running commands (use datalad-run).
argument-hint: [target-path]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-init

Create a new DataLad dataset following YODA principles for reproducible, provenance-tracked
local analysis projects. The `-c yoda` configuration is always applied — it sets up the
correct directory layout and `.gitattributes` rules.

## Steps

1. **Determine target path** — read `$ARGUMENTS`. If a path is given, use it. If empty,
   use the current working directory. Show the resolved absolute path and ask the user to
   confirm before proceeding.

2. **Pre-flight checks** — before running any command:
   - Check for an existing `.datalad/` directory at the target path. If found, stop:
     > "A DataLad dataset already exists at `<path>`. Re-initializing would overwrite
     > dataset configuration. Run `datalad status` to check its state."
   - Check whether `.git/annex/` already exists at the target path:
     ```bash
     git annex config annex.backend 2>/dev/null
     ```
     If it returns `MD5E`, warn:
     > "The existing annex uses the legacy MD5E backend. Migrating backends after the
     > fact is complex. Consider initializing a fresh dataset at a new path and
     > re-ingesting data."
     Stop unless the user explicitly asks to continue anyway.
   - Check whether the target path is inside a plain git repository (not a datalad dataset):
     run `git rev-parse --git-dir` from the target path. If a `.git/` is found but no
     `.datalad/`, warn:
     > "Target path is inside a plain git repository. Creating a DataLad dataset here
     > will nest it inside an untracked git repo, which can cause unexpected behavior.
     > Consider initializing at the git repo root, or outside the git tree. Proceed anyway?"
     Wait for user confirmation before continuing.

3. **Create the dataset** — run:
   ```
   datalad create -c yoda <path>
   ```
   Show the command before executing. Report the full output. Optionally suggest adding
   `--annex-backend SHA256E` (recommended; avoids the legacy MD5E backend which causes
   compatibility issues with some special remotes):
   ```
   datalad create -c yoda --annex-backend SHA256E <path>
   ```

4. **Report the YODA structure** — after creation, display what was created:
   ```
   <path>/
   ├── code/          ← version-controlled scripts and notebooks (annexed: never)
   ├── outputs/       ← results produced by datalad run (annexed: everything)
   ├── inputs/        ← input data, ideally linked as subdatasets (annexed: everything)
   └── README.md      ← dataset description
   ```
   Explain each directory's role briefly (see `${CLAUDE_PLUGIN_ROOT}/../references/yoda-layout.md`
   for full detail).

5. **Explain YODA principles** — briefly state the three principles:
   - **P1 — Everything is a dataset**: input data should be linked as subdatasets, not copied
   - **P2 — Record data origins**: use `datalad download-url` or `datalad clone` with provenance
   - **P3 — Never modify a dataset you didn't create**: work only in `outputs/` and `code/`

6. **Suggest next steps** — close with:
   - Put scripts and analysis code in `code/`
   - Link input data as a subdataset: `datalad clone <source> inputs/<name>`
   - Use `datalad run` to execute scripts so commands and outputs are recorded
   - Use `datalad save -m "..."` to record code changes

## Constraints

- Never run `datalad create` without explicit path confirmation from the user.
- Never re-initialize an existing DataLad dataset — always stop and explain.
- Always use `-c yoda` — never create a bare dataset without the YODA configuration.
- Always warn when the target path is inside a plain git repo, and require explicit
  confirmation before proceeding.
- Load `${CLAUDE_PLUGIN_ROOT}/../references/yoda-layout.md` if the user asks for more detail
  about YODA conventions, `.gitattributes` behavior, or subdataset patterns.
