# Nipoppy Curation Commands: `track-curation` and `reorg`

## `nipoppy track-curation`

Create or update the curation status file (`tabular/curation_status.tsv`), which
tracks raw data availability, reorg completion, and BIDS conversion status per
participant-session pair.

### Synopsis

```bash
nipoppy track-curation [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--empty` | off | Initialize an empty curation status file without scanning files. Useful to reset tracking. |
| `--regenerate` / `-f` | off | Force full regeneration of the status file, overwriting existing entries. |
| `--participant-id ID` | all | Limit update to a single participant. |
| `--session-id ID` | all | Limit update to a single session. |
| `--verbose` / `-v` | off | Increase log verbosity. |

### Curation status file schema (`curation_status.tsv`)

| Column | Values | Description |
|--------|--------|-------------|
| `participant_id` | string | Subject ID from manifest |
| `session` | string | Session label from manifest |
| `has_raw_data` | `True`/`False` | Raw DICOMs found in `pre_reorg/` |
| `has_reorg_data` | `True`/`False` | Reorg output present in `post_reorg/` |
| `has_bids_data` | `True`/`False` | BIDS output present in `bids/` |

### When to run `track-curation`

Run after each of these events to keep status current:
1. After `nipoppy init` (creates the initial empty file)
2. After dropping new DICOMs into `pre_reorg/`
3. After `nipoppy reorg` completes
4. After `nipoppy bidsify` completes

### Example invocations

```bash
# Update curation status for all participants
nipoppy track-curation --dataset /data/my-study

# Force regenerate from scratch
nipoppy track-curation --dataset /data/my-study --regenerate

# Update only one participant-session
nipoppy track-curation --dataset /data/my-study --participant-id sub-001 --session-id ses-01

# Initialize empty file without scanning
nipoppy track-curation --dataset /data/my-study --empty
```

---

## `nipoppy reorg`

Reorganize raw DICOM files from the unstructured `sourcedata/imaging/pre_reorg/`
directory into a participant-session layout in `sourcedata/imaging/post_reorg/`.

### Synopsis

```bash
nipoppy reorg [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--copy-files` | off | Copy files to `post_reorg/` instead of moving them. Preserves `pre_reorg/` originals. |
| `--check-dicoms` | off | Validate that files in `pre_reorg/` are valid DICOMs before reorg. Reports corrupt/invalid files. |
| `--participant-id ID` | all | Process only the specified participant. |
| `--session-id ID` | all | Process only the specified session. |
| `--simulate` | off | Print planned file operations without executing. |
| `--dry-run` / `-n` | off | Alias for `--simulate`. |
| `--verbose` / `-v` | off | Increase log verbosity. |
| `--layout PATH` | default | Custom heuristic script for mapping raw files to participant-session dirs. |

### pre_reorg → post_reorg layout

**Input (`pre_reorg/`):** Any structure — flat dump, scanner-native layout, or nested dirs.

**Output (`post_reorg/`):**
```
post_reorg/
└── <participant_id>/
    └── <session>/
        └── <DICOM files or series dirs>
```

### DICOM check warnings

When `--check-dicoms` is used, nipoppy validates each file with pydicom. Files that
fail validation are reported but not moved; the run continues for valid files.

### Custom layout heuristics

If the raw layout is non-standard, supply a `--layout` Python script that implements
a `get_participant_session(filepath)` function returning `(participant_id, session)`.
See nipoppy documentation for the heuristic API.

### Example invocations

```bash
# Dry-run to preview what would be reorganized
nipoppy reorg --dataset /data/my-study --simulate

# Reorg all, copying files (safe — keeps originals)
nipoppy reorg --dataset /data/my-study --copy-files

# Reorg with DICOM validation
nipoppy reorg --dataset /data/my-study --check-dicoms

# Reorg a single participant
nipoppy reorg --dataset /data/my-study --participant-id sub-001 --session-id ses-01
```

### After reorg

Run `nipoppy track-curation` to update `has_reorg_data` flags in the curation status file.
