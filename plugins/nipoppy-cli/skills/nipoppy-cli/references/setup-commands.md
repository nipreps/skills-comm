# Nipoppy Setup Commands: `init` and `status`

## `nipoppy init`

Initialize a new nipoppy dataset directory with template configuration files and the
expected directory structure.

### Synopsis

```bash
nipoppy init [OPTIONS] <dataset-path>
```

### Arguments

| Argument | Description |
|----------|-------------|
| `<dataset-path>` | Path to the new dataset root directory. Created if it does not exist. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--bids-source PATH` | — | Seed the `bids/` directory from an existing BIDS dataset (copy/move/symlink). |
| `--mode {copy,move,symlink}` | `symlink` | How to import files when `--bids-source` is set. |
| `--force` / `-f` | off | Create the dataset even if files are already present (may overwrite existing files). |
| `--dataset PATH` | cwd | Path to the dataset root (default is current working directory). |
| `--layout FILE` | default | Path to a custom layout specification file. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print commands without executing. |

### Directory structure created

```
<dataset>/
├── config.json                 # Stub — must be edited before other commands
├── manifest.tsv                # Stub — must be populated with participant rows
├── sourcedata/
│   └── imaging/
│       ├── pre_reorg/          # Drop raw DICOMs here
│       └── post_reorg/         # Reorg output lands here
├── bids/                       # BIDS output target
├── derivatives/                # Pipeline output target
├── proc/logs/                  # Log files
├── scratch/                    # Temporary working dirs
└── tabular/                    # Status tracking TSV files
```

### Post-init checklist

After `init`, always:
1. Edit `config.json` — set `DATASET_NAME`, `VISITS`, `SESSIONS`, pipeline configs.
2. Populate `manifest.tsv` — add one row per expected participant-session pair.
3. Copy or move raw DICOMs into `sourcedata/imaging/pre_reorg/`.

### Example invocations

```bash
# Initialize a new empty dataset
nipoppy init /data/my-study

# Initialize seeding bids/ from an existing BIDS directory
nipoppy init /data/my-study --bids-source /data/existing-bids --mode symlink
```

---

## `nipoppy status`

Report the current workflow status across all participants and sessions. Reads the
curation status file (`curation_status.tsv`) and the processing bagel (`bagel.tsv`)
to produce a summary table.

### Synopsis

```bash
nipoppy status [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--verbose` / `-v` | off | Show per-participant detail instead of aggregate counts. |

### Output

Status prints a summary of:
- Number of participants with raw data present in `pre_reorg/`
- Number of participants with reorg complete
- Number of participants with BIDS conversion complete
- Per-pipeline: number of participants with pipeline run complete

### Example invocations

```bash
# Status for current directory dataset
nipoppy status

# Status for a specific dataset with verbose output
nipoppy status --dataset /data/my-study --verbose
```

### Notes

- `status` is read-only and safe to run at any time.
- An empty or missing `curation_status.tsv` reports zeros — run `track-curation` first.
- If `bagel.tsv` is missing, pipeline status is reported as unknown.
