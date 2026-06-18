# YODA Layout Reference

## The Three YODA Principles

**P1 — Everything is a (sub)dataset**
Input data belongs in its own dataset, linked to the analysis dataset as a subdataset
(via `datalad clone` into `inputs/`). Never copy raw data into `inputs/` directly.
This makes the input re-usable and the link auditable.

**P2 — Record where data comes from**
Every file that enters the dataset should have its origin recorded. Use:
- `datalad download-url -m "describe source" <url> --path inputs/<file>` for web sources
- `datalad clone <source-dataset> inputs/<name>` for existing datasets
- `datalad run` for all commands that produce output (records the command itself)

**P3 — Never modify a dataset you didn't create**
Treat `inputs/` (and any subdataset) as read-only. All modifications happen in `outputs/`
or `code/`. If you need to pre-process input data, record that transformation via
`datalad run` producing files in `outputs/`.

---

## Directory Structure Created by `datalad create -c yoda`

```
<dataset>/
├── .datalad/              ← DataLad metadata (never edit manually)
│   └── config             ← dataset-level config (branch, description, etc.)
├── .gitattributes         ← controls what goes to git vs git-annex
├── .gitmodules            ← subdataset registrations (auto-managed)
├── code/                  ← scripts, notebooks, configs — git-tracked directly
├── outputs/               ← results from datalad run — annexed
├── inputs/                ← input data — annexed (or subdatasets)
└── README.md              ← dataset description
```

### `.gitattributes` behavior under `-c yoda`

| Path pattern | Storage |
|---|---|
| `code/**` | git (never annexed) |
| `README.md`, `*.md`, `*.txt` | git |
| Everything else | git-annex (content stored separately, pointer in git) |

This means: scripts in `code/` are fully version-controlled and always available.
Large data files (anywhere else) are stored in annex and can be retrieved on demand
with `datalad get`.

---

## `datalad create` Flag Reference

| Flag | Purpose |
|---|---|
| `-c yoda` | Apply YODA dataset procedure (directory layout + `.gitattributes`) |
| `-d <superdataset>` | Register new dataset as a subdataset of `<superdataset>` |
| `--description "..."` | Human-readable description stored in dataset config |
| `--no-annex` | Disable git-annex (pure git, no large-file support — rarely appropriate) |
| `--annex-version N` | Set git-annex repository version (usually leave at default) |
| `--force` | Create even if directory already exists and is non-empty (use cautiously) |

---

## Subdataset Pattern for Input Data (P1)

```bash
# Link an existing DataLad dataset as input
datalad clone https://example.com/source-dataset.git inputs/source-name

# After cloning, register it in the superdataset
datalad save -m "link source-name as input subdataset"
```

The subdataset appears in `.gitmodules` and is recorded by commit SHA, making the
exact version of the input reproducible.

To retrieve subdataset content after cloning the analysis dataset:
```bash
datalad get inputs/source-name
# or recursively:
datalad get -r inputs/
```

---

## Common Pitfall: Dataset Inside a Plain Git Repo

Creating a DataLad dataset inside a plain git repository (one with `.git/` but no
`.datalad/`) causes the DataLad dataset's `.git/` to be treated as a subdirectory of
the outer repo. This breaks `datalad` commands and confuses `git status` in the outer
repo.

**Fix**: either convert the outer repo to a DataLad dataset first (`datalad create .`
from the outer root), or move the DataLad dataset outside the git tree.

**Detection**: `git rev-parse --git-dir` from the target path — if it returns a path
and `.datalad/` does not exist at that level, you are inside a plain git repo.
