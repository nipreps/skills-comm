# DataLad Subdataset Patterns Reference

## Superdataset / subdataset relationship

A **superdataset** is a DataLad dataset that contains one or more **subdatasets** — other
datasets nested inside it. The superdataset does not store the subdataset's content
directly. Instead, it stores only a **commit SHA pointer** (in `.gitmodules` and a git
submodule entry) that records which exact version of the subdataset is linked.

This means:
- The superdataset can always reproduce a fixed, reproducible state of every subdataset
- Subdatasets can be updated independently and the superdataset can pin to a specific version
- Subdatasets can be shared, published, and accessed independently

### `.gitmodules`

Git uses `.gitmodules` to track subdatasets. Each subdataset has an entry like:

```ini
[submodule "inputs/raw/sub-01"]
    path = inputs/raw/sub-01
    url = https://gin.g-node.org/user/sub-01
```

**Never edit `.gitmodules` directly.** Use `datalad clone -d .` to add and DataLad's
subdataset tools to manage. If you need to relocate a subdataset, use `git mv` (not `mv`).

---

## `datalad subdatasets` output fields

```
.: inputs/raw/sub-01 (subdataset) [https://gin.g-node.org/user/sub-01 (git)]
  state: present
  gitshasum: a1b2c3d4...
  gitmodule_url: https://gin.g-node.org/user/sub-01

.: inputs/raw/sub-02 (subdataset) [https://gin.g-node.org/user/sub-02 (git)]
  state: absent
  gitshasum: e5f6a7b8...
  gitmodule_url: https://gin.g-node.org/user/sub-02
```

| Field | Meaning |
|-------|---------|
| `path` | Relative path of the subdataset within the superdataset |
| `state: present` | Subdataset is cloned and accessible locally |
| `state: absent` | Subdataset is registered in `.gitmodules` but not yet cloned locally |
| `gitshasum` | The exact commit in the subdataset that the superdataset currently pins |
| `gitmodule_url` | Where to clone the subdataset from |

---

## Absent vs. present subdatasets

A subdataset registered in `.gitmodules` but not yet cloned shows as **absent**. Its
files are not accessible. To make it accessible:

```bash
# Install the subdataset handle (no file content — metadata and git history only)
datalad get -n inputs/raw/sub-01

# Install the subdataset handle AND retrieve all file content
datalad get inputs/raw/sub-01

# Install ALL absent subdatasets recursively and get all content
datalad get -r .
```

The `-n` flag ("no-data") clones the subdataset so you can inspect its structure and
file tree without downloading large annexed files. Useful when you only need to check
what files exist before deciding what to retrieve.

---

## Neuroimaging nested layout (YODA pattern)

```
project/                          ← superdataset
├── .datalad/
├── .gitmodules
├── code/                         ← analysis scripts (tracked in superdataset)
│   └── run_fmriprep.sh
├── inputs/
│   └── raw/
│       ├── sub-01/               ← each subject is an independent DataLad dataset
│       │   ├── .datalad/
│       │   ├── func/sub-01_task-rest_bold.nii.gz
│       │   └── anat/sub-01_T1w.nii.gz
│       ├── sub-02/               ← independent dataset
│       └── sub-NN/
└── derivatives/
    └── fmriprep/                 ← derivatives also a DataLad dataset
        ├── .datalad/
        ├── sub-01/               ← may contain per-subject subdatasets
        └── sub-02/
```

### Why per-subject datasets?

1. **Parallel processing**: each subject's dataset can be processed independently on
   different compute nodes without locking a single repository
2. **Modular sharing**: share only one subject's data without exposing the full cohort
3. **Independent versioning**: update or re-process individual subjects without creating
   a monolithic commit touching all subjects
4. **Selective retrieval**: `datalad get inputs/raw/sub-01` retrieves only what you need

---

## Recursive operations

Most DataLad commands accept recursion flags to operate across the whole tree:

| Flag | Behavior |
|------|----------|
| `-r` | Recurse through all subdatasets (unlimited depth) |
| `-R N` | Recurse but limit to N levels deep |

Examples:

```bash
# Get all content in the entire project tree
datalad get -r .

# Save changes in the superdataset and all subdatasets
datalad save -r -m "update all"

# Push superdataset and all subdatasets to origin
datalad push -r --to origin

# Update from sibling across the whole tree
datalad update -r -s origin --how=merge
```

---

## Recursive update with `--follow`

When running `datalad update -r`, the `--follow` flag controls what version each
subdataset is checked out at:

```bash
# Pin to the version recorded in the superdataset (reproducible; recommended)
datalad update -r -s origin --how=merge --follow=parentds

# Advance to sibling's HEAD (may diverge from superdataset pointer)
datalad update -r -s origin --how=merge --follow=sibling
```

Use `--follow=parentds` when you want reproducibility: the superdataset's `.gitmodules`
pointer is the authoritative version. Use `--follow=sibling` when you want to advance
all subdatasets to the latest available version and then update the superdataset pointer.

---

## `datalad clone -d .` to add a subdataset

To register an existing dataset as a subdataset of the current dataset:

```bash
# Register inputs/raw/sub-01 as a subdataset
datalad clone -d . https://gin.g-node.org/user/sub-01 inputs/raw/sub-01
```

After cloning, always record the new submodule pointer in the superdataset history:

```bash
datalad save -m "add sub-01 as subdataset"
```

Without this save, the superdataset history does not yet include the subdataset pointer.
