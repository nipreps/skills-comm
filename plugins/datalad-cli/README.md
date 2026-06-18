# datalad-cli

Claude Code plugin that routes data processing and file changes through DataLad for
provenance tracking. Follows YODA principles for reproducible local analysis projects.

## Skills

| Skill | Slash command | Trigger |
|---|---|---|
| `datalad-init` | `/datalad-init` | Explicit: creating a new dataset or YODA layout |
| `datalad-run` | `/datalad-run` | Auto: executing scripts/pipelines that produce output files |
| `datalad-save` | `/datalad-save` | Auto: saving code changes inside a DataLad dataset |
| `datalad-container-run` | `/datalad-container-run` | Auto: running commands inside Singularity/Apptainer/Docker containers |
| `datalad-status` | `/datalad-status` | Auto: checking dataset state |
| `datalad-diff` | `/datalad-diff` | Auto: comparing dataset versions |
| `datalad-clone` | `/datalad-clone` | Auto: obtaining a copy of a dataset |
| `datalad-get` | `/datalad-get` | Auto: retrieving annexed file content |
| `datalad-push` | `/datalad-push` | Auto: pushing dataset to a sibling |
| `datalad-update` | `/datalad-update` | Auto: updating from a sibling |
| `datalad-siblings` | `/datalad-siblings` | Auto: configuring remote siblings |
| `datalad-subdatasets` | `/datalad-subdatasets` | Auto: managing nested subdatasets |
| `datalad-untrack` | `/datalad-untrack` | Auto: dropping content or removing files |
| `datalad-addurls` | `/datalad-addurls` | Auto: bulk-adding files from URLs |
| `datalad-configuration` | `/datalad-configuration` | Explicit: dataset configuration |
| `datalad-export` | `/datalad-export` | Explicit: exporting to archive or Figshare |
| `datalad-log` | `/datalad-log` | Auto: browsing run history and provenance |
| `datalad-credentials` | `/datalad-credentials` | Auto: setting up authentication credentials |

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/datalad-cli

# Permanent install
claude plugin install ./plugins/datalad-cli
```

## Quick workflow

```bash
# 1. Create a YODA dataset
/datalad-init my-analysis

# 2. Add code, link inputs as subdatasets
# (put scripts in code/, link data via datalad clone)

# 3. Run analysis with provenance
/datalad-run python code/analysis.py

# 4. Save code changes
/datalad-save "add preprocessing step to analysis script"
```

## YODA principles enforced

- **P1**: Input data linked as subdatasets (`inputs/`), not copied
- **P2**: Data origins recorded via `datalad download-url` or `datalad clone`
- **P3**: `inputs/` treated as read-only; all results go to `outputs/`

## Auto-checkpoint hook

The plugin installs a `Stop` hook that runs after every Claude turn. If the current
directory is inside a DataLad dataset and there are unsaved changes, it automatically
commits them:

```
[datalad] checkpoint 2026-03-12T14:05:22Z: code/analysis.py outputs/result.csv
```

**Opt out** for a session:
```bash
DATALAD_AUTOSAVE=0 claude --plugin-dir ./plugins/datalad-cli
```

The hook exits silently (no error, no commit) when:
- `datalad` is not on `$PATH`
- The cwd is not inside a DataLad dataset
- `DATALAD_AUTOSAVE=0` is set
- There are no modified or untracked files

**Checkpoint commits in run history**: checkpoint commits appear in `datalad log` and
`git log` alongside `datalad run` provenance records. They are identifiable by the
`[datalad] checkpoint` prefix in their message. To list only run records:
```bash
git log --oneline --grep="\[datalad run\]"
```

## Structure

```
datalad-cli/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── datalad-checkpoint.sh
├── references/                        ← shared across all skills
│   ├── yoda-layout.md
│   ├── subdataset-patterns.md
│   ├── siblings-and-remotes.md
│   ├── annex-content-states.md
│   └── troubleshooting.md
└── skills/
    ├── datalad-init/SKILL.md
    ├── datalad-run/
    │   ├── SKILL.md
    │   └── references/run-command.md
    ├── datalad-save/SKILL.md
    ├── datalad-container-run/
    │   ├── SKILL.md
    │   └── references/container-run.md
    ├── datalad-log/SKILL.md
    ├── datalad-credentials/SKILL.md
    └── [... 12 more skill directories]
```
